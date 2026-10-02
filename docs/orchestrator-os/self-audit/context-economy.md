# Context-economy harness (IMP-0018 Phase 0) — design

Status: design for implementation. Tracked improvement: **IMP-0018**, Phase 0
("measurement first") of
[context-efficiency-token-amplification.md](../../../projects/personal-agent-os/roadmap/context-efficiency-token-amplification.md).
Prior evidence: EVR-0013 / DEC-0018 (focused attachments, about 68% fewer tokens).
Companion audits: [context-anatomy.md](context-anatomy.md) measures *prompt
sections* written by Orchestrator, and [usage.md](usage.md) measures provider
totals. This harness measures how provider-side input **behaves across calls**:
amplification, growth, fan-out and resume. It does not replace either audit.

The harness is deterministic and offline. It makes no model calls and no network
calls, and it spends nothing. It reads runtime state under
`<home>/runs/` (normally `.agent-local/orchestrator/runs`). Its output contains
aggregate numbers and a closed set of labels. It never contains prompt or
transcript text.

## 1. Inputs

### 1.1 Telemetry events

For each run directory `runs/<run_id>/`, read events with
`agent_os.orchestrator.ledger.read_events(runs/<run_id>/telemetry.jsonl)`.
That function returns events sorted by `seq` and counts malformed lines. Only
these event types are used:

| Event | Fields used | Purpose |
|---|---|---|
| `model_completed`, `model_failed` | `node`, `seq`, `data.role`, `data.capability_class`, `data.provider`, `data.model`, `data.attempt`, `data.duration_ms`, `data.prompt_chars`, `data.prompt_tokens_estimate`, `data.usage.{accuracy, source, input_tokens, uncached_input_tokens, cache_read_tokens, cache_write_tokens, output_tokens, cost_usd}` | one model call |
| `run_started` | presence and `seq` only (`data.mode` is prose and is never copied) | run segmentation, `has_run_started` flag |
| `run_paused` | `seq` | pause count |
| `run_resumed` | `seq` | resume windows (metric 4) |
| `checkpoint_created` | `node`, `seq` | warm-node detection (metric 4) |
| `retry`, `model_escalated`, `fallback` | `node`, `seq` | per-run repeat-work counters (metric 3) |

All other event types are ignored. Event `data` strings (`reason`, `evidence`,
`summary`, `what`, goals) are never read into the report.

### 1.2 Worker directories (sizes only)

For `runs/<run_id>/workers/<node>-<attempt>/`, the harness calls only
`os.stat(path).st_size` on regular files directly inside the directory. It never
opens a file. The directory name is split on its **last** `-`. The suffix must
parse as an integer attempt. Otherwise the directory is counted as
`unparsed_worker_dirs` and skipped. The `(node, attempt)` pair is joined to the
model call with the same node and `data.attempt` to get its role. File names are
mapped to fixed keys: `prompt.md` to `prompt`, `stdout.log` to `stdout`,
`stderr.log` to `stderr`, `last-message.md` to `last_message`, and any other
name to `other`. Node ids, directory names and file paths stay in memory only.

## 2. Call model and eligibility

Let `calls(r)` be the `model_completed` and `model_failed` events of run `r` in
`seq` order. For a call `c` with data `d` and usage `u = d.usage`:

```text
I(c) = u.input_tokens                                   provider input
       (fallback when input_tokens is null:
        u.uncached_input_tokens + u.cache_read_tokens + u.cache_write_tokens)
CR(c) = u.cache_read_tokens or 0
CW(c) = u.cache_write_tokens or 0
O(c) = u.output_tokens or 0
P(c) = d.prompt_tokens_estimate                         ceil(prompt_chars / 4), estimate
```

**Provider input is input + cache_read + cache_write.** Every adapter writes
`input_tokens` already normalized to this total (`usage.normalized`: Claude-style
`uncached + read + write`, and Codex/OpenAI-style `prompt_tokens`, which includes
cached tokens). The harness therefore uses `input_tokens` as it is. It must
**not** add `cache_read_tokens` and `cache_write_tokens` a second time.

