# Shadow rotation advisor (IMP-0019 phase 1) — design

Status: design for implementation, recorded as **DEC-0044**. Tracked
improvement: **IMP-0019**, from
[episodic-agent-rotation.md](../../../projects/personal-agent-os/roadmap/episodic-agent-rotation.md)
("start in report/shadow mode"). Measurement base: the IMP-0018 context-economy
harness, [context-economy.md](context-economy.md),
`src/agent_os/orchestrator/context_economy.py`, with baseline EVR-0018.

The advisor answers one question for every worker in past runs: **at which
call boundary, if any, would ending the episode and starting a fresh worker
have cost less input than continuing?** A fresh worker is bootstrapped from a
checkpoint, a structured handoff and targeted retrieval. Because every
Orchestrator call is already a fresh CLI process, "continuing" means keeping
the existing re-attempt behavior (original prompt plus a failure note); §3.1
states this precisely. The advisor is
deterministic and offline. It makes no model calls and no network calls, and
it spends nothing. It **records advice only**. No dispatch, scheduling or
routing code imports it, and it never changes what Orchestrator runs.

## 0. Prior art

`agent-os orchestrate prior-art lookup "episodic agent rotation / context-pressure shadow advisor / continue-vs-restart cost model"`
(offline registry) returned 8 matches. None is a continue-vs-restart cost
model:

| Id | Decision | What it gives here |
|---|---|---|
| PA-openhands | BORROW (low) | Conversation condensers and stuck detection for long sessions. The idea behind `compact`. Its condenser runs inside its own runtime, so phase 1 cannot use it on CLI workers (§4). |
| PA-routellm | BORROW (medium) | Choosing the threshold against a cost-vs-quality curve on a development set. Borrowed as the offline `margin_sensitivity` curve (§6). |
| PA-llmlingua | DEFER | Token-level prompt compression needs a local model (torch). Not used. |
| PA-optuna | DEFER | Tuning against a cheap deterministic objective. The constants in §3 are candidates for it later, not in phase 1. |
| PA-litellm | BORROW (ideas only) | Retry and fallback semantics. These are already reflected in the `retry` and `fallback` telemetry this advisor counts. |
| PA-ragas | BORROW (later) | Context precision and recall would sharpen `estimated_relevant_tokens` once retrieval evaluation exists. |
| PA-aflow | DEFER | MCTS over workflows. Far beyond budget. |
| PA-openrouter-api | INVESTIGATE | Matched on the words "context" and "model" only. Not relevant. |

The registry has nothing to reuse for this problem. The cost model is custom,
small and deterministic. It reuses the context-economy parser and privacy check
instead of adding a second telemetry stack, as IMP-0019 requires.

## 1. Inputs

The advisor uses only data that the existing harness already reads.

### 1.1 Calls: `context_economy._read_run`

For each run directory, `_read_run(run_dir, labels, cov, forbidden)` provides
`run["eligible"]` and `run["nodes"]` (from `_node_series`). Each eligible call
supplies exactly these fields:

| Field | Symbol | Meaning |
|---|---|---|
| `input` | `I(c)` | provider input tokens (exact usage, already includes cache reads and writes) |
| `output` | `O(c)` | provider output tokens |
| `cache_read` | `CR(c)` | cache-read tokens |
| `prompt` | `P(c)` | Orchestrator prompt estimate (characters/4), or `None` |
| `attempt` | `a(c)` | node attempt, or `None` (sorts as 0) |
| `seq` | `s(c)` | telemetry sequence |
| `role` | `role(c)` | sanitized role label |
| `node` | — | node id, in memory only |

Eligibility, the exclusion categories and label sanitizing are exactly those of
context-economy §2. `run["calls"]` (every call, including ineligible ones) is
used only to find workers that have ineligible calls (§2).

### 1.2 Per-node counters: `ledger.read_events`

`_read_run` counts `retry`, `model_escalated` and `fallback` per run, not per
node. The advisor therefore reads the same `telemetry.jsonl` once more with
`ledger.read_events` and keeps `(type, node, seq, subject, verdict,
material_findings)` for these event types only:

