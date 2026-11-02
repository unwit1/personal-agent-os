# Full test suite evidence

## Run

- Exact command: `python -m unittest discover -s tests`
- Python: 3.14.7 (`C:\Python314\python.exe`)
- Tests run: 985
- Result: 12 failures, 11 errors, 1 skipped
- Wall-clock duration: 355.827 seconds (5m 55.827s), measured around the command; `unittest` reported 353.372 seconds
- Exit code: 1
- The single skipped test has no ID in the `unittest` summary.

The table includes every failure and error in the captured run. Each probable-cause category is an estimate. Test IDs include the fully qualified unittest name; the two portability subtests are separate failing instances.

| Full test ID | Test file | Result | One-line exception/assertion message | Probable cause category (estimate) | Source file and function under test (if identifiable via grep) |
|---|---|---|---|---|---|
| `test_codex_win_sandbox.CodexWindowsTempdirShimTests.test_shim_changes_only_tempfile_mode_for_workers` | `tests/test_codex_win_sandbox.py` | ERROR | `subprocess.CalledProcessError`: child Python `sitecustomize` probe exited with status 1. | environment/Windows path (estimate) | `tests/test_codex_win_sandbox.py::test_shim_changes_only_tempfile_mode_for_workers`; child `sitecustomize` probe |
| `test_orchestrator_economy.BackgroundDriverTests.test_embedded_engine_never_spawns_a_detached_driver` | `tests/test_orchestrator_economy.py` | ERROR | `RuntimeError: orchestrator control is unavailable inside an isolated worker; report the host-side prerequisite to the parent controller` | environment (estimate) | `src/agent_os/orchestrator/service.py::_reject_worker_control`, called by `create` |
| `test_orchestrator_eval.RunnerTests.test_test_runner_uses_trusted_copy_in_a_detached_worktree` | `tests/test_orchestrator_eval.py` | ERROR | `EvalError`: `git worktree add` could not create the shared parent `.git/worktrees` entry (`Permission denied`). | environment/Windows path (estimate) | `src/agent_os/orchestrator/eval.py::Worktree.__enter__`, via `_git` |
| `test_orchestrator_surfaces.CliTests.test_headless_create_run_and_result` | `tests/test_orchestrator_surfaces.py` | ERROR | `RuntimeError: orchestrator control is unavailable inside an isolated worker; report the host-side prerequisite to the parent controller` | environment (estimate) | `src/agent_os/orchestrator/service.py::_reject_worker_control`, called by `create` |
| `test_orchestrator_surfaces.CliTests.test_headless_gate_approval_and_exit_codes` | `tests/test_orchestrator_surfaces.py` | ERROR | `RuntimeError: orchestrator control is unavailable inside an isolated worker; report the host-side prerequisite to the parent controller` | environment (estimate) | `src/agent_os/orchestrator/service.py::_reject_worker_control`, called by `create` |
| `test_orchestrator_surfaces.CliTests.test_invalid_policy_is_a_clean_error` | `tests/test_orchestrator_surfaces.py` | ERROR | `RuntimeError: orchestrator control is unavailable inside an isolated worker; report the host-side prerequisite to the parent controller` | environment (estimate) | `src/agent_os/orchestrator/service.py::_reject_worker_control`, called by `create` |
| `test_orchestrator_surfaces.CliTests.test_start_recommended_with_validator_flag` | `tests/test_orchestrator_surfaces.py` | ERROR | `RuntimeError: orchestrator control is unavailable inside an isolated worker; report the host-side prerequisite to the parent controller` | environment (estimate) | `src/agent_os/orchestrator/service.py::_reject_worker_control`, reached through `start_recommended` and `create` |
| `test_orchestrator_surfaces.HttpApiTests.test_gui_controls_pause_and_gate_decision` | `tests/test_orchestrator_surfaces.py` | ERROR | `KeyError: 'run_id'` | environment (estimate; worker-control error response was used where the test expected a run result) | `src/agent_os/orchestrator/service.py::create`, consumed by the HTTP API test |
| `test_recovery.StableIdentityTests.test_same_remote_has_the_same_project_identity_in_different_paths` | `tests/test_recovery.py` | ERROR | `subprocess.CalledProcessError`: `git push -qu origin master` exited with status 128. | environment (estimate; captured exception did not include the push stderr) | `src/agent_os/recovery.py::repository_identity` is the identity behavior this test exercises; setup failed during its Git push |
| `test_rtec_applicants.RTECApplicantAdapterTests.test_applicant_reads_fail_closed_before_agent_ref_migration` | `tests/test_rtec_applicants.py` | ERROR | `KeyError: 'agent_ref_schema_ready'` | stale expectation (estimate) | `src/agent_os/rtec_applicants.py::sync_status`, checked after `list_applicants` |
| `test_rtec_applicants.RTECApplicantAdapterTests.test_sync_status_contains_health_and_outbox_counts` | `tests/test_rtec_applicants.py` | ERROR | `KeyError: 'applicant_record_count'` | stale expectation (estimate) | `src/agent_os/rtec_applicants.py::sync_status` |
| `test_agent_os.AgentOSTests.test_project_inventory_is_fully_registered` | `tests/test_agent_os.py` | FAIL | `AssertionError`: `inventory["unregistered"]` contained `brickmen`, `iphone-message-archive`, and `job-applicant-dashboard`, not `[]`. | environment (estimate; this inventory depends on local checkout registration) | `src/agent_os/inventory.py::scan` |
| `test_agent_os.AgentOSTests.test_registered_project_resolves` | `tests/test_agent_os.py` | FAIL | `AssertionError: 9 != 7` | stale expectation (estimate; the current registry yields nine distinct IDs) | `src/agent_os/registry.py::projects`, also `get_project` and `identify_project` in the test |
| `test_agent_os.AgentOSTests.test_validation` | `tests/test_agent_os.py` | FAIL | `AssertionError`: validation reported `job-applicant-dashboard: missing context file: docs/AGENT_OS_INTEGRATION.md`. | environment (estimate; validation sees another local project checkout) | `src/agent_os/validation.py::validate` |
| `test_orchestrator_roadmap.GuiCoreTests.test_simple_core_under_node` | `tests/test_orchestrator_roadmap.py` | FAIL | `AssertionError: 1 != 0`; Node reported `Error: spawn EPERM` while running the GUI core test. | environment/Windows path (estimate) | `tests/gui/simple_core.test.js`, invoked by `tests/test_orchestrator_roadmap.py::test_simple_core_under_node` |
| `test_orchestrator_surfaces.HttpApiTests.test_gui_api_start_recommended_drives_real_engine_to_complete` | `tests/test_orchestrator_surfaces.py` | FAIL | `AssertionError: 400 != 200`; response reported orchestrator control unavailable inside an isolated worker. | environment (estimate) | `src/agent_os/orchestrator/service.py::_reject_worker_control`, reached through GUI API `start_recommended` |
| `test_orchestrator_surfaces.McpTests.test_mcp_drives_a_run_to_completion` | `tests/test_orchestrator_surfaces.py` | FAIL | `AssertionError: True is not false`; MCP response reported orchestrator control unavailable inside an isolated worker. | environment (estimate) | `src/agent_os/orchestrator/service.py::_reject_worker_control`, reached through MCP create |
| `test_portability.AdapterPortabilityTests.test_rendering_is_the_comparison_basis_for_installed_copies (destination='C:\\Users\\HR.RTEC\\.codex\\AGENTS.md')` | `tests/test_portability.py` | FAIL | `AssertionError: False is not true`; installed `AGENTS.md` differed from canonical rendering. | environment/Windows path (estimate; installed copy differs) | `src/agent_os/routing.py::status` and `render`, via `tests/test_portability.py::test_rendering_is_the_comparison_basis_for_installed_copies` |
| `test_portability.AdapterPortabilityTests.test_rendering_is_the_comparison_basis_for_installed_copies (destination='C:\\Users\\HR.RTEC\\.codex\\skills\\personal-agent-os\\SKILL.md')` | `tests/test_portability.py` | FAIL | `AssertionError: False is not true`; installed skill differed from canonical rendering. | environment/Windows path (estimate; installed copy differs) | `src/agent_os/routing.py::status` and `render`, via `tests/test_portability.py::test_rendering_is_the_comparison_basis_for_installed_copies` |
| `test_portability.InventoryTests.test_alternate_checkout_is_attributed_to_its_registered_project` | `tests/test_portability.py` | FAIL | `AssertionError`: inventory reported the same three unregistered paths: `brickmen`, `iphone-message-archive`, and `job-applicant-dashboard`. | environment (estimate; inventory depends on local checkout registration) | `src/agent_os/inventory.py::scan` |
| `test_rtec_applicants.RTECApplicantAdapterTests.test_runtime_readiness_degrades_before_opaque_ref_migration` | `tests/test_rtec_applicants.py` | FAIL | `AssertionError: False is not true` for `result["outbox_schema_ready"]`. | real bug (estimate; expected outbox schema readiness was false) | `src/agent_os/rtec_applicants.py::readiness` |
| `test_rtec_applicants.RTECApplicantAdapterTests.test_runtime_readiness_healthy_only_when_all_local_gates_pass` | `tests/test_rtec_applicants.py` | FAIL | `AssertionError: 'degraded' != 'healthy'` | real bug (estimate; fixture readiness did not meet the test's all-gates expectation) | `src/agent_os/rtec_applicants.py::readiness` |
| `test_surfaces.IntegrationHealthReportTests.test_claude_code_reports_as_a_reachable_routed_surface` | `tests/test_surfaces.py` | FAIL | `AssertionError: 'bridged' != 'routed'` | environment (estimate; integration health reported a lower tier for this machine) | `src/agent_os/surfaces.py::health` |

## Slowest test modules

The full suite took under 10 minutes, so each `tests.test_<module>` suite was run individually. Durations below are wall-clock seconds for each module invocation; the top ten are:

| Rank | Test module | Duration (seconds) |
|---:|---|---:|
| 1 | `tests.test_orchestrator` | 70.012 |
| 2 | `tests.test_orchestrator_roadmap` | 53.747 |
| 3 | `tests.test_foreman_deploy` | 49.326 |
| 4 | `tests.test_orchestrator_state_machine` | 45.215 |
| 5 | `tests.test_orchestrator_telemetry` | 21.981 |
| 6 | `tests.test_orchestrator_host_actions` | 14.584 |
| 7 | `tests.test_orchestrator_economy` | 10.243 |
| 8 | `tests.test_orchestrator_eval` | 9.173 |
| 9 | `tests.test_recovery` | 8.860 |
| 10 | `tests.test_orchestrator_test_selection` | 7.108 |

The individual timing pass covered all discovered `test_*.py` modules: total measured module runtime was 362.186 seconds. No tests or product code were changed.