A call is **eligible** when all of the following hold:

```text
eligible(c) = u.accuracy == "exact"
          and u.source != "synthetic"
          and I(c) is an integer >= 0
          and CR(c) + CW(c) <= I(c)                       (consistency guard)
```

Ineligible calls are counted, not measured. The report gives
`coverage.excluded.{estimated, unavailable, synthetic, inconsistent}`. Ratios
that need `P(c)` also need `P(c) > 0`. Calls without it are counted in
`coverage.calls_without_prompt_estimate`. Missing `role` or `capability_class`
becomes `"unknown"`.

### Statistics block

Every distribution is reported as a `stats` object. It is computed over the
values that are defined:

```text
count   = n
median  = statistics.median(values)                      (mean of the two middles when n is even)
p90     = sorted(values)[ceil(0.9 * n) - 1]              (nearest rank)
min, max
```

When `n == 0`, every field except `count` is `null`. Ratios are rounded to 4
decimals, and token sums are integers. A ratio with a zero denominator is
`null`, never `0` or `inf`.

## 3. Metrics

### Metric 1 — per-worker amplification

For each eligible call:

```text
A(c) = I(c) / P(c)          input amplification   (defined when P(c) > 0)
R(c) = O(c) / I(c)          output ratio          (defined when I(c) > 0)
H(c) = CR(c) / I(c)         cache-read share      (defined when I(c) > 0)
```

Calls are grouped separately by `role` and by `capability_class`, plus an
`all` group. For each group `G`:

```text
count                    = |{c in G : eligible(c)}|
sum_input                = sum I(c)
sum_prompt_estimate      = sum P(c)          over calls where A(c) is defined
sum_output               = sum O(c)
pooled_amplification     = sum_{A defined} I(c) / sum_{A defined} P(c)
pooled_output_ratio      = sum O(c) / sum I(c)
amplification            = stats(A(c))
output_ratio             = stats(R(c))
cache_read_share         = stats(H(c))
```

`A(c) - 1` is the share of provider input that Orchestrator did not write. That
covers the agent CLI system prompt, tool definitions, files the agent read, and
its own turns. Because `P(c)` is an estimate (characters/4), `A` is labelled an
estimate.

### Metric 2 — long-session context growth

**Per node.** For each node `n` that has at least one eligible call, let
`c_1 .. c_m` be its eligible calls ordered by `(d.attempt, seq)`. Attempts
missing `d.attempt` sort by `seq` alone. `k` is the ordinal, not the raw attempt
number.

```text
m_n          = number of eligible calls on n
first_n      = I(c_1)
last_n       = I(c_m)
growth_n     = last_n / first_n            (defined when m_n >= 2 and first_n > 0)
bucket(n)    = "1" if m_n == 1, "2-3" if 2 <= m_n <= 3, "4+" if m_n >= 4
```

For each bucket `b`:

```text
nodes            = |{n : bucket(n) = b}|
calls            = sum m_n
sum_input        = sum over nodes in b of sum_k I(c_k)
first_input      = stats(first_n)
last_input       = stats(last_n)
growth_ratio     = stats(growth_n)         (null stats for bucket "1")
```

**Per run.** Let `e_1 .. e_N` be the eligible calls of run `r` in `seq` order:

```text
C_r(j)               = sum_{i <= j} I(e_i)                     cumulative input by call index, j = 1..N
cumulative_input     = [C_r(1), ..., C_r(N)]
growth_exponent      = least-squares slope b of ln C_r(j) = a + b ln j
                       over j with C_r(j) > 0               (defined when at least 3 such points)
input_by_node_bucket = { b : sum I(e_i) over e_i whose node is in bucket b }
```

A `growth_exponent` near 1 means each call costs about the same, so growth is
linear. Values that approach 2 mean per-call input rises with call index, so
cumulative work grows quadratically. Calls with a null `node` add to `C_r` but
belong to no node bucket. They are counted as `input_by_node_bucket.none`.

