# Orchestrator OS command reference

Generated from `agent-os orchestrate --help`; kept complete by
`tests/test_command_reference.py`. Commands marked † may spend model
calls or usage; the rest are deterministic. The coding-run workflow
(create/start/run, gates, integration) is described in
[multi-agent-orchestrator.md](../multi-agent-orchestrator.md); the
Orchestrator OS self-improvement commands (delegate, eval, capability,
mutate, simplify, mining, trace, corpus, context-report, prior-art,
checkpoint) are described here and in [ENTRYPOINT.md](ENTRYPOINT.md).

| Command | Purpose |
|---|---|
| `orchestrate providers` | show configured providers and routing recommendations |
| `orchestrate create` | create a run |
| `orchestrate start-recommended` † | plan, start with Auto Continue, and drive until a stop state |
| `orchestrate status` | see --help |
| `orchestrate result` | see --help |
| `orchestrate step` | see --help |
| `orchestrate events` | see --help |
| `orchestrate pause` | see --help |
| `orchestrate resume` | see --help |
| `orchestrate stop` | see --help |
| `orchestrate list` | see --help |
| `orchestrate start` | see --help |
| `orchestrate run` † | drive a run in the foreground (Auto Continue: until a stop state) |
| `orchestrate approve` | see --help |
| `orchestrate reject` | see --help |
| `orchestrate retry` † | see --help |
| `orchestrate review-again` † | see --help |
| `orchestrate reassign` | see --help |
| `orchestrate override` | provider/model/effort override for the run, a role, or a node |
| `orchestrate roadmap` | show roadmap progress and the next eligible stage (no model call) |
| `orchestrate continue-roadmap` † | Continue Roadmap: resume unfinished work or start the next roadmap stage, then drive it |
| `orchestrate report` † | efficiency report for a run from its telemetry (tokens, calls, context, avoided work) |
| `orchestrate benchmark` | repeatable token-efficiency benchmark (offline by default; --live uses real providers) |
| `orchestrate usage-report` | cross-run token usage report from run telemetry (provider-reported numbers) |
| `orchestrate models` | model catalog: current tier models, new/outdated models, proposals (local + official online sources; no model call) |
| `orchestrate model-trial` † | try a model for a tier on a real small task (real calls; spends usage) |
| `orchestrate model-proposal` † | apply or dismiss a model proposal (apply writes the provider registry, with a backup) |
| `orchestrate planner-bench` † | measure planner token use and plan quality per prompt/tool variant (real calls; spends usage) |
| `orchestrate overhead` † | measure each coding CLI's fixed per-call context cost (real calls; spends usage) |
| `orchestrate delegate` † | one read-only task through the router with an output contract; records capability evidence (real call) |
| `orchestrate api-key` | store or check a provider API key in the OS keyring (never in files) |
| `orchestrate capability` | aggregate capability observations into CAP records (no model call) |
| `orchestrate checkpoint` | Orchestrator OS continuation checkpoint + next prompt (no model call) |
| `orchestrate next-prompt` | print the current generated next prompt |
| `orchestrate control-check` | check paths (or the working-tree diff) against the protected control plane |
| `orchestrate eval` † | incumbent vs candidate over an EVS suite; writes an EVR (test suites: git refs; case suites: routes) |
| `orchestrate context-report` | context-utility: attachment reference rates and always-unreferenced attachments (no model call) |
| `orchestrate corpus` | external attack-corpus registry: list, or import a corpus as data into .agent-local (no model call) |
| `orchestrate mining` | failure/success signature clusters and coverage gaps (no model call) |
| `orchestrate trace` | export a run's telemetry as OpenTelemetry OTLP/JSON spans (GenAI conventions; no content exported) |
| `orchestrate simplify` | simplification engine: component view + dead/duplicate/dependency/prior-art candidates (no model call; deletes nothing) |
| `orchestrate mutate` | mutation testing: mutate a module in throwaway worktrees and run the named tests (no model call) |
| `orchestrate prior-art` | open-source prior-art registry: lookup, discovery queries, staleness, metadata refresh (no model call) |
| `orchestrate eval-cases` | generate deterministic development cases for a task family (no model call) |
| `orchestrate gui` | serve the local control GUI and API |

† may spend model calls/usage; all others are deterministic (no model call).
