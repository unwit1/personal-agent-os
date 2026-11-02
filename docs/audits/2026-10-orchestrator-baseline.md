# Orchestrator baseline audit (Milestone A)

Run on 2026-11-02 in a Claude Code cloud container. File name follows the
operator's request (`2026-10-…`); the measurements are from November.

## Environment and source state

| Item | Value |
|---|---|
| Repository | `unwit1/personal-agent-os`, branch `main` |
| HEAD audited | `ce09ad2dbfc202fe54d1f4bb02753eb10037c257` (2026-10-20, "Add HeroBloks minifigure controls…") |
| Working tree | clean at start; audit work on `claude/orchestrator-os-extraction` |
| Platform | Linux 6.18, Python 3.13.18, Node 22.23.4, Git 2.43 |
| Sibling dependency | `unwit1/ingester-engine@88e8110` (required, see finding A1) |
| Not available | the operator's Windows workstation, its `.agent-local` run history, `~/.agent-os` config, provider credentials, RTEC data |
| Last Orchestrator checkpoint | `ORCH-0116` (`status.json` updated 2026-10-02) |
| Superseded next action | "wire `free_routing.decide` into engine dispatch, then SkyPilot/RunPod, vLLM, TensorZero…". This migration replaces it; the free-routing work is preserved as backlog item S9. |

## Reproduce

```bash
git clone https://github.com/unwit1/personal-agent-os && cd personal-agent-os
git fetch --depth=3000 origin main      # eval tests resolve historical commits (f8f4453f)
python -m venv .venv && .venv/bin/pip install -e . -e ../ingester-engine pytest
.venv/bin/python -m unittest discover -s tests
python migrations/orchestrator-os-extraction/inventory.py docs/audits/orchestrator-component-inventory.json
```

## Test baseline

| Run | Tests | Failures | Errors | Skipped | Wall |
|---|---|---|---|---|---|
| Without Ingester Engine installed | 367 collected | 6 | 299 | 0 | 2 s |
| With Ingester Engine, shallow clone | 3337 | 10 | 3 | 3 | 239 s |
| With Ingester Engine, history depth 3000 | 3337 | 10 | 0 | 3 | ~240 s |

All 10 remaining failures are environment-coupled. None is an Orchestrator defect:

| Test | Class | Cause |
|---|---|---|
| `test_agent_os.test_project_inventory_is_fully_registered`, `test_portability.InventoryTests.test_alternate_checkout…` | environment | scan the real home directory; this container has unrelated checkouts in `/home/user` |
| `test_portability.test_every_project_resolves_to_a_local_path`, `…LauncherTests.test_discovery_prefers…`, `…SkillDiscoveryTests…`, `test_agent_os.test_skill_discovery…`, `test_agent_os.test_routing_targets…` | environment | need sibling checkouts (`hr-gui`, scanner) at registered paths |
| `test_surfaces.test_declared_locations_resolve…` | Windows-only | `${APPDATA}` is unset on Linux |
| `test_surfaces.test_claude_code_reports_as_a_reachable_routed_surface` | environment | no Agent OS MCP registration on this machine |
| `test_readiness_validators.test_vd4_node_test_command…` | stale test expectation | sets `NODE_OPTIONS=--test-isolation=none`, which Node 22.23 rejects inside `NODE_OPTIONS` |

The three errors on a shallow clone are `test_orchestrator_eval` cases that
resolve commit `f8f4453f`. They pass once history is fetched.

**Historical comparison.** The September 30 self-audit's "12 failures, 11
errors" did not reproduce. The `status.json` known baseline ("656 tests; 9
failures + 3 errors on f8f4453f") is the same pattern: machine-coupled tests
plus shallow history. Both are labelled historical. The new baseline above
supersedes them.

## Findings

Severity: **H** = safety or correctness, **M** = blocks portability or
multi-repo use, **L** = cleanliness.

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| A1 | M | Every `agent_os` import, including the whole Orchestrator, hard-fails without the Ingester Engine: `agent_os/__init__.py` calls `ensure_ingester_engine()`. | 299 import errors in the first run |
| A2 | H | The control-plane floor and negative-evidence guard are repo-relative literals (`src/agent_os/orchestrator/control_plane.py`, `projects/personal-agent-os/orchestrator-os/records/`). Moved code or a different target layout silently loses protection. The copied tests caught it during extraction. | `control_plane.py:33-39,101`; fixed in orchestrator-os `78968ab` |
| A3 | H | Protected paths apply only to the state root or the hard-coded project id `personal-agent-os`. Any other repository the Orchestrator edits gets no control-plane guard. | `control_plane.applies_to`; generalised in orchestrator-os `ac68f10` |
| A4 | M | Affected-test selection and the simplification engine only recognise modules named `agent_os.*`. On any other repository they select nothing and fall back to the full suite. | `test_selection.py:26-60`; fixed in orchestrator-os `a8068f9` |
| A5 | H | Cost safety. `failure_learning` defaults to `fix`, which auto-launches fix runs (≤ $5 each, 3/day) against the control repository. The provider registry also adopts any coding CLI found on `PATH` when no registry file exists. Together, one mis-wired test cost **$0.77** of real model spend in this session (details below). | policy `failure_learning.policy_keys`; `engine._launch_fix_run` |
| A6 | M | `_launch_fix_run` and `capture_improvement` hard-code `project="personal-agent-os"`. | `engine.py:2795,3590` |
| A7 | L | Self-referential corpora live inside the engine: `foreman_eval.py` task goals name `src/agent_os/orchestrator/*`, and `eval.py` prompts reference Agent OS paths. They are data, not engine code. | `foreman_eval.py:52-136` |
| A8 | L | Run branches and commit messages are prefixed `agent-os/…` even for unrelated repositories. | engine branch naming |
| A9 | L | `test_readiness_validators` vd4 depends on Node ≥ 23 `NODE_OPTIONS` semantics. | above |