| Event | Keyed by | Counter |
|---|---|---|
| `retry` | event `node` | `retries` |
| `model_escalated` | event `node` | `escalations` |
| `fallback` | event `node` | `fallbacks` |
| `review_started` | `data.subject` (the event `node` is the reviewer) | `review_started` |
| `review_completed` | `data.subject` | `review_completed` |
| `review_completed` with integer `data.material_findings > 0` or `data.verdict == "blocked"` | `data.subject` | `review_required` |

`review_required` is **not** a ledger event type (`ledger.EVENT_TYPES` does
not contain it). It is derived from `review_completed` with the same rule the
engine uses to send a subject to repair (`material(...)` findings or a
`blocked` verdict). A repair node is a separate node with id
`<subject>.repair<N>`. It also takes the review counters of `<subject>`,
because the findings it must act on came from those rounds. This id parsing
happens in memory only.

Coverage counters (`events`, `malformed_lines`, ...) come from `_read_run`
alone. The second read never adds to them, so nothing is counted twice. No
`data` string other than `verdict` is read, and `verdict` is compared, never
copied.

### 1.3 Worker-file sizes: `os.stat` only

For the handoff calibration (§6) the advisor calls
`os.stat(runs/<run>/workers/<node>-<attempt>/last-message.md).st_size`. It never
opens a worker file, in line with context-economy §1.2. `_read_workers` drops
the `(node, attempt)` key for privacy, so the advisor stats the one path
itself. A missing file is counted, never guessed.

## 2. Workers and boundaries

A **worker** is one node's eligible call series `c_0 .. c_{n-1}`, ordered by
`(a(c) or 0, s(c))` exactly as in `_node_series`. In Orchestrator, reviews and
repairs are separate nodes (`<s>.review<N>`, `<s>.repair<N>`), so a series
holds the attempts of one assignment: the first try plus retries and
escalations.

- A **candidate boundary** is `k = 1 .. n-1`. It lies between `c_{k-1}` and
  `c_k`. Rotating at `k` means calls `c_k .. c_{n-1}` run as fresh episodes.
  A worker with `n == 1` has no boundaries. It is counted in
  `coverage.single_call_workers`.
- A boundary is **semantic** when `a(c_k) != a(c_{k-1})`, that is, a retry or
  repair attempt starts there. Only semantic boundaries may receive `rotate`
  (§4). A boundary inside one attempt, such as a provider fallback within the
  attempt, is still scored so that the savings curve stays complete, but its
  recommendation is always `continue`.
- A worker whose node also has ineligible calls (estimated, unavailable or
  inconsistent usage) is **not scored**, because its `C_continue` would be
  understated. It is counted in `coverage.unscored_workers.ineligible_calls`.

Within-node rotation is the only kind phase 1 assesses. Across nodes, from
implementer to reviewer to repairer, Orchestrator already starts fresh workers.
Measuring those handoffs is out of scope here.

## 3. Cost model

Named constants live at module top. Each one is reported in the
`constants` block:

| Constant | Type | Value | Rationale |
|---|---|---|---|
| `HANDOFF_FACTOR` | float | `0.5` | A structured handoff keeps decisions, state, evidence and pointers, not the whole output. EVR-0013 measured about 68% fewer tokens with focused attachments (a factor of about 0.32). 0.5 is deliberately conservative. |
| `HANDOFF_CAP` | int | `8000` | Upper bound on handoff tokens per fresh episode. It is about one harness overhead (the context-anatomy default is 6000 to 9000). |
| `REDISCOVERY_RATE` | float | `0.25` | The share of one bootstrap that a fresh worker spends rediscovering state, per retry, review round or repair-required round already seen. |
| `MARGIN` | float | `0.2` | Rotation must save more than 20% of `C_continue` (§4). |
| `ROLE_FALLBACK_WEIGHT` | float | `0.5` | Confidence multiplier when the bootstrap comes from all runs rather than this run (§5). |