### Metric 3 — worker fan-out cost

The planner role is `planner`. Every other role is a worker role (`implementer`,
`test_author`, `reviewer`, `repairer`, ...). For run `r`:

```text
worker_nodes[role]          = |{distinct node : node has any model call with that role}|   (all calls, any accuracy)
worker_nodes_total          = sum over worker roles of worker_nodes[role]
planner_input               = sum I(c) over eligible calls with role == planner
worker_input                = sum I(c) over eligible calls with role != planner
fanout_input_ratio          = worker_input / planner_input
duplicated_fixed_overhead   = sum over worker nodes w of sum over eligible calls c of w with P(c) defined of (I(c) - P(c))
overhead_share              = duplicated_fixed_overhead / worker_input
overhead_per_worker_call    = stats(I(c) - P(c))       over the same calls
negative_overhead_calls     = |{c : I(c) - P(c) < 0}|  (kept in the sum, not clamped)
repeat_attempt_input        = sum I(c_k) over node ordinals k >= 2       (from metric 2)
retries, escalations, fallbacks = counts of retry, model_escalated, fallback events
```

`duplicated_fixed_overhead` estimates the context that each worker pays again
regardless of its assignment: the harness prompt, tool schemas and repository
rediscovery. It is an estimate because `P` is one. A totals block sums
`planner_input`, `worker_input`, `duplicated_fixed_overhead`,
`repeat_attempt_input` and the counters across runs. It recomputes the two
ratios from those sums and never averages per-run ratios.

### Metric 4 — checkpoint-resume overhead

Only runs with at least one `run_resumed` event are included. Let
`s_1 < ... < s_k` be the `seq` values of those events and `s_{k+1} = +inf`.
Resume window `i` holds the calls with `s_i < seq < s_{i+1}`.

```text
warm_i(n)   = exists checkpoint_created on n with seq < s_i
              or exists model call on n with seq < s_i
              or the call's d.attempt > 1
resume_input_i        = sum I(c) over eligible c in window i whose node is warm_i
resume_first_input_i  = same sum restricted to the first eligible call per warm node in window i
resume_overhead_input = sum_i resume_input_i
resume_first_input    = sum_i resume_first_input_i
run_input             = sum I(c) over all eligible calls of the run
resume_share          = resume_overhead_input / run_input
resume_first_share    = resume_first_input / run_input
```

Per run, the report also gives `resumes = k`, `pauses` (`run_paused` count),
`checkpoints` (`checkpoint_created` count), `warm_nodes` (distinct warm nodes
summed over windows) and `cold_resume_input` (eligible window calls on nodes
that are not warm). `resume_first_input` is the cleanest re-entry cost: what a
warm node pays to rebuild context before doing new work. It is the baseline that
the roadmap's test F, "checkpoint vs conversation replay", must beat. A totals
block sums across resumed runs and recomputes the shares from those sums.

### Worker file sizes (supporting, metric 1)

For each role and each fixed file key, the report gives `stats(st_size)` and
`sum_bytes`. It also gives `prompt_bytes_per_estimated_token = stats(prompt
bytes / P(c))` as a size-only cross-check of the characters/4 estimate. UTF-8
bytes are at least the character count, so values near 4 confirm the estimate
basis.

## 4. Output schema `personal-agent/orchestrator-context-economy/v1`

All keys are serialized with `json.dumps(..., sort_keys=True)`. Runs are listed
in sorted order. There is no wall-clock timestamp, so the same input always
produces byte-identical output.

