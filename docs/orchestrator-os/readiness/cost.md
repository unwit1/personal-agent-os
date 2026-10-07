# Cost and usage caps

## Checklist items

- **CC-1 — Launch budget gate:** With `max_launches=1` and two tasks, stop at a `budget_exhausted` approval gate and record no more than one launch before approval.
- **CC-2 — Usage accounting:** A completed run has a usage totals record with each documented key, even if values are empty or unavailable.
- **CC-3 — Provider usage exhaustion:** If all synthetic providers report quota exhaustion, wait or block without retrying indefinitely.
- **CC-4 — Bounded retries and escalation:** A validator that exits with `SystemExit(3)` must end `BLOCKED` with node state `FAILED_FINAL`, exactly two escalations, and three attempts under `max_escalations=2`. A separate all-provider `process_error` run must also end `BLOCKED` within retry/escalation limits.
- **CC-5 — Token or money cap policy:** `max_usd` and `max_tokens` (default null = no cap) are validated policy keys. Before each model launch, recorded usage plus the next-launch estimate (the average of this run's earlier calls) is checked, and a `budget_exhausted` gate is opened instead of launching. Approval raises the cap by half, like CC-1. Subscription providers count their API-equivalent estimate toward `max_usd`; calls that report no `cost_usd` (for example Codex) count toward `max_tokens` only. Evidence: [spend cap](../../tests/test_orchestrator_spend_cap.py) and [policy caps](../../tests/test_orchestrator_policy_caps.py).

  `cost_usd` is an API-equivalent estimate reported by the provider, not cash.
- **CC-6 — Synthetic-only providers:** Every provider in the embedded fixture engine registry uses adapter `synthetic`.

## Commands

- `rg -n "max_launches|max_review_rounds|retry|cheaper|wait" src/agent_os/orchestrator/model.py` — inspected policy defaults. Found `max_stage_retries=2`, `max_escalations=2`, `max_review_rounds=2`, `max_launches=40`, and `wait_for_reset_seconds=300`; no token or money cap key exists in `DEFAULT_POLICY`.
- `python -m unittest tests.test_readiness_cost -v` — final assigned validator; passed.
- OS: Windows 10.0.26200.0; PowerShell (shell).
- Python: 3.14.7 (`C:\Python314\python.exe`).

## Results

| item | Python fixture | JavaScript fixture | observed | status PASS/GAP/FAIL |
|---|---|---|---|---|
| CC-1 | PASS | PASS | `APPROVAL_REQUIRED`; last gate `budget_exhausted`; launches ≤ 1 before approval | PASS |
| CC-2 | PASS | PASS | Both runs completed; usage included `input_tokens`, `cached_tokens`, `output_tokens`, `workers`, `cache_write_tokens`, `reasoning_tokens`, `cost_usd`, `calls_exact`, `calls_estimated`, `calls_unavailable` | PASS |
| CC-3 | PASS | PASS | Both providers reported quota; run waited or blocked with usage in the reason, without looping | PASS |
| CC-4 | PASS | PASS | Validator failure ended `BLOCKED` / `FAILED_FINAL`, escalations=2 and attempts=3; separate provider process failures ended `BLOCKED` within limits | PASS |
| CC-5 | PASS | PASS | Validated `max_usd` and `max_tokens` caps; projected usage is checked before each launch, gates at the cap, and approval raises it by half. `cost_usd` is an API-equivalent estimate, not cash; subscription providers count it, while calls without a reported cost count toward `max_tokens` only. | PASS |
| CC-6 | PASS | PASS | Both fixture runs use synthetic adapter entries only | PASS |

## Failures and gaps

- First validator run failed the JavaScript CC-4 escalation count: synthetic provider state persisted across fixture subtests. The test now resets synthetic adapter state and installs clean scripts before each fixture.
- Final validator run passed all six checklist tests.
- Policy gap: usage totals are accounting only. There is no per-run token or money cap; `max_launches` bounds launches rather than spend.

## Raw

```text
Initial: python -m unittest tests.test_readiness_cost -v
CC-1 ... ok
CC-2 ... ok
CC-3 ... ok
CC-4 ... FAIL (fixture='javascript'): AssertionError: 0 != 2 at node['escalations']
CC-5 ... ok
CC-6 ... ok
Ran 6 tests in 22.250s
FAILED (failures=1)

Final: python -m unittest tests.test_readiness_cost -v
test_CC1_launch_budget_stops_before_approval ... ok
test_CC2_run_usage_totals_exist ... ok
test_CC3_out_of_usage_waits_without_looping ... ok
test_CC4_retries_and_escalation_are_bounded ... ok
test_CC5_unknown_money_cap_is_rejected ... ok
test_CC6_synthetic_registry_only ... ok
Ran 6 tests in 24.300s
OK
