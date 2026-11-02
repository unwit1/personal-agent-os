# Orchestrator simplification backlog

Ranked by expected benefit ÷ (effort × risk). Every item lands in
`orchestrator-os` as its own commit, gated by the full suite. Evidence comes
from the [baseline audit](2026-10-orchestrator-baseline.md) and
[`orchestrator-component-inventory.json`](orchestrator-component-inventory.json).
Line counts are at `personal-agent-os@ce09ad2`.

| # | Rec | Item | Evidence | Benefit | Risk | Effort | Conf |
|---|---|---|---|---|---|---|---|
| S1 | DELETE | `free_metrics`, `foreman_optimize`, `openrouter_account`, `shared_prefix_compare` (783 lines + 4 test files) | no importer from any entry point; string search across code, JSON, docs and scripts finds only their own tests and research notes; `shared_prefix_compare`'s result is already recorded in EVR-0021 | less code to read and maintain | low: dynamic dispatch was checked | S | medium |
| S2 | SIMPLIFY | Direct route: small tasks run one implementer plus deterministic validation, with no planner and no model review | a trivial synthetic run launches 3 workers; the accidental live datapoint (n=2) shows `start-recommended` at about 8× an explicit single worker | large cost cut on small tasks | quality on edge cases; gate on EVS suites, and keep model review for risk-flagged diffs | M | medium |
| S3 | SIMPLIFY | Default `failure_learning` from `fix` to `improve` (file the IMP, never auto-spend) | incident A5: an automatic fix run spent $0.29 unasked | removes surprise spend | slower self-repair; **operator decision**, since `policy/**` is protected | S | high |
| S4 | SIMPLIFY | Make `cli.dispatch` (CC 242, about 60 actions in one if-chain) table-driven | radon | 60 of 322 recent commits touched `cli.py`; fewer merge conflicts | low: `test_command_reference` pins the surface | M | high |
| S5 | SIMPLIFY | Registry auto-detection only on `providers --suggest --write`, never at engine start | A5: an unconfigured engine adopted `/opt/node22/bin/claude` | no implicit paid provider | first-run friction; the GUI shows a setup action | S | high |
| S6 | EXTRACT | GPU foreman stack into an optional extra (`orchestrator-os[foreman]`): `foreman*`, `provision`, `compute*`, `vllm_*`, `gpu_keep_busy`, `weight_cache` (≈3,900 lines) | operator-gated; inactive without a write-enabled RunPod key (`status.json` blocker) | the core package drops about 14% of its code | foreman users install the extra | M | medium |
| S7 | MERGE | One model-quality store. `capability` (CAP), `provider_health`, `model_value`, `route_calibration` and `rotation_advisor` each keep their own view of provider quality; the last two are shadow-only | inventory: 1 importer each for the shadow advisors | one data path into `router.select` | experiments in flight (IMP-0019); finish or close them first | L | medium |
| S8 | SIMPLIFY | `engine.py` (3,737 lines): split along the three real seams only (launch/dispatch, validation+review, integration). Do not split mechanically | `_launch` CC 81, `_fail` CC 49; 71 commits in 60 days | smaller conflict surface | high: the core state machine; needs differential tests first | L | low |
| S9 | DEFER | `free_routing.decide` wiring into dispatch (the superseded ORCH-0116 next action) | second routing authority beside `router.select` | n/a | n/a | M | n/a |
| S10 | SIMPLIFY | Rename `AGENT_OS_*` environment variables and `agent-os/…` run branches to `ORCHESTRATOR_*` / `orchestrator/…`, with the old names read as fallback for one release | A8 | clarity in other repos | breaks scripts if done without fallback | S | high |
| S11 | MERGE | Agent OS imports `telemetry` and `capabilities` from `orchestrator_os` after cutover | vendored copies (990 lines) | one implementation | Agent OS workflows depend on telemetry | S | high |
| S12 | INVESTIGATE | Can the OpenHands Software Agent SDK or Pydantic AI replace `adapters/*` (claude_code, codex_cli, http_api: ≈1,240 lines)? | not measured | possibly large | new dependency and runtime; requires a spike plus EVS comparison | M | low |
| S13 | KEEP | `retry.py` (132 lines), `store.py`, `ledger.py`, `control_plane.py`, `router.py` | small, central, well tested; a library would not delete meaningful code | — | — | — | high |
| S14 | INVESTIGATE | `orchestrator/artifacts.py`: no importer, but its name collides with workflow artifacts | inventory | — | — | S | low |

Not recommended: Temporal or DBOS for durable execution (no recovery failure
in evidence); a large permanent analysis-tool stack (radon and vulture were
run once from a scratch venv); splitting small modules for symmetry.
