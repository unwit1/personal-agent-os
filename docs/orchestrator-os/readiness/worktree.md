# Worktree isolation and rollback

## Checklist items

- WT-1: Concurrent disjoint tasks receive distinct worktree paths and branches, outside the fixture's tracked tree and distinct from the base repository.
- WT-2: An edit outside a task's declared scope fails validation and does not change the base fixture.
- WT-3: A run whose only task fails validation leaves base HEAD at `base_commit` and the base repository clean.
- WT-4: `final_integration='branch'` completes on an integration branch while leaving base HEAD unchanged and keeping the task output on that branch.
- WT-5: A conflicting `WorktreeManager` merge is aborted, preserves the integration head, and leaves integration status clean.

## Commands

- Exact validator command: `python -m unittest tests.test_readiness_worktree -v`
- OS: Microsoft Windows 10.0.26200 (PowerShell `$PSVersionTable` / .NET `RuntimeInformation.OSDescription`). The initial `Get-CimInstance Win32_OperatingSystem` query was denied by the host; fallback OS identification succeeded.
- Python: `Python 3.14.7`
- Fixtures were created by `readiness_fixtures.ReadinessFixture` under the system temporary directory for each test case. All provider calls used the in-process synthetic adapter.

## Results

| item | Python fixture | JavaScript fixture | observed | status |
|---|---|---|---|---|
| WT-1 | Pass | Pass | Distinct worktree paths and branches; each worktree is outside the fixture repository. | PASS |
| WT-2 | Pass | Pass | Out-of-scope README edit is rejected; run is BLOCKED and base README remains unchanged. | PASS |
| WT-3 | Pass | Pass | Failing validator blocks the run; base HEAD equals recorded `base_commit` and porcelain status is empty. | PASS |
| WT-4 | Pass | Pass | Run completes on integration branch; base HEAD is unchanged and task output exists on the integration branch. | PASS |
| WT-5 | Pass | Pass | Second README merge reports conflict, does not advance integration head, and leaves integration status clean. | PASS |

## Failures and gaps

No worktree checklist failures or behavior gaps were observed. The first OS metadata query was denied, then the OS was identified successfully through PowerShell/.NET metadata; this did not affect the test run.

## Raw output

```text
----------------------------------------------------------------------
Ran 5 tests in 13.624s

OK
```
