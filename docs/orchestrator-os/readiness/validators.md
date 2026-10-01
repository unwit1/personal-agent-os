# Validator detection for non-Python repositories

## Checklist items

- **VD-1** — Create a `planning='single'` run for each unregistered fixture with no explicit validators. Observed run policy defaults and single-node validators are `[]` for both Python and JavaScript. This is a recorded JavaScript gap: no npm test detection.
- **VD-2** — `_project_commands(None)` returns `[]`.
- **VD-3** — An explicit Python command validator that reads `package.json` passes on the JavaScript fixture. The orchestrator invokes validators with the worker worktree as cwd; the test also confirms that `package.json` exists there and that the path differs from the base fixture.
- **VD-4** — Run `node --test` on the JavaScript fixture when Node is installed. Node was installed, but its test runner failed with `EPERM` while spawning a child process, so the run did not complete. This is an environment failure against the expected completion.
- **VD-5** — A JavaScript-fixture validator exiting 1 leaves the node `FAILED_FINAL` with validation `passed: false` (zero escalations).

## Commands

- Source detection search: `rg -n -e 'package\.json' -e '\bnpm\b' -e 'pyproject' -e 'validation_commands' src/agent_os`
- Test/validator command: `python -m unittest tests.test_readiness_validators -v`
- OS: Windows (PowerShell worker; version not captured by the run).
- Python: `Python 3.14.7` (`python --version`).
- Node: `v24.19.0` (`node --version`).
- Source search result: no `package.json` or npm test detection in `src/agent_os`; `npm` matches only publication guard patterns in `orchestrator/control_plane.py`. `validation_commands` is consumed by the compiler, validation, prompts, roadmap, and orchestrator; `engine.py` documents `_project_validators` as sourcing canonical project `validation_commands`.

## Results

| item | Python | JavaScript | Observed result |
|---|---|---|---|
| VD-1 | `default_validators=[]`; node validators `[]` | `default_validators=[]`; node validators `[]` | Pass; no language-based validator auto-detection, including npm test detection. |
| VD-2 | N/A | N/A | Pass; `_project_commands(None) == []`. |
| VD-3 | N/A | Explicit package.json validator | Initially blocked by the fixture editor writing outside the task scope (`impl/...` vs `src`); corrected scope is `impl`. Validator is run from the worker worktree by the engine. The one requested run preceded that scope correction, so successful completion after correction remains unverified. |
| VD-4 | N/A | `node --test` | Failed in the requested run: Node test runner reported `code: 'EPERM'`, `syscall: 'spawn'`. |
| VD-5 | N/A | Explicit exit-1 validator | Validation failed as expected; initial test assertion expected `FAILED`, while observed terminal node state is `FAILED_FINAL`. The assertion was corrected; the one requested run preceded that correction. |

The exact validator command above ran once and reported VD-1 and VD-2 passing, with VD-3, VD-4, and VD-5 test failures described in the table. Test scope/state assertions have since been aligned to observed engine behavior, but were not rerun under the one-run instruction. Consequently this evidence is not a clean passing validation record.
