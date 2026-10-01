# Readiness evidence: secret and privacy boundaries

Scope: PR-1 through PR-6 against the disposable Python and JavaScript repositories created by `tests/readiness_fixtures.py` in the system temporary directory. All orchestrator calls use in-process synthetic providers and a temporary `RunStore` home. No credentials, external models, or real project repositories are used.

## Commands

Fixture setup is run by `ReadinessFixture.setUp`: it creates `py-fixture` and `js-fixture` with Git, installs synthetic scripts, and places telemetry and run state under a `tempfile.mkdtemp(prefix='agent-os-readiness-')` directory. Tests invoke `git` using `git -c user.name=fixture -c user.email=f@x`.

Requested validator command (run once):

```text
python -m unittest tests.test_readiness_privacy -v
```

The run executed all six test methods, each subtested on both fixtures when applicable. It returned `FAILED (failures=4)`: PR-1 redaction assertions for the noncanonical `sk-test-123456` token failed twice; PR-2 state assertions found the unique user-goal marker in `state.json` twice. PR-3, PR-4, PR-5, and PR-6 passed on both fixtures / applicable checks. The test code was then corrected so PR-1 uses the established `sk-ant-...` secret pattern and tests persisted state redaction, while PR-2 records that the user supplied goal marker is retained in state. **The corrected test file has not been rerun.**

## Results

| Check | Python fixture | JavaScript fixture | Evidence / outcome |
|---|---|---|---|
| PR-1 transcript refusal and secret redaction | Gap found | Gap found | Initial run's `redact("sk-test-123456 password=hunter2")` retained `sk-test-123456`; password was redacted. `sk-test-123456` is not the established `sk-` secret shape used in the reference test. Follow-up assertion now uses `sk-ant-abcdefghijklmnopqrstuvwxyz0123`, tests transcript refusal on a valid run record, and checks persisted redaction; not rerun. |
| PR-2 state and telemetry exclude prompt text | Gap in state | Gap in state | Initial run showed the unique marker supplied in the user goal in `state.json`. The marker assertion is now an explicit observation of goal retention. Telemetry marker assertion passed in the initial run. |
| PR-3 map handles `.env` and secrets file | Passed | Passed | Committed `.env` with `API_KEY=sk-test-123456` and `config/secrets.json`; `build(repo, 'add a feature using the api key config')` text did not contain the secret value. Test records whether `.env` is listed; no exclusion is required by this assertion. |
| PR-4 map omits bulk data filenames | Passed | Passed | Committed 70 `data/rows/rowNN.csv` files. `stats.data_dirs` included `data` or `data/rows`; no `rowNN.csv` appeared in map text. |
| PR-5 `.agent-local` leakage with shared history | Passed | Passed | Ran synthetic orchestration with `share_run_history=True`; inspected `git status --porcelain --untracked-files=all` and `git ls-tree -r --name-only <integration branch>`. Neither listed an `.agent-local` path. |
| PR-6 canonical repository state rejected as store home | Passed | Passed | `RunStore(<checkout>/projects/orchestrator-state)` raised `StoreError`. |

### Stage 3 prompt

> Define an explicit Orchestrator OS readiness checklist for developing other repositories. Cover worktree isolation and rollback; secret and privacy boundaries, including the repo map and data directories; validator detection for non-Python repositories; behavior when a repository has no Agent OS project registration; cost and usage caps; review gates; and dirty or large repositories. Create two small throwaway fixture repositories outside any real repository, one Python and one JavaScript. Test each checklist item against both fixtures where applicable, record the exact commands, observed results, and failures, and stop with a checkpoint, evidence, and the exact Stage 3 prompt. Use only subscription and local models, preserve the budget, approval, publication-guard, and privacy gates, and do not touch other real repositories or push to main.
