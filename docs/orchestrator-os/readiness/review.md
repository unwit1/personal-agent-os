# Review gates

## Checklist items

- **RG-1:** Structured reviewer verdicts with material findings route work to a repairer; repaired work is reviewed again.
- **RG-2:** Unstructured “looks good” feedback is rejected as malformed review output.
- **RG-3:** Unresolved findings after `max_review_rounds` open an approval gate.
- **RG-4:** A worker's self-reported success cannot override a failing validator.
- **RG-5:** Integration rejects unvalidated work and a forged `PASSED` state.
- **RG-6:** `final_integration='merge_to_base'` leaves base HEAD unchanged while approval is open; only approval permits landing. Source inspection also checks that the engine and worktree manager contain no `"push"` invocation literal.

## Commands

Commands run from the readiness-review worktree in PowerShell:

```powershell
$os = (Get-CimInstance Win32_OperatingSystem).Caption
$py = python --version 2>&1
python -m unittest tests.test_readiness_review -v
```

OS: Windows, PowerShell. The Windows caption query failed with `Access denied` (HRESULT `0x80041003`), so the exact edition/build was unavailable. Python: `Python 3.14.7`.

The test suite creates disposable Python and JavaScript Git repositories under the system temporary directory. Provider calls use the in-process synthetic adapter; no subscription or remote model is called.

## Results

| item | Python fixture | JavaScript fixture | observed | status PASS/GAP/FAIL |
|---|---|---|---|---|
| RG-1 | PASS | PASS | Material finding caused repair; run completed after second review. | PASS |
| RG-2 | PASS | PASS | Unstructured “looks good” review was malformed; run blocked without integration. | PASS |
| RG-3 | PASS | PASS | Critical unresolved finding opened `unresolved_review_findings` approval gate. | PASS |
| RG-4 | PASS | PASS | Self-reported `done` did not pass the failing command validator; run blocked. | PASS |
| RG-5 | PASS | PASS | Unvalidated work opened a restricted-action gate; forged pass was rejected as `FAILED_FINAL`. | PASS |
| RG-6 | PASS | PASS | Base HEAD equaled recorded base commit while the consequential-write gate was open; approved decision completed and landed integration head on `main`. | PASS |
| Push source inspection | shared | shared | Neither `engine.py` nor `worktrees.py` contains the literal `"push"`. | PASS |

## Failures and gaps

- The OS caption command was blocked by WMI access restrictions. This did not affect the test run; record identifies Windows/PowerShell, but not its edition/build.
- No checklist behavior gaps were observed in this area.

## Raw output

```text
Get-CimInstance : Access denied
FullyQualifiedErrorId : HRESULT 0x80041003
Python: Python 3.14.7
test_cross_review_is_structured_and_material_findings_route_to_repair ... ok
test_engine_sources_never_invoke_git_push ... ok
test_integration_guard_refuses_a_forged_pass ... ok
test_integration_refuses_unvalidated_work ... ok
test_looks_good_is_not_a_review ... ok
test_merge_to_base_requires_approval_then_fast_forwards ... ok
test_self_reported_success_cannot_bypass_validators ... ok
test_unresolved_findings_after_max_rounds_require_approval ... ok

----------------------------------------------------------------------
Ran 8 tests in 21.601s

OK
```
