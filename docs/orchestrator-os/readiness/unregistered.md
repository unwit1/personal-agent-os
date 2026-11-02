# Repositories without Agent OS registration

## Checklist items

- **NR-1:** Creating a run with an unregistered Git repository and no project argument records `project: null` and the fixture's Git root as `repository` in both the summary and stored record.
- **NR-2:** Supplying a nonexistent project identifier raises an exception; capture its concrete type and message.
- **NR-3:** Supplying a directory inside the fixture resolves to the containing fixture Git root.
- **NR-4:** A directory outside any Git repository raises `OrchestratorError` containing `not inside a Git repository`.
- **NR-5:** An explicit-task run against each unregistered fixture reaches `COMPLETE`; the before and after `git status --porcelain projects` snapshots in Agent OS `ROOT` are identical.
- **NR-6:** Creating an unregistered run does not itself open an approval gate (`record['gates'] == []`).

## Commands

Executed from the worktree root on Windows 11 (PowerShell 5.1.26100.9444), Python 3.14.7:

```powershell
python -m unittest tests.test_readiness_unregistered -v
```

The test creates both Git fixtures beneath `tempfile.mkdtemp()` (system temporary directory), uses embedded `Orchestrator`/`RunStore` instances and synthetic `alpha`/`beta` providers, and removes the temporary tree via unittest cleanup. The test also runs `git status --porcelain projects` before and after against `agent_os.paths.ROOT` and asserts equality.

## Results

| item | Python fixture | JavaScript fixture | observed | status PASS/GAP/FAIL |
|---|---|---|---|---|
| NR-1 | PASS | PASS | Both summary and record have `project` set to `None`; record repository resolves to respective fixture root. | PASS |
| NR-2 | `KeyError: 'Unknown project: no-such-project-readiness'` | `KeyError: 'Unknown project: no-such-project-readiness'` | Unknown explicit project identifier fails; type and message captured in the test. | PASS |
| NR-3 | PASS (`calc/` resolves to Python root) | PASS (`src/` resolves to JavaScript root) | Nested repository arguments normalize to the fixture Git root. | PASS |
| NR-4 | PASS | PASS | Both attempts from a temporary non-Git directory raise `OrchestratorError` containing `not inside a Git repository`. | PASS |
| NR-5 | PASS | PASS | Explicit-task run reaches `COMPLETE` on both fixtures; `projects` status snapshot remains unchanged. | PASS |
| NR-6 | PASS | PASS | Both initial run records have an empty `gates` list. | PASS |

## Failures and gaps

No remaining failures or gaps. During development, early attempts exposed that `start()` alone leaves the run at `READY`, and the synthetic editor writes under its task ID scope. The successful case calls `run_loop()` with scope `impl`. Synthetic runs verify orchestration behavior without paid or network model calls.

## Raw output

Successful command output:

```text
test_unregistered_repository_behavior (tests.test_readiness_unregistered.UnregisteredRepositoryTests.test_unregistered_repository_behavior) ... ok

----------------------------------------------------------------------
Ran 1 test in 5.245s

OK
```
