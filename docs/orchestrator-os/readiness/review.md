# Review gates

## Checklist items

- **RG-1:** A structured reviewer verdict with material findings routes work to repair; repaired work is reviewed again.
- **RG-2:** An unstructured “looks good” response is rejected as malformed review output.
- **RG-3:** Findings left unresolved at `max_review_rounds` open an approval gate.
- **RG-4:** Self-reported success cannot bypass a failing validator.
- **RG-5:** Integration refuses unvalidated work and a forged `PASSED` state.
- **RG-6:** With `final_integration='merge_to_base'`, base HEAD remains unchanged while the approval gate is open; approval then permits fast-forward integration.
- Push source inspection searches every top-level `*.py` file in `src/agent_os/orchestrator`, excluding `repos.py`, for either single- or double-quoted `push` tokens. `repos.py` separately invokes `gh repo create` with the `--push` flag when creating a repository; that repository creation path is outside the run engine/worktree path checked here.

## Commands

Executed from the readiness-review worktree in PowerShell:

```powershell
$os = [System.Runtime.InteropServices.RuntimeInformation]::OSDescription
$py = python --version 2>&1
python -m unittest tests.test_readiness_review -v
```

OS: Microsoft Windows 10.0.26200. Python: Python 3.14.7.

Each checklist behavior runs against disposable Python and JavaScript fixture repositories in the system temporary directory. The orchestrator uses the in-process synthetic provider adapter; no remote model is called.

## Results

| item | Python fixture | JavaScript fixture | observed | status PASS/GAP/FAIL |
|---|---|---|---|---|
| RG-1 | PASS | PASS | Material finding routed to repair, received a fixed disposition, then passed a second review. | PASS |
| RG-2 | PASS | PASS | Unstructured “looks good” review was marked malformed; run blocked and work was not integrated. | PASS |
| RG-3 | PASS | PASS | Critical unresolved finding opened the `unresolved_review_findings` approval gate. | PASS |
| RG-4 | PASS | PASS | Self-reported `done` did not pass the failing command validator; run blocked. | PASS |
| RG-5 | PASS | PASS | Unvalidated work opened a restricted-action approval gate; forged pass was refused as `FAILED_FINAL`. | PASS |
| RG-6 | PASS | PASS | Base HEAD matched its pre-run commit while approval was open; after approval, `main` advanced to the integration head. | PASS |
| Push source inspection | shared | shared | No quoted `push` token was found in scanned Python sources; `repos.py` is excluded and its `gh ... --push` behavior is called out above. | PASS |

## Failures and gaps

- No behavior gaps were observed for RG-1 through RG-6 on either fixture.
- The source scan is a targeted token search, not a proof against dynamically assembled push arguments. It covers all top-level Python files in the orchestrator package and both quote styles. Repository creation can push through `repos.py` using the GitHub CLI `--push` flag, separate from the engine and worktree run path.

## Raw output

```text
OS: Microsoft Windows 10.0.26200 
Python: Python 3.14.7
test_cross_review_is_structured_and_material_findings_route_to_repair (tests.test_readiness_review.ReviewReadinessTests.test_cross_review_is_structured_and_material_findings_route_to_repair) ... ok
test_engine_sources_never_invoke_git_push (tests.test_readiness_review.ReviewReadinessTests.test_engine_sources_never_invoke_git_push) ... ok
test_integration_guard_refuses_a_forged_pass (tests.test_readiness_review.ReviewReadinessTests.test_integration_guard_refuses_a_forged_pass) ... ok
test_integration_refuses_unvalidated_work (tests.test_readiness_review.ReviewReadinessTests.test_integration_refuses_unvalidated_work) ... ok
test_looks_good_is_not_a_review (tests.test_readiness_review.ReviewReadinessTests.test_looks_good_is_not_a_review) ... ok
test_merge_to_base_requires_approval_then_fast_forwards (tests.test_readiness_review.ReviewReadinessTests.test_merge_to_base_requires_approval_then_fast_forwards) ... ok
test_self_reported_success_cannot_bypass_validators (tests.test_readiness_review.ReviewReadinessTests.test_self_reported_success_cannot_bypass_validators) ... ok
test_unresolved_findings_after_max_rounds_require_approval (tests.test_readiness_review.ReviewReadinessTests.test_unresolved_findings_after_max_rounds_require_approval) ... ok

----------------------------------------------------------------------
Ran 8 tests in 27.659s

OK
```
