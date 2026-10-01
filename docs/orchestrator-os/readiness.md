# Orchestrator OS readiness for other repositories: Stage 2 checkpoint

## Scope and method

This checkpoint synthesizes the seven [readiness evidence files](readiness/) and the [fixture helper](../../tests/readiness_fixtures.py). The Python and JavaScript Git fixtures are created under the system temporary directory, outside any real repository, and are never registered as Agent OS projects. Tests use an embedded `Orchestrator` with a temporary `RunStore` and synthetic providers only; no paid, API, or external model is called. Results describe these fixtures and this Windows test environment, not a general deployment guarantee. No other real repository was touched or pushed to main.

## Readiness checklist

“Pass” in a fixture column means the evidence test passed; the status column identifies observed product gaps. N/A means the check was not run for that fixture.

| item | requirement | Python | JavaScript | status | evidence link |
|---|---|---|---|---|---|
| WT-1 | Give concurrent tasks distinct external worktrees and branches. | Pass | Pass | PASS | [Worktree](readiness/worktree.md) |
| WT-2 | Reject edits outside declared scope without changing base. | Pass | Pass | PASS | [Worktree](readiness/worktree.md) |
| WT-3 | Leave base HEAD and status intact after failed validation. | Pass | Pass | PASS | [Worktree](readiness/worktree.md) |
| WT-4 | Integrate on a branch without advancing base HEAD. | Pass | Pass | PASS | [Worktree](readiness/worktree.md) |
| WT-5 | Abort a conflicting merge and preserve clean integration state. | Pass | Pass | PASS | [Worktree](readiness/worktree.md) |
| PR-1 | Refuse transcript persistence and redact secrets in state. | Pass; generic `sk-` token gap | Pass; generic `sk-` token gap | GAP | [Privacy](readiness/privacy.md) |
| PR-2 | Exclude prompt text from run state and telemetry. | Pass | Pass | PASS | [Privacy](readiness/privacy.md) |
| PR-3 | Keep `.env` path and secret values out of the repo map. | Pass | Pass | PASS | [Privacy](readiness/privacy.md) |
| PR-4 | Omit bulk `data/` filenames from the repo map. | Pass | Pass | PASS | [Privacy](readiness/privacy.md) |
| PR-5 | Keep shared run history out of fixture status and integration. | Leakage observed | Leakage observed | GAP | [Privacy](readiness/privacy.md) |
| PR-6 | Reject a canonical repository path as RunStore home. | Pass | Pass | PASS | [Privacy](readiness/privacy.md) |
| VD-1 | Infer suitable validators for unregistered repositories. | Empty defaults | Empty defaults; no npm discovery | GAP | [Validators](readiness/validators.md) |
| VD-2 | Return no project commands without registration. | N/A | `[]` | PASS | [Validators](readiness/validators.md) |
| VD-3 | Run an explicit JavaScript fixture validator in its worktree. | N/A | Pass | PASS | [Validators](readiness/validators.md) |
| VD-4 | Run `node --test` as an explicit validator. | N/A | Pass with Windows isolation workaround | PASS | [Validators](readiness/validators.md) |
| VD-5 | Reject a failing JavaScript validator. | N/A | Pass | PASS | [Validators](readiness/validators.md) |
| NR-1 | Record null project and the unregistered Git root. | Pass | Pass | PASS | [Unregistered](readiness/unregistered.md) |
| NR-2 | Reject an unknown explicit project identifier. | `KeyError` captured | `KeyError` captured | PASS | [Unregistered](readiness/unregistered.md) |
| NR-3 | Resolve a nested path to its fixture Git root. | Pass | Pass | PASS | [Unregistered](readiness/unregistered.md) |
| NR-4 | Reject a path outside Git. | Pass | Pass | PASS | [Unregistered](readiness/unregistered.md) |
| NR-5 | Complete an explicit task without changing Agent OS `projects` status. | Pass | Pass | PASS | [Unregistered](readiness/unregistered.md) |
| NR-6 | Record initial approval gates for unregistered runs. | Empty gates | Empty gates | PASS; policy decision | [Unregistered](readiness/unregistered.md) |
| CC-1 | Stop at a launch budget approval gate. | Pass | Pass | PASS | [Cost](readiness/cost.md) |
| CC-2 | Record documented usage-total fields. | Pass | Pass | PASS | [Cost](readiness/cost.md) |
| CC-3 | Bound all-provider quota exhaustion. | Pass | Pass | PASS | [Cost](readiness/cost.md) |
| CC-4 | Bound validator retries, escalation, and provider errors. | Pass | Pass | PASS | [Cost](readiness/cost.md) |
| CC-5 | Enforce a token or money cap. | N/A | N/A | GAP | [Cost](readiness/cost.md) |
| CC-6 | Use synthetic adapters for fixture runs. | Pass | Pass | PASS | [Cost](readiness/cost.md) |
| RG-1 | Repair material review findings and review again. | Pass | Pass | PASS | [Review](readiness/review.md) |
| RG-2 | Reject malformed reviewer approval. | Pass | Pass | PASS | [Review](readiness/review.md) |
| RG-3 | Gate unresolved findings at the review-round limit. | Pass | Pass | PASS | [Review](readiness/review.md) |
| RG-4 | Prevent self-reported success from bypassing validation. | Pass | Pass | PASS | [Review](readiness/review.md) |
| RG-5 | Refuse unvalidated work and forged pass state. | Pass | Pass | PASS | [Review](readiness/review.md) |
| RG-6 | Gate merge to base and advance only after approval. | Pass | Pass | PASS | [Review](readiness/review.md) |
| DL-1 | Preserve dirty base bytes and exclude untracked files from integration. | Pass | Pass | PASS | [Dirty and large](readiness/dirty-large.md) |
| DL-2 | Detect staged changes as dirty when creating a run. | Pass; creation proceeds | Pass; creation proceeds | PASS | [Dirty and large](readiness/dirty-large.md) |
| DL-3 | Bound repo-map output with 1,200 data files and a large blob. | Pass; 0.042 s, 348 chars | N/A | PASS; Python only | [Dirty and large](readiness/dirty-large.md) |
| DL-4 | Complete a task on the large fixture. | Pass; 3.119 s | N/A | PASS; Python only | [Dirty and large](readiness/dirty-large.md) |