```json
{
  "schema": "personal-agent/orchestrator-context-economy/v1",
  "estimate_method": "characters/4",
  "runs": ["run-20261001T195202Z-16098f"],
  "coverage": {
    "runs": 0, "runs_without_run_started": 0, "events": 0, "malformed_lines": 0,
    "calls": 0, "eligible_calls": 0, "calls_without_prompt_estimate": 0,
    "excluded": {"estimated": 0, "unavailable": 0, "synthetic": 0, "inconsistent": 0},
    "sanitized_labels": 0, "unparsed_worker_dirs": 0
  },
  "amplification": {
    "all": {"count": 0, "sum_input": 0, "sum_prompt_estimate": 0, "sum_output": 0,
            "pooled_amplification": null, "pooled_output_ratio": null,
            "amplification": "stats", "output_ratio": "stats", "cache_read_share": "stats"},
    "by_role": {"implementer": "group"},
    "by_capability_class": {"standard": "group"}
  },
  "session_growth": {
    "by_node_bucket": {"1": "bucket", "2-3": "bucket", "4+": "bucket"},
    "by_run": {"run-...": {"calls": 0, "cumulative_input": [], "growth_exponent": null,
                           "input_by_node_bucket": {"1": 0, "2-3": 0, "4+": 0, "none": 0}}}
  },
  "fanout": {
    "by_run": {"run-...": {"worker_nodes": {"reviewer": 0}, "worker_nodes_total": 0,
                           "planner_input": 0, "worker_input": 0, "fanout_input_ratio": null,
                           "duplicated_fixed_overhead": 0, "overhead_share": null,
                           "overhead_per_worker_call": "stats", "negative_overhead_calls": 0,
                           "repeat_attempt_input": 0, "retries": 0, "escalations": 0, "fallbacks": 0}},
    "totals": "same keys, ratios recomputed from sums"
  },
  "resume": {
    "by_run": {"run-...": {"resumes": 0, "pauses": 0, "checkpoints": 0, "warm_nodes": 0,
                           "run_input": 0, "resume_overhead_input": 0, "resume_first_input": 0,
                           "cold_resume_input": 0, "resume_share": null, "resume_first_share": null}},
    "totals": "same keys, shares recomputed from sums"
  },
  "worker_files": {"by_role": {"implementer": {"prompt": {"sum_bytes": 0, "size": "stats"}}},
                   "prompt_bytes_per_estimated_token": "stats"},
  "provider_models": {"claude-code": ["sonnet"]},
  "privacy": {"rule": "max80-no-whitespace", "strings_checked": 0, "passed": true}
}
```

(`"stats"`, `"group"` and `"bucket"` stand for the objects defined above.)

### Allowed strings

Only these strings may appear as keys or values:

1. fixed metric keys defined in this document, including bucket labels `1`,
   `2-3`, `4+`, `none` and file keys `prompt`, `stdout`, `stderr`,
   `last_message`, `other`;
2. run ids, which must match `^run-\d{8}T\d{6}Z-[0-9a-f]{6}$`. A run directory
   that does not match is skipped and counted as a malformed run, not echoed;
3. role names, capability classes, provider names and model names copied from
   telemetry `data`;
4. the constants `schema`, `estimate_method` and `privacy.rule`.

These are excluded: node ids, worker directory names, goals, summaries,
reasons, failure details, prompt or transcript text, commit hashes and file
paths.

### Privacy rule

```text
violates(s) = len(s) > 80  or  re.search(r"\s", s) is not None
```

1. **Label sanitizing (before aggregation).** A role, class, provider or model
   label from telemetry where `violates(label)` is true becomes `"other"`, and
   `coverage.sanitized_labels` is incremented. One odd model string therefore
   cannot block a report.
2. **Final check (before writing).**
   `check_privacy(report, forbidden=...)` walks every dict key and every string
   value recursively. The report itself holds no node ids, so the caller must
   supply them: while scanning, `measure` collects every node id and worker
   directory name into a set held only in memory, and passes it as `forbidden`.
   The check rejects any string equal to a member of `forbidden`, unless the
   string is also an allowed role, class, provider or model label. On any violation it
   raises `ValueError`, naming the JSON path of the offending item but not its
   text. The report is not written. `privacy.strings_checked` and
   `privacy.passed` are filled in only after the check passes.

