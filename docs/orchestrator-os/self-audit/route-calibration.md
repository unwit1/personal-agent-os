# Route calibration via shadow testing (IMP-0015 third-party optimization track) — design

Status: design for implementation, tracked improvement **IMP-0015**, from
[model-infrastructure-manager.md](../../../projects/personal-agent-os/roadmap/model-infrastructure-manager.md)
(third-party optimization track, measurement first). Measurement base: existing
Orchestrator telemetry (model completions, escalations, retries, and review
outcomes per task family).

The calibrator answers one question for every task family and capability class
pair: **given observed task outcomes and their review verdicts, at which
escalation threshold would the estimated pass rate of the cheaper route
meet or exceed a target bar (0.9)?** A threshold is a score above which
escalation to a stronger model is recommended; a lower threshold escalates
more often. The calibrator is deterministic and offline. It makes no model
calls and no network calls. It **records advice only** and never changes what
Orchestrator runs. No routing, scheduling, or dispatch code imports it. The
advisor estimates, does not validate. Limits in §8 apply.

## 0. Prior art

`agent-os orchestrate prior-art lookup "RouteLLM / strong-vs-weak routing /
calibrated threshold / shadow advisor / cost-vs-quality curve"`
(offline registry) returned one match:

| Id | Decision | What it gives here |
|---|---|---|
| PA-routellm | BORROW | Choosing the escalation threshold against a cost-vs-quality curve on a development set. The cost-vs-quality curve traces what pass rate is achievable at each threshold. The recommended threshold is the smallest one whose kept pass rate meets the target bar (0.9). Borrowed: the grid of thresholds and the curve concept. Rejected: trained routers, torch dependency, and online updates. |

The registry has no other directly applicable entry. The threshold selection
is custom. The estimator is simple: Beta posteriors and Wilson bounds,
suitable for small, slowly growing sample sizes per family and class. The
cost model is specific to Orchestrator routing state.

## 1. Purpose

The third-party optimization track, measurement-first methodology (IMP-0015)
requires calibration advice that estimates, from real outcomes, whether cheaper
routes (lower capability class) would pass validation at a given escalation threshold,
and recommends a threshold that targets 90% pass rate on the kept-cheap tasks.

This is shadow mode: the advice is recorded and analyzed offline. It never
touches dispatch, routing configuration, or live decisions. A real promotion to
automatic escalation thresholds requires separate held-out validation evidence
(EVR) showing noninferior quality and lower cost per verified task.

## 2. Inputs

The calibrator reads only telemetry already collected by existing infrastructure.

### 2.1 Model events

From `telemetry.jsonl`, extract these event types:

| Event | Relevant fields | Meaning |
|---|---|---|
| `model_completed` | `role`, `provider`, `capability_class`, `effort`, `node` | Attempted a task on a model; effort is a relative cost proxy. |
| `model_failed` | `role`, `provider`, `capability_class`, `effort`, `node` | Model call failed or returned an error. Treated as a run (not a pass). |
| `model_escalated` | `node`, `from_class`, `to_class` | Escalated from weaker to stronger; not a task outcome, used to infer initial route choice. |
| `retry` | `node` | Task was retried after failure; used for context only. |
| `fallback` | `node` | Switched providers within the same class; used for context only. |
| `tests_completed` | `node`, `passed` | Test/validator ran, with pass/fail outcome. |
| `review_completed` | `subject`, `verdict`, `material_findings` | Code review of task node (the event `node` is the reviewer, keyed by `data.subject`). Verdict is `approved`, `blocked`, or similar. |

Events are ordered by `seq` (sequence number). A `.repair<N>` node inherits the review
counters of its subject `<subject>`, via id parsing.

### 2.2 Capability class and effort

Each `model_completed` or `model_failed` event carries `capability_class`
(e.g., `cheap`, `standard`, `strong`, `reasoning`; the exact values come from
the routing config) and `effort` (a relative cost metric, where cheap is lower).
These are fixed per provider/model combination.

## 3. Labels

For each task (identified by `node`), determine whether the kept-cheap route would have
**passed validation and review**:

| Outcome | Label | Meaning |
|---|---|---|
| Task completed on cheap/standard class AND all downstream validators/reviewers approved | `cheap_route_passed=True` | The cheap route was sufficient. |
| Task was escalated OR failed validators/reviewers after trying the cheap route | `cheap_route_passed=False` | The cheap route was insufficient. |
| Task never attempted the cheap route (started on strong class), or outcome is ambiguous | `cheap_route_passed=unlabeled` | No training signal; excluded from pass-rate estimation. |

A task that started on a cheap class and later escalated is labeled `False`.
A task that started on a strong class with no failed cheaper attempt is unlabeled.

## 4. Estimator