## Exact commands

Each area reports a final focused validator run with this exact command:

```text
python -m unittest tests.test_readiness_worktree -v
python -m unittest tests.test_readiness_privacy -v
python -m unittest tests.test_readiness_validators -v
python -m unittest tests.test_readiness_unregistered -v
python -m unittest tests.test_readiness_cost -v
python -m unittest tests.test_readiness_review -v
python -m unittest tests.test_readiness_dirty_large -v
```

The [worktree](readiness/worktree.md), [privacy](readiness/privacy.md), [validators](readiness/validators.md), [unregistered](readiness/unregistered.md), [cost](readiness/cost.md), [review](readiness/review.md), and [dirty and large](readiness/dirty-large.md) files record setup, observed results, and any additional inspection commands.

## Failures and gaps

- **PR-1:** Transcript refusal and tested secret patterns passed, but `redact("sk-test-123456")` returns that generic token unchanged on both fixtures ([privacy](readiness/privacy.md)).
- **PR-5:** With `share_run_history=True` and no fixture `.gitignore`, `.agent-local` entries appear in fixture `git status` and the integration branch on both fixtures ([privacy](readiness/privacy.md)).
- **VD-1:** Unregistered Python and JavaScript runs have empty default and node validator lists; JavaScript does not infer npm tests. Explicit commands work. Node's default child-process test isolation initially failed with `spawn EPERM` in this Windows worker; `NODE_OPTIONS=--test-isolation=none` let `node --test` pass ([validators](readiness/validators.md)).
- **CC-5:** An unknown `max_usd` policy key is rejected. Defaults have `max_launches` but no token or money cap; usage totals are accounting only ([cost](readiness/cost.md)).
- **NR-6:** Unregistered run creation records no initial approval gate. This is observed behavior, not a failing assertion; whether explicit consent should be required is a policy decision ([unregistered](readiness/unregistered.md)).
- **DL-3/DL-4:** Large-repository map and run checks used only the Python fixture. Their timings are machine-specific ([dirty and large](readiness/dirty-large.md)).
- **RG source inspection:** The targeted scan found no quoted `push` token in the checked run-engine Python files; it does not prove that dynamically assembled push arguments are impossible. `repos.py` has a separate `gh repo create --push` path outside that run path ([review](readiness/review.md)).