All token quantities are integers. A median or a product is rounded up with
`math.ceil`, so rounding never favors rotation.

### 3.1 Continue

```text
C_continue(k) = sum_{j=k}^{n-1} I(c_j)              actual input of the remaining calls (hindsight)
```

**What "continue" means here.** Orchestrator runs every call as its own CLI
process, so the calls after a semantic boundary are already fresh processes:
Orchestrator's existing re-attempt restarts the worker with the original
assignment prompt plus a failure note. `C_continue(k)` is therefore the
observed cost of that existing re-attempt path, not of a long-lived session.
`savings(k)` (§3.6) estimates whether a different restart, built from a capped
structured handoff `H(k)` plus targeted retrieval `R`, would have cost less
input than the re-attempt that actually ran. "Rotate" in this document means
"restart with a structured handoff instead of the original prompt", and
"continue" means "keep Orchestrator's current re-attempt behavior".

### 3.2 Bootstrap

```text
first(role, scope) = [ I(series[0]) for every worker in scope whose first call has that role ]
B(role) = ceil(median(first(role, this run)))      if that list is non-empty     (bootstrap_source = run_role)
        = ceil(median(first(role, all runs)))      otherwise, if non-empty       (bootstrap_source = all_runs_role)
        = undefined                                otherwise -> boundary unscored (no_bootstrap)
```

The first call of a series is the measured cost of a fresh worker for that
role. It includes the agent's own tool turns and that call's prompt, so adding
retrieval on top double-counts one prompt. That bias is deliberate: it makes
the shadow advisor err toward `continue`.

### 3.3 Handoff

```text
H(k) = min(HANDOFF_CAP, ceil(HANDOFF_FACTOR * sum_{i=0}^{k-1} O(c_i)))
```

`H(k)` is the same for every remaining call. It summarizes the work done
before the boundary.

### 3.4 Retrieval

```text
R(c_j) = P(c_j)                                        when P(c_j) > 0
       = ceil(median P over eligible calls of role(c_j), all runs)   otherwise (counted: retrieval_fallback_calls)
       = undefined -> boundary unscored (no_retrieval_estimate)
```

The call's own Orchestrator prompt estimates the targeted context that a fresh
episode needs for that step.

### 3.5 Rediscovery

The counters use only events with `seq < s(c_k)`, so the advisor never sees
the future of the state it would hand off:

```text
retries_k        = retry events on the node
review_rounds_k  = max(review_started, review_completed) on the node's subject key(s)
review_required_k= review_required on the node's subject key(s)
rework_k         = retries_k + review_rounds_k + review_required_k
D(k)             = ceil(REDISCOVERY_RATE * B(role(c_k)) * rework_k)
```

A round that required repair is counted twice, as a round and as
repair-required, because open findings are the state a fresh worker most
often has to rediscover. `D(k)` is charged once per rotation, not once per
remaining call.

### 3.6 Rotate

```text
F(k)          = sum_{j=k}^{n-1} ( B(role(c_j)) + H(k) + R(c_j) )      estimated fresh-worker input
C_rotate(k)   = F(k) + D(k)
savings(k)    = C_continue(k) - C_rotate(k)                            may be negative
```

The model does not try to predict output tokens, retries, review results or
latency. The roadmap's full `C_rotate` lists them, but historical telemetry has
no counterfactual for any of them. Section 6 says how calibration uses the
observed equivalents instead.

## 4. Decision rule

```text
recommend(k) = "rotate"    if semantic(k) and savings(k) > MARGIN * C_continue(k)
             = "continue"  otherwise
```

The comparison is strict. Savings exactly at the margin give `continue`.
Unscored boundaries get no recommendation. They are counted in
`coverage.unscored_boundaries.<reason>`.

**Worker advice.** A worker gets `rotate` when any of its boundaries does. Its
chosen boundary `k*` is the `rotate` boundary with the largest `savings`, with
ties going to the smallest `k`. Otherwise the worker gets `continue`.
Savings at different `k` overlap, so totals add only `savings(k*)` per rotate
worker and never add across the boundaries of one worker.