For each `(task_family, initial_capability_class)` pair:

1. **Collect labeled outcomes** where `cheap_route_passed in [True, False]`.
   Exclude unlabeled.
2. **Count** `n_pass` (True outcomes) and `n_total` (True + False outcomes).
3. If `n_total < min_samples` (default `min_samples = 5`), the pair is too sparse;
   report `insufficient_samples` and proceed to the next pair.
4. **Posterior mean** using Beta(α, β) with uniform prior Beta(1, 1):
   ```
   p_pass = (n_pass + 1) / (n_total + 2)
   ```
5. **Confidence interval** using Wilson score, 95% level:
   ```
   wilson_lower = (p_hat + z²/2n - z√(p_hat(1-p_hat)/n + z²/4n²)) / (1 + z²/n)
   where z = 1.96 and p_hat = n_pass / n_total
   ```
   The lower bound is conservative; it captures aleatory (measurement) uncertainty
   and is used to decide escalation, not p_pass itself.

## 5. Calibration

For each `(family, class)` pair with sufficient samples:

1. **Grid thresholds** from 0.50 to 0.95 in increments of 0.05 (fixed set: 0.50, 0.55, ..., 0.95).
2. **Decision rule at each threshold**:
   ```
   keep_cheap at threshold T := wilson_lower >= T
   ```
   If the conservative bound meets the threshold, keep the cheap route for future
   tasks of that family and class. Otherwise escalate.
3. **Cost-vs-quality curve**: For each threshold, record:
   - `threshold`: the escalation threshold.
   - `kept_cheap_count`: how many tasks would remain on cheap (pass the rule).
   - `kept_cheap_pass_rate`: what fraction of kept-cheap tasks actually passed.
   - `escalated_count`: how many would be escalated (fail the rule).
   - `escalated_pass_rate`: of those escalated, what fraction passed anyway.

4. **Recommended threshold**: The smallest threshold T such that
   ```
   kept_cheap_pass_rate(T) >= target  (target = 0.9 by default)
   ```
   If no threshold achieves the target, report the highest achievable and a reason code.

Reason codes include: `target_not_achievable`, `insufficient_samples`, `low_overall_pass_rate`.

## 6. Output schema and privacy

Aggregates only. The keys are serialized with `sort_keys=True`. `generated_at`
is the only nondeterministic field.

```json
{
  "schema": "personal-agent/orchestrator-route-calibration/v1",
  "mode": "shadow",
  "dispatch_changes": 0,
  "generated_at": "iso-8601",
  "task_families": ["family1", "family2"],
  "calibration": {
    "task_family": {
      "initial_class": {
        "samples": 0,
        "labeled_outcomes": 0,
        "n_pass": 0,
        "n_fail": 0,
        "p_pass_mean": 0.0,
        "wilson_lower_95": 0.0,
        "min_samples": 5,
        "status": "ok | insufficient_samples | low_overall_pass_rate",
        "curve": [
          {
            "threshold": 0.5,
            "kept_cheap_count": 0,
            "kept_cheap_pass_rate": 0.0,
            "escalated_count": 0,
            "escalated_pass_rate": 0.0
          }
        ],
        "recommended_threshold": 0.75,
        "reason_codes": ["reason1"]
      }
    }
  },
  "privacy": {"rule": "max80-no-whitespace", "strings_checked": 0, "passed": true}
}
```

**Privacy** follows context-economy §4 without changes. Node ids, task subjects,
review verdicts, provider credentials, and user-facing paths are **never emitted**.
All string keys are fixed: schema id, mode, reason codes, capability-class names,
and task-family names (already sanitized in telemetry). Before returning, `build`
calls `assert_aggregate_only(report, forbidden)`, where `forbidden` is the set
of node ids and subjects extracted during the read. It fills `privacy.strings_checked`
and `passed` only after the check succeeds. `report()` calls `assert_aggregate_only`
again before writing `--out`.

## 7. Limits and caveats

### 7.1 Selection bias

The advisor observes only tasks that Orchestrator chose to route. Tasks never
attempted on the cheap route contribute no labeled outcome, creating positive
bias: estimated pass rates assume that future cheap routes will have similar
coverage and difficulty. Hard tasks are underrepresented.

### 7.2 Small samples

With `min_samples = 5`, many `(family, class)` pairs will have fewer than 10
labeled outcomes, especially early in deployment. Wilson bounds are wider when
`n` is small; confidence is lower. The advisor remains deterministic but
recommends caution when curve counts are low.

### 7.3 No counterfactual

The advisor cannot observe what would happen if Orchestrator had taken a different
route. Tasks that escalated to strong did not run on cheap; their cheap-route pass
rate is estimated from tasks that did run on cheap. The estimate may not apply
to a different distribution of tasks or effort levels.

