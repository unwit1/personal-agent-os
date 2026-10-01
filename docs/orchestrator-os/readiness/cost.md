# Cost and usage caps

## Checklist items

- **CC-1 — Launch budget gate:** With `max_launches=1` and two tasks, the run reaches the `budget_exhausted` approval gate and records no more than one launch before approval.
- **CC-2 — Usage accounting:** A completed run contains `usage`, with per-run totals populated or present as empty totals. Expected totals keys: `input_tokens`, `cached_tokens`, `output_tokens`, `workers`, `cache_write_tokens`, `reasoning_tokens`, `cost_usd`, `calls_exact`, `calls_estimated`, `calls_unavailable`.
- **CC-3 — Provider usage exhaustion:** When every synthetic provider reports quota exhaustion, the run waits or blocks instead of retrying indefinitely.
- **CC-4 — Bounded retries and escalation:** Provider/process retries and escalation remain within policy limits.
- **CC-5 — Token or money cap policy:** `merge_policy({'max_usd': 1})` raises `PolicyError`. `DEFAULT_POLICY` has launch-count limits but no token or money cap key. **GAP:** caps are launch-count only; usage totals are accounting, not enforced limits.
- **CC-6 — No paid API use in readiness checks:** Every provider in the embedded fixture engine registry uses the `synthetic` adapter.

## Commands

- `Get-Content src/agent_os/orchestrator/model.py` — inspected policy defaults and key validation.
- `python -m unittest tests.test_readiness_cost -v` — assigned validator; final run passed.
- OS: Windows 10.0.26100.9444; PowerShell 5.1.26100.9444.
- Python: 3.14.7.

## Results

| item | Python fixture | JavaScript fixture | observed | status PASS/GAP/FAIL |
|---|---|---|---|---|
| CC-1 | PASS | PASS | `APPROVAL_REQUIRED`, last gate `budget_exhausted`, launches ≤ 1 before approval | PASS |
| CC-2 | PASS | PASS | Completed runs contain usage totals; synthetic usage may be unavailable while totals remain present | PASS |
| CC-3 | PASS | PASS | Both providers report quota; run waits with usage reset state, no retry loop | PASS |
| CC-4 | PASS | PASS | Attempts ≤ 3 with two retries; escalations ≤ 2 | PASS |
| CC-5 | N/A | N/A | Unknown `max_usd` rejected; no enforced token or money cap in defaults | GAP |
| CC-6 | PASS | PASS | Both fixture runs use registry entries with `adapter=synthetic` only | PASS |

## Failures and gaps

- Initial validator attempt: `test_CC6_synthetic_registry_only` errored because the test treated `engine.registry` as a property. Inspection showed the engine exposes `registry()`; the test now checks `self.engine.registry().providers`.
- Final validator: all six tests passed (`Ran 6 tests in 18.934s`, `OK`).
- Policy gap: launch count is the only enforced cost proxy. There is no per-run token or money cap; `cost_usd` in usage totals does not impose a stop condition.

## Raw output

```text
Initial: python -m unittest tests.test_readiness_cost -v
test_CC1_launch_budget_stops_before_approval ... ok
test_CC2_run_usage_totals_exist ... ok
test_CC3_out_of_usage_waits_without_looping ... ok
test_CC4_retries_and_escalation_are_bounded ... ok
test_CC5_unknown_money_cap_is_rejected ... ok
test_CC6_synthetic_registry_only ... ERROR
AttributeError: 'function' object has no attribute 'providers'
Ran 6 tests in 15.695s
FAILED (errors=1)

Final: python -m unittest tests.test_readiness_cost -v
test_CC1_launch_budget_stops_before_approval ... ok
test_CC2_run_usage_totals_exist ... ok
test_CC3_out_of_usage_waits_without_looping ... ok
test_CC4_retries_and_escalation_are_bounded ... ok
test_CC5_unknown_money_cap_is_rejected ... ok
test_CC6_synthetic_registry_only ... ok
Ran 6 tests in 18.934s
OK
```