### A5 incident record (unapproved spend)

While testing the bridge in external mode, four Agent OS surface tests injected
their synthetic engine into the *internal* `service` module. The CLI and MCP
then built a default engine from the external package. That engine found
`/opt/node22/bin/claude` (installed in this container) and ran real workers.
One worker returned malformed output. Failure learning filed IMP-0027 and
started a fix run against the new `orchestrator-os` checkout.

- 9 runs, all on throwaway fixture repos except the fix run. Reported cost $0.7668: two "plan and build" runs at $0.176 and $0.186, the fix run at $0.292, and six single-worker runs at $0.016–0.023.
- `orchestrator-os` `main` was not modified. The fix run left four branches and worktrees. Its diff (+9 lines in `failure_learning.py` and a test) was saved for review, then the branches were deleted.
- IMP-0027 and its index entry were reverted: it describes a fixture-induced failure, not a product defect.
- Prevention added: the bridge contract test (`tests/test_orchestrator_bridge.py`) uses an explicit synthetic registry, removes coding-agent CLIs from `PATH` and sets `failure_learning=off`. Full-suite runs in this session also ran without `claude` on `PATH`.
- Accidental datapoint, n=2, not a benchmark: on a trivial fixture, planner + implementer + reviewer cost ~8× one explicit worker ($0.18 vs $0.02).

## Coupling map

Inbound: what Agent OS imports from the Orchestrator. Five sites:
`cli.py` (register/dispatch), `mcp_server.py` (tool schemas and methods),
`executive/window/providers_orchestrator.py` and `actions_items.py`
(`service`, `simple.gate_card/failure_card`), and `validation.py`
(`evidence.validate_tree`).

Outbound: what the Orchestrator imports from Agent OS. 13 modules:

| Kind | Modules | Lines | Treatment in extraction |
|---|---|---|---|
| Leaf utilities | `timestamps`, `storage`, `fingerprints`, `local_paths`, `telemetry`, `capabilities` | 990 | vendored |
| Paths | `paths.ROOT` (18 sites), `machine.CONFIG_DIR` | — | `orchestrator_os.host` state root and config dir |
| Agent OS business logic | `registry`, `machine.resolve_path`, `compiler`, `improvements`, `coordination`, `economy` | ~12 call sites | `orchestrator_os.host` hooks, served by `agent_os.orchestrator_host` |

The GUI split is clean. `gui/index.html`, `app.js`, `simple*.js` and
`style.css` are served only by `orchestrator/server.py`. `executive.html` and
`executive.js` are served by `executive/window/server.py`; `style.css` is shared.

## Size and complexity

97 modules, 27,786 lines (radon 6.0.1; average cyclomatic complexity B, 7.6).
The largest functions are `cli.dispatch` (CC 242, one if-chain over about 60
actions), `Orchestrator._launch` (81), `server.Api.post` (79),
`ledger.describe` (70) and `Orchestrator._fail` (49). Over the last 60 days,
322 commits touched the Orchestrator; `engine.py` changed in 71 of them and
`cli.py` in 60.

Statically unreachable from every entry point (CLI, MCP, server, simple,
evidence), confirmed by string search across code, JSON, docs and scripts:
`free_metrics`, `foreman_optimize`, `openrouter_account` and
`shared_prefix_compare` (783 lines). `orchestrator/artifacts.py` is
unreachable but needs investigation, because its name collides with workflow
artifacts. `adapters/win_sandbox/*` is loaded dynamically via `PYTHONPATH`;
keep it.

The full per-module table, with recommendation, evidence and confidence for
each module, is in [`orchestrator-component-inventory.json`](orchestrator-component-inventory.json).
The ranked backlog is in [`2026-11-orchestrator-simplification-backlog.md`](2026-11-orchestrator-simplification-backlog.md).

## A representative run

A synthetic `start-recommended` run on a one-file fixture launched three
workers (planner, implementer, reviewer). It emitted 20 events across 12
kinds and wrote a 19.7 KB `state.json`. For a trivial change, two of the
three launches are orchestration overhead. That supports backlog item S2 (a
direct route).

## Uncertainty

- No Windows run. Process handling, `win_sandbox` and path behaviour are unverified here; CI for orchestrator-os includes `windows-latest`.
- No live provider measurements, beyond the accidental A5 datapoints. Phase Two comparisons (direct vs orchestrated vs simplified) need approved spend.
- Vulture reported 29 unused functions or methods at 60% confidence. They are not listed as deletions: dynamic CLI and MCP dispatch makes that tool unreliable here.