**`compact` and `split_parallel`: phase 1 never emits them.** The
`recommendation` enum keeps all four values from the roadmap so the schema
stays stable. Their counts are always `0`, and a test pins that.

- `compact` means replacing context inside a live session. Orchestrator runs
  each call as a separate CLI process. Nothing outside that process can compact
  it, and no telemetry measures compaction. OpenHands-style condensers
  (PA-openhands) belong to a later phase that has a runtime hook.
- `split_parallel` needs artifact and dependency separability. Call telemetry
  does not record either.

## 5. Explanation fields

Every scored boundary produces one explanation object with a **closed set** of
fields. They mirror the roadmap's `context_pressure` block. Every value is an
integer, a float rounded to 4 decimals, or `null`. The only string is
`recommendation`.

| Field | Definition |
|---|---|
| `current_context_tokens` | `I(c_{k-1})` |
| `estimated_relevant_tokens` | `H(k) + R(c_k)` |
| `relevance_ratio` | `estimated_relevant_tokens / current_context_tokens` (`null` when the denominator is 0) |
| `repeated_or_stale_tokens` | `CR(c_{k-1})`: context the last call re-read from cache |
| `context_window_utilization` | always `null` in phase 1, because telemetry has no window size |
| `expected_remaining_calls` | `n - k` (hindsight count) |
| `projected_continue_input` | `C_continue(k)` |
| `estimated_fresh_worker_input` | `F(k)` |
| `bootstrap_overhead` | `sum_j B(role(c_j))` |
| `handoff_overhead` | `H(k) * (n - k)` |
| `retrieval_tokens` | `sum_j R(c_j)` |
| `estimated_rediscovery_penalty` | `D(k)` |
| `projected_savings` | `savings(k)` |
| `confidence` | `(remaining calls with their own P > 0) / (n - k)`, times `1.0` for `run_role` bootstrap or `ROLE_FALLBACK_WEIGHT` for `all_runs_role` |
| `semantic` | `1` or `0` |
| `retries`, `escalations`, `fallbacks`, `review_rounds`, `review_required` | the §3.5 counters before the boundary (`escalations` and `fallbacks` are explanation only) |
| `recommendation` | `continue` or `rotate` (`compact`, `split_parallel` reserved) |

Explanations are returned in memory by the pure function that scores one
worker. Tests and a later `episode.rotation.explain` use them. They are
**never written per boundary**. The report aggregates them (§6).

## 6. Report `personal-agent/orchestrator-rotation-advice/v1`

Aggregates only. The keys are serialized with `sort_keys=True`, and runs are
sorted. `generated_at` is the only nondeterministic field, as in
context-economy.

```json
{
  "schema": "personal-agent/orchestrator-rotation-advice/v1",
  "mode": "shadow",
  "dispatch_changes": 0,
  "generated_at": "iso-8601",
  "estimate_method": "characters/4",
  "constants": {"HANDOFF_FACTOR": 0.5, "HANDOFF_CAP": 8000, "REDISCOVERY_RATE": 0.25,
                "MARGIN": 0.2, "ROLE_FALLBACK_WEIGHT": 0.5},
  "runs": ["run-20261001T195202Z-16098f"],
  "coverage": {
    "runs": 0, "malformed_runs": 0, "events": 0, "malformed_lines": 0, "eligible_calls": 0,
    "workers": 0, "single_call_workers": 0, "scored_workers": 0,
    "unscored_workers": {"ineligible_calls": 0},
    "boundaries": 0, "semantic_boundaries": 0, "scored_boundaries": 0,
    "unscored_boundaries": {"no_bootstrap": 0, "no_retrieval_estimate": 0},
    "bootstrap_source": {"run_role": 0, "all_runs_role": 0},
    "retrieval_fallback_calls": 0, "handoff_size_missing": 0, "sanitized_labels": 0
  },
  "advice": {
    "boundaries": {"continue": 0, "compact": 0, "rotate": 0, "split_parallel": 0},
    "workers": {"continue": 0, "compact": 0, "rotate": 0, "split_parallel": 0},
    "by_role": {"implementer": {"workers": 0, "boundaries": 0, "rotate_workers": 0, "projected_savings": 0}}
  },
  "savings": {
    "scored_worker_input": 0,
    "chosen_continue_input": 0, "chosen_rotate_input": 0, "projected_savings": 0,
    "savings_share": null,
    "per_rotate_worker": "stats"
  },
  "explanation": {
    "all": {"<numeric field>": "stats"},
    "by_recommendation": {"continue": {"<numeric field>": "stats"}, "rotate": {"<numeric field>": "stats"}}
  },
  "margin_sensitivity": {"0.0": {"rotate_workers": 0, "projected_savings": 0},
                         "0.1": "same", "0.2": "same", "0.3": "same", "0.5": "same"},
  "calibration": {"fresh_call_ratio": "stats", "handoff_ratio": "stats"},
  "by_run": {"run-...": {"workers": 0, "scored_boundaries": 0, "rotate_workers": 0, "projected_savings": 0}},
  "privacy": {"rule": "max80-no-whitespace", "strings_checked": 0, "passed": true}
}
```

