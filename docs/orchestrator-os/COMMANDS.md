# Orchestrator OS command reference

The top-level `agent-os app` command opens the Command Center, embedding the
control GUI alongside Today, Projects, Chat and Usage. Flags: `--no-window`,
`--port PORT`, and repeatable `--remote-host HOST`. Both servers stay on loopback;
remote hosts allow exact Host headers from a private proxy, not remote binding.

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
| `orchestrate secrets` | provider-neutral secret references `secrets://<provider>/<profile>`: `setup` (masked pop-ups for every known credential), `set [--gui]`, `status`, `delete`; OS keyring or env; values never printed |
| `orchestrate model-add` | register an OpenAI-compatible endpoint (open-weight or abliterated model) in the machine-local registry; preview unless `--write` (see [model-infrastructure.md](../model-infrastructure.md)) |
| `orchestrate services` | model service catalog ([model-services.md](../model-services.md)): `list [--category] [--status]`, `show <id>`, `validate` (exit 1 on errors), `discover <id> [--endpoint]` (read-only GET of a documented model list, cached locally), `add <id> --model <id> [--classes] [--endpoint] [--plan] [--provider-id] [--roles] [--cost] [--max-concurrency] [--ack-terms] [--write]` (preview unless --write), `bridge <id> [--plan] [--model-map sonnet=...] [--roles] [--cost] [--ack-terms] [--write]` (Claude Code bridge for an eligible coding plan) |
| `orchestrate refusals` | refusal/non-answer telemetry by provider, model and refusal profile (no model call) |
| `orchestrate cloud` | Claude Code cloud sessions: `submit` a task from a clean, trusted, non-sensitive repository (spends a promotional cloud credit before plan limits; runs `claude --cloud` in a pseudo-console), `send` a follow-up, `list`, `check` (docs/command-center.md) |
| `orchestrate extras` | one-time plan extras (cloud credit, saved usage resets): `list`, or `set <id> <status>` after redeeming in the vendor UI; never redeems |
| `orchestrate headroom` | plan allowance left per subscription provider (Codex session logs, Claude rate-limit event, NanoGPT usage API) and its routing effect: exhausted skipped, tight cost x3, expiring cost x0.6; `--refresh` rereads now (docs/model-services.md) |
| `orchestrate learn` | `[run_id ...] [--all] [--summary]`. Failure learning: record run failures as signatures, file improvements and start capped fix runs (policy `failure_learning`); with no run, the 30-day signature summary |
| `orchestrate quote` | no-spend quote for a workload: API vs GPU pod vs serverless, low/expected/high, budget gate and routing requirements (no model call, no provisioning) |
| `orchestrate radar` | Model Research Radar: scan the Hugging Face Hub (text, vision, image, ASR, TTS, ...) into a local catalog with license/revision/size and queue eval candidates (no model call, no weight downloads) |
| `orchestrate eval-queue` † | evaluate queued catalog models once served: `plan` (deterministic) explains readiness; `run` calls `orchestrate eval` per suggested suite (bounded real calls) and records the outcome with an attribution check |
| `orchestrate throughput` † | serving-throughput evidence per model x GPU x engine: `measure` benchmarks your own OpenAI-compatible endpoint (real calls), `record`/`show` store and list; quotes use it via `quote --model` |
| `orchestrate budget` | operator compute budget: `show`, or `set --project-usd --job-cap-usd` (operator action; history kept); quotes gate on it |
| `orchestrate api-budget` | operator API-delegation budget (Anthropic/OpenAI per-token spend; separate from host-plan usage and the compute budget): `show`, or `set --total-usd --call-cap-usd` |
| `orchestrate compute` | GPU inventory (read-only; RunPod first; cached 6 h) and gated compute provisioning. Sub-actions: `inventory` (`--provider`, `--refresh`, `--min-vram`); `provision` (budget gate + approval, write-ahead reservation, `--provider` required + only `fake` launches today, `--gpu`, `--hourly-usd`, `--low-usd`/`--expected-usd`/`--high-usd`, `--job-id` for resume, `--max-runtime-seconds` auto-stop, `--secret-ref secrets://...`); `status`, `stop`, `destroy`, `reconcile` (by `--job-id`, `--actual-usd` optional, idempotent); `jobs` (list). Guarantees: budget gate on high estimate, write-ahead reservation, mandatory auto-stop from cap, idempotent by job_id, secrets:// refs only. Only --provider fake launches today (operator approval needed for real, IMP-0015 slice 3). MCP tools: compute.provision/status/stop/destroy/reconcile. |
| `orchestrate foreman-shadow` † | shadow foreman: a candidate model proposes a DAG + classes for a run (`propose`, one real call); `compare`/`report` score proposals against actual outcomes deterministically |
| `orchestrate foreman` † | session foreman: `preview`/`deploy` a Hugging Face model on a RunPod GPU within the job budget and use it as the planner for new runs; `status`/`stop`; `eval` scores its per-task model choices and efficiency (real calls); `use claude|chatgpt|openrouter|local|registered` (no rental; `use registered --provider <id> [--model <id>]` makes an eligible registered provider the foreman) |
| `orchestrate context-anatomy` | IMP-0018 Phase 0: tokens per prompt section, fan-out duplication and context amplification for a finished run's saved prompts (no model call) |
| `orchestrate context-economy` | IMP-0018 Phase 0: token amplification, context growth, fan-out and resume overhead across run telemetry (aggregates only, no model call) |
| `orchestrate context-bench` | P2.3 synthetic prompt/context measurement over compiler, skill-selection, prompt, handoff and optional telemetry fixtures (no model call) |
| `orchestrate rotation-advisor` | IMP-0019 shadow: would-rotate advice per worker from run telemetry (aggregates only, advice only, no model call) |
| `orchestrate route-calibration` | IMP-0015 shadow: RouteLLM-style escalation calibration per task family and capability class from run telemetry (aggregates only, advice only, no model call) |
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

† may spend model calls or usage. Unmarked commands do not make model calls;
some read live service data or write local configuration, as described above.