Earlier test-harness failures were corrected before the final focused runs: the worktree was removed before the first VD-3 assertion, the JavaScript CC-4 synthetic state leaked between subtests, DL-3 expected 1,207 rather than 1,206 tracked paths, DL-4 initially stopped at `READY`, and a DL-2 inspection used another temporary store. The [evidence files](readiness/) preserve those observations. All seven final focused commands passed; passing gap tests confirm the reported gaps rather than resolving them.

## Verdict

| Area | Verdict | Basis |
|---|---|---|
| Worktree isolation and rollback | **ready** | All five behaviors passed on both fixtures. |
| Secret and privacy boundaries | **not ready** | Generic token redaction and shared-history `.agent-local` leakage remain. |
| Validator detection | **ready with conditions** | Explicit validators pass; unregistered JavaScript repositories get no inferred test command. |
| Unregistered repositories | **ready with conditions** | Runs work, but initial consent policy needs a decision. |
| Cost and usage caps | **ready with conditions** | Launch and retry bounds work; token or money caps are absent. |
| Review gates | **ready** | All six gate behaviors passed; push evidence is a targeted source scan. |
| Dirty and large repositories | **ready with conditions** | Dirty checks passed on both; large checks covered Python only. |

Overall, **not ready for unrestricted development of other repositories** while the observed privacy leakage remains. Explicit validators, a bounded launch budget, and existing review and approval gates support a narrower supervised use once privacy is addressed.

## Decisions needed from the user

- Should unregistered JavaScript repositories infer `npm test` from `package.json`, and under which opt-in flag or project policy?
- What per-run token or money cap should supplement `max_launches`, and what approval behavior should apply at the cap?
- Should unregistered repositories require an explicit approval gate before work begins?
- Should the repo map and shared-history path categorically exclude secret-file paths and `.agent-local` from prompts and integration, even when those paths are tracked or the fixture lacks `.gitignore`? The tested `.env` map case passed, while `.agent-local` leakage was observed.

## Checkpoint and exact next prompt

Stage 2 established isolation, rollback, explicit validation, unregistered-run, review, dirty-tree, and bounded-launch behavior on disposable fixtures. It also established privacy leakage, absent automatic JavaScript validation, and absent token or money caps. The seven evidence files and [fixture helper](../../tests/readiness_fixtures.py) are the checkpoint; no gate was relaxed.

> **Stage 3 prompt:** In this repository only, fix the highest-priority observed readiness gaps with bounded, opt-in behavior and targeted tests: prevent `.agent-local` shared run history from entering fixture status, worker prompts when inappropriate, or integration branches; cover generic `sk-` token redaction and repo-map secret-file exclusion; add optional non-Python validator detection from `package.json`; and add an optional per-run token or money cap with an approval gate while retaining `max_launches`. Specify the opt-in defaults and require an explicit policy choice before changing unregistered-repository approval behavior. Re-run all seven `python -m unittest tests.test_readiness_* -v` readiness modules against the same temporary Python and JavaScript fixture patterns, plus deterministic project validation. Record exact commands, results, regressions, and remaining gaps. Preserve budget, approval, publication-guard, and privacy gates; use only subscription and local models, do not touch other real repositories, and do not push to main.