The whitespace test rejects every multi-word sentence, so prose cannot pass.
The length bound catches long single tokens such as paths or encoded blobs.

## 5. Implementation shape

- Module: `src/agent_os/orchestrator/context_economy.py` with
  `measure(runs_dir: Path, run_ids: list[str] | None = None) -> dict` and
  `check_privacy(report: dict, forbidden: Iterable[str] = ()) -> int` (returns
  the number of strings checked). `measure` calls
  `check_privacy(report, forbidden=seen_ids)` before returning, where
  `seen_ids` is the set of node ids and worker directory names it collected
  during the scan. That set is never returned or stored. With the default
  empty `forbidden`, only the length and whitespace rules apply.
- CLI: `agent-os orchestrate context-economy [--run RUN_ID ...] [--out PATH]`.
  It prints the JSON report. `--out` writes it only if `measure`, and therefore
  its `check_privacy` call, passed. It
  defaults to `<home>/reports/context-economy-<UTC>.json`, gitignored runtime
  state, and the timestamp goes in the file name only.
- Reuse `ledger.read_events` and `usage.CHARS_PER_TOKEN`. Do not add a second
  telemetry parser or token estimator.

## 6. Tests (synthetic fixtures, no network)

Each new test file starts with
`sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))` before it
imports `agent_os`. Fixtures write `telemetry.jsonl` with the ledger schema and
empty or fixed-size worker files into a temporary `runs/` directory. Required
cases:

1. Amplification: hand-computed `A`, `R`, pooled ratios, median and p90 per
   role and class. Estimated, unavailable, synthetic and inconsistent calls are
   excluded and counted. `input_tokens` is not double-counted with cache fields.
2. Growth: nodes with 1, 3 and 5 eligible calls land in buckets `1`, `2-3` and
   `4+`, and `growth_n` uses ordinals. A constant per-call series gives
   `growth_exponent` about 1. A linearly rising series gives a clearly higher
   exponent.
3. Fan-out: distinct worker nodes per role, planner vs worker input, and
   `duplicated_fixed_overhead` equal to the hand sum, including a negative call.
4. Resume: two resumes. Warm detection holds for a checkpointed node, a
   previously called node and an `attempt > 1` call. Cold nodes are excluded,
   and the shares are correct. Runs without `run_resumed` are absent from
   `resume.by_run`.
5. Sizes only: worker files contain a sentinel phrase, and the harness output
   neither contains it nor contains any node id. The test patches `open` and
   `Path.read_text` for the workers tree to prove that files are never opened.
6. Privacy: a planted node id, a goal sentence and an 81-character label are
   rejected or sanitized as specified. `check_privacy(report, forbidden={id})`
   rejects a report string equal to `id`, and passes the same report when
   `forbidden` is empty. A clean report passes, and two runs of
   `measure` produce identical JSON.

## 7. Recording findings

When the harness runs over real history, record the result with existing
record formats in `projects/personal-agent-os/orchestrator-os/records/`:

- **EXP-NNNN** (`experiments/`): hypothesis that cumulative input grows
  superlinearly with calls per node, and that fixed per-worker overhead
  dominates worker input. Method: this harness over all finished runs. The
  falsifiers are `growth_exponent` at or below 1.1 for most runs and an
  `overhead_share` below 0.5.
- **EVR-NNNN** (`evaluations/`, schema `personal-agent/evidence-record/v1`,
  `task_family: "context_economy"`): `metrics` copies aggregate figures from
  the report only, such as pooled amplification per role, bucket growth
  medians, fan-out totals and resume shares, plus `model_calls: 0` and
  `spend_usd: 0`. `links` contains `measures` →
  `src/agent_os/orchestrator/context_economy.py`, `relates_to` → `IMP-0018`, and
  `relates_to` → `EVR-0013`. `provenance.source` names the CLI command, and
  coverage counts state how many calls were exact.

Findings are baselines, not optimizations. Promoting any reduction still needs
the controlled evaluation in the roadmap's promotion rule.
