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

The calibrator reads only `telemetry.jsonl` from existing run directories.

| Event | Fields used | Use |
|---|---|---|
| `model_completed`, `model_failed` | `role`, `provider`, `capability_class`, `effort` | The first such event of a node fixes its initial class, effort and provider. |
| `model_escalated` | `from`, `to` | Counts as an escalation; `to` gives the final class. |
| `retry`, `fallback` | none | Counted for context only. |
| `tests_completed` | `passed` | Validation result (the last event wins). |
| `review_completed` | `subject`, `verdict`, `material_findings` | Review result for the subject node. |

**Reviewer nodes are excluded.** A `.repair<N>` node is attributed to the review
of its subject node, not to a review of its own.

## 4. Label

`cheap_route_passed` is set per non-reviewer node:

- **True**: the initial cheap class passed tests and review with no escalation.
- **False**: the node escalated, its tests failed, or its review was blocking.
- **Unlabeled** (`None`): otherwise, i.e. no escalation and no test or review
  evidence. Unlabeled nodes are counted in coverage but not in estimates.

## 5. Estimator

Per task family and initial capability class, over labeled outcomes only:
`n` labeled, `passes` True.

- `p_pass` = Beta(1,1) posterior mean = (passes + 1) / (n + 2).
- `wilson_lower` = 95% Wilson lower bound (z = 1.96) of passes / n; the decision
  uses this conservative bound, not `p_pass`.
- A cell is `sufficient` only when `n >= min_samples` (default 5).

## 6. Calibration

1. Grid of thresholds 0.50, 0.55, ..., 0.95.
2. At threshold T a sufficient cell is `keep_cheap` when `wilson_lower >= T`.
3. Curve point per threshold: `threshold`, `cheap_share` (labeled share in
   kept cells), `kept_pass_rate` (pass rate over kept cells, null if none), and
   `escalations_avoided`.
4. **Recommended threshold**: the smallest T whose `kept_pass_rate >= target`
   (default 0.9).
5. Reason codes: `threshold_selected`, `no_threshold_meets_target` (sufficient
   cells exist but none reach the target; threshold is null), and
   `insufficient_evidence` (no sufficient cell).
6. Per-cell advice, for the recommended threshold (0.95 when none):
   `keep_cheap`, `escalate_earlier`, or `insufficient_data`.

## 7. Output schema and privacy

Aggregates only. Top-level keys: `schema`
(`personal-agent/orchestrator-route-calibration/v1`), `mode` (shadow),
`generated_at`, `routing_changed` (always false), `runs`, `coverage`, `cells`
(per family and class: `n`, `passes`, `unlabeled`, `escalated`, `p_pass`,
`wilson_lower`, `sufficient`, effort and provider counts), `calibration`
(`curve`, `target`, `recommended_threshold`, `reason`), `advice`, and `method`.

No node ids are emitted. `build` sanitizes family, class, effort and provider
labels, then runs `assert_aggregate_only` with the node ids as forbidden
strings. `report()` checks again before writing `--out`.

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