`"stats"` is the context-economy statistics block (`_stats`: count, median,
nearest-rank p90, min, max). Ratios use `_ratio`, which gives `null` for a zero
denominator.

- `scored_worker_input` is the sum of `I` over every call of the scored
  workers. `savings_share = projected_savings / scored_worker_input`.
- `explanation` has one `stats` per numeric field from §5 over scored
  boundaries. `context_window_utilization` always has count 0.
- `margin_sensitivity` reruns only the §4 rule with `MARGIN` set to each listed
  value, so the threshold can be read off a curve (the PA-routellm idea; it
  also feeds the roadmap's EXP-B). The keys are fixed strings.
- `calibration.fresh_call_ratio` is `stats((B(role(c_k)) + H(k) + R(c_k)) / I(c_k))`
  over scored semantic boundaries with `I(c_k) > 0`. A new attempt is already
  a new CLI process, so `I(c_k)` is an **observed** fresh-process cost. A
  median far from 1 means the model is mis-scaled.
- `calibration.handoff_ratio` is `stats(observed / H(k))`, where `observed =
  ceil(sum st_size(last-message.md for the attempts of c_0..c_{k-1}) /
  CHARS_PER_TOKEN)`. It is defined when `H(k) > 0` and at least one file
  exists. Otherwise `handoff_size_missing` is incremented.

**Privacy** follows context-economy §4 without changes. The allowed strings
are fixed keys, the four recommendation labels, run ids matching `RUN_ID`,
sanitized role labels, the margin keys and the constants' names. **Node ids,
worker directory names, subjects, verdicts, goals and paths are never
emitted.** Per-node state exists only in memory. Before returning,
`build` calls `assert_aggregate_only(report, forbidden - labels.seen)`, where
`forbidden` is the set that `_read_run` collected (node ids and worker
directory names). It fills `privacy.strings_checked` and `passed` only after
the check succeeds. `report()` calls `assert_aggregate_only` again before
writing `--out`.

## 7. Implementation shape

- Module: `src/agent_os/orchestrator/rotation_advisor.py`.
  - `score_worker(series, counters, bootstrap, retrieval_median) -> list[dict]`
    is pure. It returns the per-boundary explanations from §5.
  - `build(run_dirs) -> dict` and `report(home=None, out=None) -> dict` mirror
    `context_economy.build` and `context_economy.report`.
  - It reuses `context_economy._read_run`, `_Labels`, `_stats`, `_ratio`,
    `RUN_ID`, `PRIVACY_RULE` and `assert_aggregate_only`, plus
    `ledger.read_events` and `usage.CHARS_PER_TOKEN` / `ESTIMATE_METHOD`. It
    adds no second call parser or token estimator.
- CLI: `agent-os orchestrate rotation-advisor [--home PATH] [--out PATH]`. It
  prints the report.
- **Shadow guarantee.** Only `cli.py` imports `rotation_advisor`. `engine.py`,
  routing, scheduling and `context_economy.py` do not, and a test asserts this.
  The advisor writes nothing under `runs/`.
- Protected control-plane paths are not touched.

## 8. Tests (synthetic fixtures, no network)

Each test file starts with
`sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))`.
Fixtures write ledger-schema `telemetry.jsonl` lines and fixed-size worker
files into a temporary `runs/` directory. Required cases:

1. **Formulas.** A worker with 3 calls (attempts 1, 2, 3), plus a `retry`
   event and a reviewer's `review_started` and `review_completed`
   (`material_findings: 1`, keyed by `data.subject`). `C_continue`, `B`,
   `H` (including the `HANDOFF_CAP` clamp), `R`, `D`, `F`, `savings`, every §5
   field and `confidence` are checked against hand-computed integers.
2. **Bootstrap fallback.** A role with no first call in its own run uses the
   all-runs median, and `confidence` is multiplied by `ROLE_FALLBACK_WEIGHT`.
   A role absent everywhere gives `no_bootstrap`. A missing `P` uses the role
   median and increments `retrieval_fallback_calls`.
3. **Boundaries.** A single-call worker has no boundary. A same-attempt
   boundary with large savings still gives `continue` (`semantic = 0`). A
   worker with an ineligible call is unscored.
4. **Decision edge.** `savings == MARGIN * C_continue` gives `continue`, and
   one token more gives `rotate`. `k*` is the boundary with maximum savings,
   with ties going to the smallest `k`.
5. **Never emitted.** `compact` and `split_parallel` counts are 0 for every
   fixture.
6. **Causality.** Adding `retry` or `review_*` events after `s(c_k)` leaves
   `D(k)` unchanged. A `<s>.repair1` node inherits the review counters of `<s>`.
7. **Privacy and sizes only.** Node ids, subjects and a sentinel phrase in the
   worker files are absent from the JSON. Patching `open` and
   `Path.read_text` for the workers tree proves that worker files are never
   opened. `assert_aggregate_only` passes. Two builds are identical except for
   `generated_at`.
8. **Shadow.** `mode == "shadow"` and `dispatch_changes == 0`, and no module
   except `cli.py` imports `rotation_advisor`.

## 9. Offline evaluation and evidence

The worker builds the command and its tests. The **host** runs it over the
real local telemetry, because workers cannot read the orchestrator home:

```text
python agent.py orchestrate rotation-advisor --out docs/orchestrator-os/self-audit/rotation-advisor-baseline.json
```

Results are recorded with the existing formats under
`projects/personal-agent-os/orchestrator-os/records/`, using the next free ids:

- **EXP** (`experiments/`). Hypothesis: within-node rotation at semantic
  boundaries would have cost less input than continuing for a material share
  of multi-call workers. Method: this advisor over all local runs, in shadow
  mode. Falsifiers: `savings_share < 0.05` at `MARGIN = 0.2`, or a
  `calibration.fresh_call_ratio` median outside `[0.5, 2.0]`. A miscalibrated
  model makes the savings figure untrustworthy.
- **EVR** (`evaluations/`, schema `personal-agent/evidence-record/v1`,
  `task_family: "rotation_advice"`). `metrics` copies report aggregates only:
  coverage, advice counts, `projected_savings`, `savings_share`, the
  `margin_sensitivity` curve and the calibration medians, plus
  `model_calls: 0`, `spend_usd: 0` and `dispatch_changes: 0`. `links`:
  `measures` → `src/agent_os/orchestrator/rotation_advisor.py`, `relates_to` →
  `IMP-0019`, `relates_to` → `EVR-0018`, `relates_to` → `DEC-0044`.

Shadow advice is a prediction, not evidence that rotation works. Live rotation
still needs the roadmap's promotion criteria: a controlled comparison (EXP-A)
with noninferior validation and lower total cost per validated completion.
