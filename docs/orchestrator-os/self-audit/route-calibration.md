# Route calibration via shadow testing (IMP-0015 third-party optimization track) — design

Status: design for implementation, tracked improvement **IMP-0015**, from
[model-infrastructure-manager.md](../../../projects/personal-agent-os/roadmap/model-infrastructure-manager.md)
(third-party optimization track, measurement first). Measurement base: existing
Orchestrator telemetry (model completions, escalations, retries, and review
outcomes per task family).

The calibrator answers one question for every task family and capability class
pair: **given observed task outcomes and their review verdicts, at which
escalation threshold would the estimated pass rate of the cheaper route
meet or exceed a target bar (0.9)?** A threshold (T) is a bar on the Wilson
confidence bound lower bound. If wilson_lower >= T, the cheap route is kept;
otherwise, escalation to a stronger model is recommended. The calibrator is
deterministic and offline. It makes no model calls and no network calls. It
**records advice only** and never changes what Orchestrator runs. No routing,
scheduling, or dispatch code imports it. The advisor estimates, does not
validate. Limits in §8 apply.

## 1. Purpose

The third-party optimization track, measurement-first methodology (IMP-0015)
requires calibration advice that estimates, from real outcomes, whether cheaper
routes (lower capability class) would pass validation at a given escalation threshold,
and recommends a threshold that targets 90% pass rate on the kept-cheap tasks.

This is shadow mode: the advice is recorded and analyzed offline. It never
touches dispatch, routing configuration, or live decisions. A real promotion to
automatic escalation thresholds requires separate held-out validation evidence
(EVR) showing noninferior quality and lower cost per verified task.

## 2. Prior art

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

## 3. Inputs

The calibrator reads only telemetry already collected by existing infrastructure.

### 3.1 Model events

From `telemetry.jsonl`, extract these event types. **Reviewer nodes are excluded.**

| Event | Relevant fields | Meaning |
|---|---|---|
| `model_completed` | `role`, `provider`, `capability_class`, `effort` | Attempted a task on a model; effort is a relative cost proxy. |
| `model_failed` | `role`, `provider`, `capability_class`, `effort` | Model call failed or returned an error. Treated as a run (not a pass). |
| `model_escalated` | `from`, `to` | Escalated from weaker to stronger; not a task outcome, used to infer initial route choice. |
| `retry` | — | Task was retried after failure; used for context only. |
| `fallback` | — | Switched providers within the same class; used for context only. |
| `tests_completed` | `passed` | Test/validator ran, with pass/fail outcome. |
| `review_completed` | `subject`, `verdict`, `material_findings` | Code review of task node. Verdict is `approved`, `blocked`, or similar. |

Events are ordered by `seq` (sequence number). A `.repair<N>` node inherits the review
counters of its subject `<subject>`, via id parsing.

### 3.2 Capability class and effort

Each `model_completed` or `model_failed` event carries `capability_class`
(e.g., `cheap`, `standard`, `strong`, `reasoning`; the exact values come from
the routing config) and `effort` (a relative cost metric, where cheap is lower).
These are fixed per provider/model combination.

## 4. Label

For each task, determine whether the kept-cheap route would have **passed validation and review**:

- **`True`**: The initial cheap capability class passed all tests and review with no escalation.
- **`False`**: The task was escalated, or it failed tests, or the review issued a blocking verdict.
- **`unlabeled`**: The task never attempted the cheap route (started on a strong class), or the outcome is ambiguous. Excluded from pass-rate estimation.

## 5. Estimator

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

## 6. Calibration

For each `(family, class)` pair with sufficient samples:

1. **Grid thresholds** from 0.50 to 0.95 in increments of 0.05 (fixed set: 0.50, 0.55, ..., 0.95).
   T is a bar on the Wilson lower bound.
2. **Decision rule at each threshold**:
   ```
   keep_cheap at threshold T := wilson_lower >= T
   ```
   If the conservative bound meets or exceeds T, keep the cheap route for future
   tasks of that family and class. Otherwise escalate.
3. **Cost-vs-quality curve**: For each threshold, record:
   - `threshold`: the escalation threshold value.
   - `kept_count`: how many tasks would remain on cheap (pass the rule).
   - `kept_pass_rate`: what fraction of kept tasks actually passed.
   - `escalated_count`: how many would be escalated (fail the rule).

4. **Recommended threshold**: The smallest threshold T such that
   ```
   kept_pass_rate(T) >= target  (target = 0.9 by default)
   ```
   If no threshold achieves the target, report the highest achievable and a reason code.

Reason codes include: `target_achievable`, `insufficient_samples`, `low_overall_pass_rate`.

## 7. Output schema and privacy

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
            "kept_count": 0,
            "kept_pass_rate": 0.0,
            "escalated_count": 0
          }
        ],
        "recommended_threshold": 0.75,
        "reason_codes": ["reason1"]
      }
    }
  },
  "privacy": {"rule": "assert_aggregate_only", "strings_checked": 0, "passed": true}
}
```

**Privacy**: Node ids, task subjects, review verdicts, provider credentials, and user-facing paths are **never emitted**. All string keys are fixed: schema id, mode, reason codes, capability-class names, and task-family names (already sanitized in telemetry). Before returning, `build` calls `assert_aggregate_only(report, forbidden)`, where `forbidden` is the set of node ids and subjects extracted during the read. The function fills `privacy.strings_checked` and `passed` only after the check succeeds. `report()` calls `assert_aggregate_only` again before writing `--out`.

## 8. Limits and caveats

The advisor has three key limitations:

1. **No counterfactual for strong-start nodes.** The advisor cannot observe what
   would have happened if a node had taken a cheaper route instead. Tasks that
   did not run on cheap contribute no labeled outcome and cannot inform the pass
   rate estimate.

2. **Ladder selection bias.** The advisor observes only tasks that Orchestrator
   routed through the cheap class. This creates positive bias: estimated pass rates
   are conditioned on Orchestrator's routing choice and may not apply to hard tasks
   never attempted on cheap.

3. **Small samples.** With `min_samples = 5`, many `(family, class)` pairs will
   have fewer than 10 labeled outcomes early in deployment. Wilson bounds widen
   with small `n`; confidence is lower.

## 9. How the supervisor runs it

The worker builds the module in `src/agent_os/orchestrator/route_calibration.py`
and its tests in `tests/`. The **supervisor** runs the calibrator over real local
telemetry after this worktree is merged:

```text
agent-os orchestrate route-calibration --home --out docs/orchestrator-os/self-audit/route-calibration-baseline.json
```

The CLI is deterministic and offline; `--home` reads local telemetry, `--out`
writes a privacy-safe aggregate report. Promotion to automatic thresholds requires
a separate held-out validation (EVR) showing noninferior quality and lower cost
per verified task compared to the incumbent routing. Shadow advice alone is not
evidence; the supervisor gate is noninferior quality plus cost savings.