### 7.4 Effort proxy

`effort` is a relative cost metric, not model quality. Two different cheap-class
models may have different pass rates. The calibrator groups by `capability_class`,
not per model, so it trades off precision for stability on small samples.

## 8. Implementation shape

- Module: `src/agent_os/orchestrator/route_calibration.py`.
  - `estimate_family(outcomes) -> dict` is pure. Returns posterior mean, Wilson
    bound, sample counts per `(family, class)` pair.
  - `calibrate_threshold(estimate, target=0.9) -> dict` returns the cost-vs-quality
    curve and recommended threshold per family and class.
  - `build(run_dirs) -> dict` reads telemetry and produces estimates.
  - `report(home=None, out=None) -> dict` formats and writes the output.
  - It reuses `ledger.read_events`, privacy checks from context-economy,
    `RUN_ID`, `PRIVACY_RULE`, and `assert_aggregate_only`. It adds no second
    telemetry parser.
- CLI: `agent-os orchestrate route-calibration [--home PATH] [--out PATH]`.
  Prints the report.
- **Shadow guarantee.** Only `cli.py` imports `route_calibration`. `engine.py`,
  routing, scheduling and existing modules do not. A test asserts this.
  The calibrator writes nothing under `runs/`.
- Protected control-plane paths are not touched.

## 9. Tests (synthetic fixtures, no network)

Each test file starts with
`sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))`.
Fixtures write ledger-schema `telemetry.jsonl` lines into a temporary `runs/`
directory. Required cases:

1. **Formulas.** A task family with 5+ labeled outcomes (mix of `cheap_route_passed=True`
   and `False`). Compute `n_pass`, `n_fail`, `p_pass` mean, Wilson lower bound by hand
   and verify against the function output.
2. **Insufficient samples.** A `(family, class)` pair with 3 outcomes (`< min_samples=5`).
   Status should be `insufficient_samples` and the pair should not appear in the curve.
3. **Threshold curve.** A family with 20+ outcomes and varying pass rates. Verify that
   the curve traces threshold 0.50–0.95 correctly, that `kept_cheap_count` and `passed_rate`
   change monotonically, and that the recommended threshold is the smallest T where
   `kept_cheap_pass_rate >= 0.9`.
4. **Unlabeled outcomes.** Add tasks that started on strong class or have ambiguous
   verdict. Verify they are excluded from `labeled_outcomes` and `n_total`.
5. **Privacy and strings only.** Node ids, subjects, and sentinel phrases are absent.
   `assert_aggregate_only` passes. Two builds are identical except for `generated_at`.
6. **Shadow.** `mode == "shadow"` and `dispatch_changes == 0`, and no module except `cli.py`
   imports `route_calibration`.

## 10. Offline evaluation and promotion

The worker builds the module and its tests. The **host** runs it over the
real local telemetry:

```text
agent-os orchestrate route-calibration --out docs/orchestrator-os/self-audit/route-calibration-baseline.json
```

Results are recorded with existing formats under
`projects/personal-agent-os/orchestrator-os/records/`:

- **EXP** (`experiments/`). Hypothesis: A calibrated cheaper-route escalation
  threshold per task family would achieve 90% pass rate on the kept-cheap set,
  reducing paid-model spend. Method: shadow calibration over all local runs.
  Falsifiers: `wilson_lower < 0.8` for a major task family (under-confidence),
  or a held-out validation EVR showing higher failure rate than predicted.
- **EVR** (`evaluations/`, schema `personal-agent/evidence-record/v1`,
  `task_family: "route_calibration"`). `metrics` copies report aggregates:
  per-family sample counts, p_pass estimates, recommended thresholds, curve
  data where applicable. Plus `model_calls: 0`, `spend_usd: 0`,
  `dispatch_changes: 0`. `links`: `measures` → `src/agent_os/orchestrator/route_calibration.py`,
  `relates_to` → `IMP-0015`, `relates_to` → `PA-routellm`.

Promotion to automatic escalation thresholds requires a separate held-out
validation (EVR) showing noninferior quality and lower cost per verified
task compared to the incumbent routing. Shadow advice alone is not evidence
that automatic thresholds will improve production routing.

## 11. Integration into routing

The calibration output is static advice, not a live router. When/if thresholds
are promoted from shadow to active:

1. A separate configuration step applies the recommended threshold to the routing
   layer's escalation policy.
2. The routing layer checks the escalation score (from the routing model or a
   heuristic) against the threshold and decides whether to escalate.
3. Telemetry continues to record model completions, escalations, and outcomes.
4. The next calibration run re-estimates from the new data and can recommend
   threshold adjustments.

This keeps the calibrator decoupled from live routing code.
