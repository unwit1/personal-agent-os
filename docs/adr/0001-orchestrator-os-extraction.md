# ADR 0001: Extract the Orchestrator into `orchestrator-os`

Status: **accepted for Milestones C–D**. Cutover (H) needs operator sign-off.
Date: 2026-11-02. Evidence: [baseline audit](../audits/2026-10-orchestrator-baseline.md).

## Decision

1. The Orchestrator becomes the package `orchestrator_os` in its own
   repository, `unwit1/orchestrator-os`. Its CLI is `orchestrator`; the same
   actions and exit codes are kept, and a leading `orchestrate` still parses.
2. Exactly one module, `orchestrator_os.host`, stands where Agent OS used to
   be. It owns the state root, the machine config dir and optional project
   services: projects, context packet, handoff, improvement capture, work
   claims. Standalone, `StandaloneHost` serves them from an optional
   `orchestrator-projects.json`. Agent OS serves them from
   `agent_os.orchestrator_host:HOST`.
3. The dependency runs one way: `Agent OS → orchestrator_os`. The
   Orchestrator never imports Agent OS. A subprocess test in orchestrator-os
   asserts that.
4. Agent OS chooses an engine in one place, `agent_os.orchestrator_bridge`:
   `AGENT_OS_ORCHESTRATOR_BACKEND=internal|external`. CLI, MCP and the
   Executive window all read from it. The default stays `internal` until
   cutover. There is no second engine and no per-surface fork.
5. Durable Orchestrator evidence moves with the code under `state/`:
   evals, typed records, provider policy, prior-art registry, improvement
   backlog. Runtime state stays outside Git.
   - Checkpoints `ORCH-0001…0116`, `status.json` and `next-prompt.md` stay in Agent OS. They interleave Agent OS feature work (mail, applicants), so they are Agent OS session history.
   - `EVS-CONTEXT` and `EVS-RESUME` measure Agent OS features and stay there too.
6. Existing runs need no format migration. The code is identical, and the
   bridge keeps the old run store (`<agent-os>/.agent-local/orchestrator`)
   unless `AGENT_OS_ORCHESTRATOR_HOME` says otherwise.
7. Provenance is a copy plus a recorded mapping, not a history rewrite.
   `PROVENANCE.json` maps every file to its origin path at
   `personal-agent-os@ce09ad2`. `migrations/orchestrator-os-extraction/extract.py`
   reproduces the initial import. A path-filtered history split was rejected
   for three reasons:
   - the code moves together with six vendored utilities and data from four directories;
   - the session clone holds 3,000 of 8,120 commits;
   - published history must not be rewritten.

## Challenging the premise

| Question | Finding | Verdict |
|---|---|---|
| Is a separate repo worth the overhead? | The inbound surface is 5 import sites. Outbound is 990 lines of leaf utilities plus ~12 business-logic call sites. The Ingester Engine set the same precedent. Standalone already runs on a foreign repository with `agent_os` absent. | Yes. The cost was one seam module, one bridge and about 40 lines of fixes. |
| Should the Orchestrator keep its own copies of `telemetry` and `capabilities`? | They are run telemetry and the capability ladder: Orchestrator concepts that Agent OS workflows also use. | Keep them in `orchestrator_os`. After cutover Agent OS imports them from there (backlog S11). |
| Does more orchestration help? | On trivial tasks, `start-recommended` launches planner, implementer and reviewer. In the only live datapoint (n=2, accidental) that cost about 8× a single explicit worker. | Add a direct route for small tasks (S2) before adding features. |
| Should Harness² replace evaluation? | No. It is an offline optimiser with model-picked selection and no score in the loop. The Orchestrator already has incumbent-vs-candidate evals with protected suites. | Optional offline lab only (see below). |
| Durable workflow engines (Temporal, DBOS)? | Runs are a JSON state machine with checkpoints and resume. Nothing in the baseline shows a crash-recovery failure the store cannot handle. | Reject for now. Revisit only if recovery tests fail. |
| Mature SDKs (OpenHands SDK, Pydantic AI)? | Not evaluated against the code in this pass. The adapter layer (`adapters/*`, ~1,500 lines) is the only plausible replacement target. | Defer to S12, with a measured spike. |
| Should the GUI be shared? | Orchestrator GUI assets are self-contained and served by the Orchestrator's own server. | Orchestrator serves its GUI. Agent OS embeds data through the bridge and does not copy UI. |

## Harness²

Implementation review of `google-research/harness2@6868817` (Apache-2.0,
Python 3.12–3.13, no core dependencies, not on PyPI):

- **How it works.** Propose–Probe–Compose (`core/recursion.py`) uses 4k rollouts and 3k model sessions per task, with k reference runs shared across modes. INV and DOM proposals differ only in prompt. Every candidate is really executed. Behavioural comparison is left to the next proposer, not scored. Final selection is a blind model pick (`core/selection.py`). Lessons are stored as `EXPERIENCE.md` entries in a library.
- **Extension seam.** A `BenchmarkAdapter` protocol (12 methods) plus a `Proposer` whose `call()` can be overridden. A custom executor and scorer need no fork.
- **Security.** Its own executors run `claude --dangerously-skip-permissions` and `codex --dangerously-bypass-approvals-and-sandbox`, with no network restriction (README:168, EXPERIMENTS:100-108). We must never use them.
- **Verified run.** The deterministic demo ran with no network namespace (`unshare -rn`) and no model: exit 0, 28 executions, a 4k/3k ledger, `EXPERIENCE.md` written.

Decision: **Option C, an optional external adapter**, with B as fallback.
`orchestrator_os` gets an optional `harness2` extra, pinned to a commit. The
adapter implements `BenchmarkAdapter` with `execute()` routed through
Orchestrator runs on the synthetic provider or other approved providers. The
proposer is a `Proposer` subclass over our provider layer. Harness² executors,
its `claude` channel and its third-party runners are never used.

- **Placement.** Offline only, as an improvement lab on explicitly requested sessions. Never in a production run's path.
- **Cost.** The overhead is 4k rollouts per optimised task. For k=2 that is 8 rollouts and 6 proposer sessions per experiment.
- **Break-even.** An accepted change must save more than (8 × mean rollout cost + 6 × mean session cost) across the runs it affects before its next revision.
- **First target.** Worker context construction (`prompts._context_packet`). It is deterministic, cheap, and already measured by `context_anatomy` and `EVS-CONTEXT`.

Optimisation never becomes policy self-modification:

- candidate trees may touch only prompt and context files;
- control-plane paths, eval suites, holdouts and the policy stay protected (`control_plane.py`);
- promotion still goes through `orchestrator eval` incumbent-vs-candidate on protected suites, with the existing promotion rules.

## Consequences

- Agent OS keeps working unchanged with the default backend. Its suite is the regression gate for that.
- Until cutover the Orchestrator code exists twice: `src/agent_os/orchestrator` (frozen) and `orchestrator-os` (authoritative for new work). Cutover deletes the Agent OS copy after the checklist in `migrations/orchestrator-os-extraction/README.md`.
- Environment variable names (`AGENT_OS_PROVIDERS`, `AGENT_OS_ORCHESTRATOR_HOME`, …) and the keyring service name `agent-os` are kept for compatibility. Renaming is backlog item S10.

## Rollback

Unset `AGENT_OS_ORCHESTRATOR_BACKEND`, or set it to `internal`. Nothing in
Agent OS was removed, and run state was not converted.
