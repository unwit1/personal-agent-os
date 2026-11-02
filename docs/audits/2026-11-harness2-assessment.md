# Harness² assessment

Source reviewed: `google-research/harness2@6868817518876de8fd170c6a8354daca273b6191`,
read at implementation level. The decision is in
[ADR 0001](../adr/0001-orchestrator-os-extraction.md#harness).

## Facts (verified in code)

| Topic | Finding | Where |
|---|---|---|
| License, runtime | Apache-2.0; Python `>=3.12,<3.14`; core `dependencies = []`; extras `render`, `bridge` (litellm 1.95.0, fastapi 0.139.2, google-auth 2.56.3) | `pyproject.toml:10-24` |
| Distribution | Git checkout plus `uv pip install -e`; no PyPI release seen | `README.md:87-89` |
| Reference runs | `run_task` runs the unmodified harness k times (`base1..k`), shared by both modes | `core/schedule.py:473-520,619-734` |
| Propose | `_run_stage` builds an evidence folder (task, rollouts, deliverables, current harness, library). The proposer edits `context/harness/` in place. The tree is validated, with one retry | `core/recursion.py:114-262`, `core/context.py:105` |
| INV vs DOM | Same machinery, different prompt (procedure and tools vs domain knowledge) | `core/prompts.py:348,372,824-835` |
| Probe | Every candidate harness is executed | `core/recursion.py:271-351` |
| Compare | No numeric diff. Trajectories and deliverables go to the next proposer's `pool/` | `core/recursion.py` |
| Compose | Parallel: 2k candidates, then k aggregations. Sequential: k rounds of INV+DOM, then compose. Both use 4k rollouts and 3k sessions (asserted) | `core/recursion.py:354-577`, `core/ledger.py:26-34` |
| Select | A blind, anonymised model pick among k finals. **Scores are never used in the loop** | `core/selection.py:268-357` |
| Lessons | `<experience>` cue/lesson/evidence/confidence entries go to `library/<mode>/<domain>/harnesses/<task>/EXPERIENCE.md`; `INDEX.md` rebuilt; no leakage from future tasks | `core/selection.py:402-505`, `core/library.py:106-152` |
| Editable surface (OpenCode) | `systemprompt.md`, `guardrails.md`, `LongTermMEMORY.md`, `tool_descriptions/tool_guidance.md`, `skills/*/SKILL.md`(+scripts), `sub_agents/*/AGENT.md`, `scripts/*.py`, `plugin/*.ts` | `substrate/opencode.py:42-70` |
| Editable surface (Codex) | `AGENTS.md` (8k cap), `.agents/skills/…`, `.codex/hooks.json` | `substrate/codex.py:39-70` |
| Extension seam | `BenchmarkAdapter` protocol (12 required methods), plus a `Proposer` subclass overriding `call()`. Python API `run_task` / `run_domain`. The CLI is hard-wired to its own benchmarks | `core/spec.py:200-250`, `cli/demo.py:39-48`, `cli/_common.py:30` |
| Security | `claude --dangerously-skip-permissions`, `codex --dangerously-bypass-approvals-and-sandbox --dangerously-bypass-hook-trust`; network unrestricted; only an OpenCode `external_directory` deny rule and env scrubbing | `core/proposer.py:205-207,261`, `substrate/codex.py:166-167`, `README.md:168`, `docs/EXPERIMENTS.md:100-108` |

## Deterministic demo (run)

Run in a copied tree, with no network namespace and no model:

```bash
unshare -rn env -i PATH=/usr/bin:/bin HOME=$PWD <venv>/bin/python -I -c \
  "import sys; sys.path.insert(0,'<copy>'); from harness2.cli.demo import main; raise SystemExit(main(['--output','<out>','--k','2']))"
```

Result: exit 0, "2 tasks completed; 0 failed". `demo.json` reported
`execution_count: 28` and `editor_calls: 32`. The ledger for each mode was
R=8, P=6 (4k/3k at k=2). The library `EXPERIENCE.md` files were written.

## Mapping to the Orchestrator

| Harness² component | Orchestrator counterpart |
|---|---|
| system prompt / guardrails | `prompts.py` role prompts and the output contract |
| memory | `prompts._context_packet` via `host.compile_context` |
| tool guidance | worker tool rules in adapters (`claude_code.py` disallowed tools) |
| sub_agents | planner, reviewer and repairer roles in `engine.py` |
| skills / scripts | Agent OS skills (host) and validator commands |
| scorer (post-hoc only) | `eval.py` suites (incumbent vs candidate), with protected holdouts |

## Assessment

- Harness² adds a *proposal generator* that the Orchestrator lacks. Its selection step is weaker than ours: a model's blind pick, with no score. So Harness² proposes, and `orchestrator eval` decides. Promotion rules do not change.
- Cost per optimised task is 4k rollouts plus 3k sessions. At k=2 that is 8 Orchestrator runs and 6 proposer calls per experiment. That is affordable only offline and on a cheap, deterministic target.
- Integration is Option C: an optional, commit-pinned extra with one `BenchmarkAdapter` (about 150–250 lines) and one `Proposer` subclass (about 60–100 lines). Option B (re-implement) is estimated at 500–700 lines plus prompts, which is not justified while the seam works without a fork.
- Python 3.12+ only, so the extra cannot be a core dependency (we support 3.11).

## Status and first experiment

Done:

- research and assessment;
- the isolated demo run;
- the Option C adapter: `orchestrator-os` `src/orchestrator_os/lab_harness2.py`, commit `69ad9cf`, test `tests/test_lab_harness2.py`;
- the first experiment (EXP-0013, report in `docs/lab/harness2-context-k2.json` there).

The experiment ran `run_domain(mode=agg, k=2)` over 3 dev tasks inside
`unshare -rn`. Proposals came from a scripted proposer; scoring used the
Orchestrator's deterministic scorer. Result: 3/3 tasks done, 24 executions,
24 proposer calls, **0 model calls**.

| Variant (worker context packet) | Dev recall | Dev tokens | Held-out recall | Held-out tokens |
|---|---|---|---|---|
| existing rule (`prompts._context_packet`) | 0.694 | 188.0 | 1.0 | 188.0 |
| shortened summary | 0.694 | 153.0 | 1.0 | 153.0 |
| task-specific constraints | 1.0 | 117.7 | 1.0 | 116.5 |
| Harness²-composed (INV+DOM via PPC) | 1.0 | 82.7 | 1.0 | 81.5 |

What this shows:

- The integration works end to end through the seams. Nothing was forked.
- The incumbent's 8-item cap drops required constraints once a project lists more than 8. That is a cheap, deterministic candidate fix.

What it does not show:

- That Harness² finds improvements. I scripted the proposals and wrote the fixture.
- That task success improves. Recall of named constraints is only a proxy.

The outcome is recorded as **inconclusive**. The next step needs approved
spend: a model proposer, with candidates scored by `orchestrator eval` on the
EVS suites.
