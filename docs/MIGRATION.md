# Migration from personal-agent-os

Origin: `unwit1/personal-agent-os@ce09ad2dbfc202fe54d1f4bb02753eb10037c257`.
Decision: `state/orchestrator/records/decisions/DEC-0045.json`. ADR and audit
live in personal-agent-os (`docs/adr/0001-orchestrator-os-extraction.md`,
`docs/audits/2026-10-orchestrator-baseline.md`).

## Commits after the import

| Commit | Change | Why |
|---|---|---|
| `642ed34`, `fa4c349` | mechanical copy + import rewrite | `extract.py` output, see `PROVENANCE.json` |
| `a8068f9`, `184178f` | affected-test selection and simplify find `src/` packages instead of `agent_os` | selection was a no-op on every other repository |
| `5ee2358`, `58485a7` | evidence moves to `state/`; suite runner paths re-pointed | records unchanged byte for byte |
| `78968ab` | control-plane floor and append-only guard use `host.OS_REL` | **security**: the copied literals left holdouts and FAIL/EVR records unprotected here |
| `ac68f10` | any repository with `policy/orchestrator-os.policy.json` is guarded | before, only the control repo was |
| `abcb710` | docs, status, checkpoint ORCH-0001, host-requirement skips | |
| `69ad9cf` | Harness² lab adapter, EXP-0013 | Option C of DEC-0045 |

## Run state

Nothing is converted. The run-state format is the same code. Agent OS keeps
its run store in place: the bridge sets
`AGENT_OS_ORCHESTRATOR_HOME=<personal-agent-os>/.agent-local/orchestrator`
unless you set it. Old runs stay listable, resumable and inspectable from
either backend.

To move a store later, stop all drivers first (`orchestrator list`; no run
in `RUNNING` with a live driver). Then copy the directory and point
`AGENT_OS_ORCHESTRATOR_HOME` at the copy. The source stays as the rollback.
Active worker processes are never adopted across machines or environments.

## Cutover checklist (Milestone H)

- [ ] `unwit1/orchestrator-os` exists (private) and CI passes on ubuntu and windows
- [ ] workstation: `pip install -e <orchestrator-os>` and `AGENT_OS_ORCHESTRATOR_BACKEND=external` for one week of normal use, with no regressions
- [ ] personal-agent-os CI runs this repository's suite with `ORCHESTRATOR_HOST=agent_os.orchestrator_host:HOST` (host-dependent tests stop skipping)
- [ ] port Agent OS tests that construct the internal engine (`test_orchestrator_surfaces`, `test_compute_provision_*`, `test_orchestrator_host_actions`) to the bridge
- [ ] `agent_os/validation.py` validates this repository's `state/` via `orchestrator_os.evidence`
- [ ] Agent OS imports `telemetry` and `capabilities` from `orchestrator_os` (no second copy)
- [ ] default backend flipped to `external`; one release later, delete `src/agent_os/orchestrator/`, its tests and the frozen copies under `projects/personal-agent-os/orchestrator-os/{evals,records,provider-policy}`

Rollback at any point before the deletion: set
`AGENT_OS_ORCHESTRATOR_BACKEND=internal`.
