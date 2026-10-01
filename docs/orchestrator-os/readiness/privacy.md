# Readiness evidence: secret and privacy boundaries

Scope: PR-1 through PR-6 against the disposable Python and JavaScript repositories created by `tests/readiness_fixtures.py` in the system temporary directory. All orchestrator calls use in-process synthetic providers and a temporary `RunStore` home. No credentials, external models, or real project repositories are used.

## Commands

Fixture setup is run by `ReadinessFixture.setUp`: it creates `py-fixture` and `js-fixture` with Git, installs synthetic scripts, and places telemetry and run state under a `tempfile.mkdtemp(prefix='agent-os-readiness-')` directory. Tests invoke `git` using `git -c user.name=fixture -c user.email=f@x`.

Requested validator command (final corrected run):

```text
python -m unittest tests.test_readiness_privacy -v
```

Exact final command output:

```text
test_gap_redact_misses_generic_sk_token (tests.test_readiness_privacy.ReadinessPrivacyTests.test_gap_redact_misses_generic_sk_token) ... ok
test_pr1_run_state_refuses_transcripts_and_redacts_secrets (tests.test_readiness_privacy.ReadinessPrivacyTests.test_pr1_run_state_refuses_transcripts_and_redacts_secrets) ... ok
test_pr2_state_and_telemetry_hold_no_prompt_text (tests.test_readiness_privacy.ReadinessPrivacyTests.test_pr2_state_and_telemetry_hold_no_prompt_text) ... ok
test_pr3_repo_map_secret_file_visibility (tests.test_readiness_privacy.ReadinessPrivacyTests.test_pr3_repo_map_secret_file_visibility) ... ok
test_pr4_repo_map_excludes_bulk_data_directory_contents (tests.test_readiness_privacy.ReadinessPrivacyTests.test_pr4_repo_map_excludes_bulk_data_directory_contents) ... ok
test_pr5_agent_local_does_not_leak_into_status_or_integration_branch (tests.test_readiness_privacy.ReadinessPrivacyTests.test_pr5_agent_local_does_not_leak_into_status_or_integration_branch) ... ok
test_pr6_store_rejects_canonical_repository_location (tests.test_readiness_privacy.ReadinessPrivacyTests.test_pr6_store_rejects_canonical_repository_location) ... ok

----------------------------------------------------------------------
Ran 7 tests in 11.885s

OK
```

Result: 7 test methods passed, 0 failures/errors. Fixture subtests ran for both Python and JavaScript where applicable. PR-1/PR-2 were rerun with the corrected assertions; PR-3 through PR-6 also passed in this final run.

## Results

| Check | Python fixture | JavaScript fixture | Evidence / outcome |
|---|---|---|---|
| PR-1 transcript refusal and secret redaction | Passed; generic-token gap | Passed; generic-token gap | Final run confirms transcript refusal and redaction of `sk-ant-abcdefghijklmnopqrstuvwxyz0123` and `password=hunter2` in persisted state. Named test `test_gap_redact_misses_generic_sk_token` confirms `redact("sk-test-123456")` currently returns that value unchanged on both fixtures. |
| PR-2 state and telemetry exclude prompt text | Passed | Passed | Final run found no `Rules:`, `agent-os-result`, or transcript/messages/conversation/history keys in state. Telemetry omitted the unique prompt marker and every event's keys were a subset of the allowed metadata fields. |
| PR-3 map handles `.env` and secrets file | Passed | Passed | Committed `.env` with `API_KEY=sk-test-123456` and `config/secrets.json`; `build(repo, 'add a feature using the api key config')` text did not contain the secret value. Test records whether `.env` is listed; no exclusion is required by this assertion. |
| PR-4 map omits bulk data filenames | Passed | Passed | Committed 70 `data/rows/rowNN.csv` files. `stats.data_dirs` included `data` or `data/rows`; no `rowNN.csv` appeared in map text. |
| PR-5 `.agent-local` leakage with shared history | Passed | Passed | Ran synthetic orchestration with `share_run_history=True`; asserted an integration branch exists, then inspected `git status --porcelain --untracked-files=all` and `git ls-tree -r --name-only <integration branch>`. Neither listed an `.agent-local` path. |
| PR-6 canonical repository state rejected as store home | Passed | Passed | `RunStore(<checkout>/projects/orchestrator-state)` raised `StoreError`. |

### Stage 3 prompt

> Define an explicit Orchestrator OS readiness checklist for developing other repositories. Cover worktree isolation and rollback; secret and privacy boundaries, including the repo map and data directories; validator detection for non-Python repositories; behavior when a repository has no Agent OS project registration; cost and usage caps; review gates; and dirty or large repositories. Create two small throwaway fixture repositories outside any real repository, one Python and one JavaScript. Test each checklist item against both fixtures where applicable, record the exact commands, observed results, and failures, and stop with a checkpoint, evidence, and the exact Stage 3 prompt. Use only subscription and local models, preserve the budget, approval, publication-guard, and privacy gates, and do not touch other real repositories or push to main.
