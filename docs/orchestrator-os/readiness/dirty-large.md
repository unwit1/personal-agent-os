# Dirty and large repositories

## Checklist items

- **DL-1:** With an unstaged tracked README edit and untracked `notes.txt`, verify preflight reports a dirty worktree and note, complete a run, preserve exact base checkout bytes, and confirm the integration branch excludes `notes.txt`.
- **DL-2:** Stage a README modification without committing, then record whether `create_run` proceeds or refuses.
- **DL-3:** Add and commit 1,200 small `.txt` files in `bulk/` and a 300,000-byte `big/blob.txt`; time `repomap.build`, check output length and excluded names, and record map stats.
- **DL-4:** Complete a one-task run on the large fixture and record elapsed time.

## Commands

OS: Windows 11 (`Windows-11-10.0.26200-SP0`); Python 3.14.7.

Exact validation command:

```powershell
python -m unittest tests.test_readiness_dirty_large -v
```

The test creates disposable Python and JavaScript Git repositories with `tempfile` under the system temporary directory. The run path uses an embedded `Orchestrator(RunStore(<temp>/home), registry=ProviderRegistry(providers=[synthetic ...]))`; no machine orchestrator or external model is used. The focused command completed successfully in 9.451 seconds.

## Results

| item | Python fixture | JavaScript fixture | observed (include timings) | status PASS/GAP/FAIL |
|---|---|---|---|---|
| DL-1 | Completed; README bytes remained identical; `notes.txt` remained intact in base and absent from integration branch | Same | Assertions passed for both; worker branch derived from `git ls-tree -r --name-only <branch>` | PASS |
| DL-2 | `create_run` proceeded, `dirty_worktree=True` | Same | Staged changes are detected as dirty and do not block creation | PASS |
| DL-3 | Large Python fixture built | N/A; one shared large fixture is used | `repomap.build`: 0.049 s; 348 chars (<= 6,200); stats: 1,206 tracked files, `data_dirs=['bulk']`, 1,200 excluded data files, 4 candidates scored/listed, 0 related. No `bulk/` file name or `blob.txt` appeared. | PASS |
| DL-4 | One-task large fixture run reached `COMPLETE` | N/A; large fixture is Python | 3.365 s elapsed | PASS |

## Failures and limitations

- The first test attempt expected 1,207 tracked paths; actual total was 1,206 (five initial Python fixture files plus 1,201 added files). The assertion was corrected to the observed total.
- The first run driving attempt stopped at `READY`; adding `run_loop` drove it through the review gate to `COMPLETE`.
- One intermediate staged-change observation incorrectly loaded the run from a different temporary `RunStore`, producing an unknown-run `KeyError`. The harness now retains the same engine for creation and inspection; the final result is `proceeded; dirty_worktree=True` for both fixtures.
- DL-3/DL-4 are exercised on the Python fixture only; these checks concern one large repository layout and are not duplicated for JavaScript. Timing is machine-specific.
