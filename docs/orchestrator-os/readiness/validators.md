# Validator detection for non-Python repositories

## Checklist items

- **VD-1 — Defaults on unregistered fixtures:** Create a planning-only single-node run for each disposable Python and JavaScript repository without declaring validators. Record run policy defaults and the node validator list. Expected and observed: both are empty. The JavaScript result is a detection gap: no npm test command is inferred.
- **VD-2 — Missing project registration:** `_project_commands(None)` returns `[]`.
- **VD-3 — Explicit JavaScript validator:** An explicit Python command reads the JavaScript fixture's `package.json` and succeeds when its `scripts` includes `test`. The command writes its current directory to a temporary evidence file; the test confirms this equals the node's worker worktree path. The run completes.
- **VD-4 — Node test command:** When `node` is installed, run the JavaScript fixture task with `['node', '--test']`; assert the run completes and validation passes. This Windows worker denies Node's default child-process test isolation with `EPERM`, so the test sets `NODE_OPTIONS=--test-isolation=none` during the run. The validator argv remains exactly `node --test`.
- **VD-5 — Failing JavaScript validator:** An explicit JavaScript-fixture validator exits 1; validation fails and the node does not pass.

Search of `src/agent_os` found no `package.json` or npm test discovery. The `npm` matches found are publication guards in `orchestrator/control_plane.py`; `validation_commands` is loaded as the source of project defaults in `orchestrator/engine.py` (`_project_validators`). Other `pyproject.toml` references are unrelated to validator detection.

## Commands

Environment: Microsoft Windows 10.0.26200; Python 3.14.7; Node.js v24.19.0.

Exact source search command:

```powershell
rg -n "package\.json|npm|pyproject|validation_commands" src/agent_os
```

Exact requested test command:

```powershell
python -m unittest tests.test_readiness_validators -v
```

Node version command:

```powershell
node --version
```

Observed output: `v24.19.0`.

## Results

| item | Python fixture | JavaScript fixture | Result |
|---|---|---|---|
| VD-1 | `policy.default_validators=[]`; single node `validators=[]` | `policy.default_validators=[]`; single node `validators=[]` | Pass; JS automatic npm test discovery is a gap |
| VD-2 | Not applicable | `_project_commands(None) == []` | Pass |
| VD-3 | Not applicable | Explicit `package.json` test-script validator passes; captured cwd equals worker worktree path; run `COMPLETE` | Pass |
| VD-4 | Not applicable | `node --test` passes with `NODE_OPTIONS=--test-isolation=none`; run `COMPLETE` | Pass with Windows worker isolation workaround |
| VD-5 | Not applicable | Exit-1 validator yields failed validation and `FAILED_FINAL` node | Pass |

The first VD-3 attempt failed because it checked for `package.json` after run completion, when the orchestrator had removed the worktree. The check now records and compares the validator's cwd while the worktree is active. The first VD-4 attempt failed with Node `spawn EPERM` under default test isolation; disabling test isolation through `NODE_OPTIONS` let Node run its test in-process.

Final test result: all five tests passed (`Ran 5 tests in 8.057s`, `OK`).
