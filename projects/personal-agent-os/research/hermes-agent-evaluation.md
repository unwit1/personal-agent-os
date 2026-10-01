# Hermes Agent — what to subsume, and where it goes

Status: evaluation (no runtime adoption yet) · Evaluated 2026-10-01 · IMP-0020 · PA-hermes-agent

Source: [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) at
`bd394e2a` (2026-10-01), MIT; [hermes-agent-self-evolution](https://github.com/NousResearch/hermes-agent-self-evolution).
Read from a local shallow clone: `README.md`, `AGENTS.md`, `website/docs/{user-guide,developer-guide}`,
`hermes_cli/_parser.py`, `agent/memory_provider.py`, `mcp_serve.py`, `gateway/platforms/`.
Nothing was installed or run.

## What Hermes is

A personal agent (Python ≥3.11, native Windows supported) with one agent core behind a CLI,
a TUI, a desktop app and a messaging gateway (Telegram, Discord, Slack, WhatsApp, Signal,
Email, iMessage via BlueBubbles, Teams, Home Assistant, webhooks and more). It keeps bounded
memory and a skill library it writes itself, runs scheduled jobs, delegates to subagents,
and is extended through plugins, skills and MCP. It is large (≈8,000 Python files, ≈39k tests)
and changes daily; its own rules forbid compatibility shims for internal moves, so internal
APIs are not stable — only the documented plugin ABCs, the CLI and MCP are.

Two of its design invariants match Agent OS's economy rules and are worth adopting as rules
even where we take no code:

- **Per-conversation prompt caching is sacred**: never mutate past context, swap tools or
  rebuild the system prompt mid-conversation; state changes take effect next session.
- **The Footprint Ladder**: extend existing code → CLI command + skill → service-gated tool →
  plugin → MCP server → new core tool, in that order. Every tool schema costs tokens on
  every call, so new capability lands at the cheapest rung that works.

## The split

**Agent OS stays canonical** for durable state (projects, profile, memory candidates,
handoffs, policies, runs). Hermes, where adopted, is a *front door and runtime* that reads
and writes through Agent OS's MCP server and a memory-provider plugin — never a second
source of truth.

- **Orchestrator OS (execution of bounded work)** takes Hermes as an optional *worker* and
  borrows a few mechanisms. Its own engine (worktrees, validators, cross-review, gates,
  routing, telemetry) is stronger than Hermes' equivalents (`delegate_task`, Kanban) for
  verified code work and stays.
- **Executive function (P3–P8 of the master roadmap)** is mostly unbuilt in Agent OS and is
  where Hermes is already strong: messaging, scheduling, proactive turns, voice, bounded
  memory, self-maintained skills. Here Hermes should be *run*, not reimplemented.

Mode legend: **RUN** (use Hermes itself through a stable seam) · **PORT** (reimplement the
mechanism in Agent OS, MIT attribution) · **BORROW** (adopt the idea/rule only) · **SKIP**.

### Executive function

| Hermes capability (verified) | Mode | Agent OS item | Why / how |
|---|---|---|---|
| Messaging gateway, ~20 platforms incl. Email, Discord, Signal, iMessage (BlueBubbles); DM pairing + platform allowlists | **RUN** | EXEC-11.5, EXEC-7, EXEC-13; GUI chat | The communication front door Agent OS lacks. Lets the foreman/swarm chat (Run card → Chat) reach the phone. Sending stays approval-gated (Hermes command approval + Agent OS autonomy policy). |
| `hermes mcp serve` — conversations, history, send, live events, approvals as MCP tools | **RUN** | EXEC-11, Event Bus | Agent OS (or Claude/Codex) reads and replies to messages through MCP without owning platform adapters. |
| Cron: one-shot/recurring jobs, delivery to a chat or file, **no-agent mode** (script only, zero LLM), webhook-triggered jobs, per-job model and effort pin, cron cannot create cron | **RUN** (PORT the invariants) | EXEC-7 Daily Brief, EXEC-12 Proactive, P0.5 | No-agent mode is exactly "deterministic before model". Daily brief = an Agent OS script whose stdout Hermes delivers. |
| Memory-provider ABC: `prefetch(query)`, `on_memory_write`, `on_session_end`, `on_pre_compress`, `on_delegation` | **RUN** via an *Agent OS memory provider plugin* | EXEC-0.5, candidate memory, handoffs | `prefetch` → `agent.context`; `on_memory_write` → `agent.capture_candidates` (candidates only — no silent promotion); `on_session_end` → handoff/checkpoint. Keeps one source of truth. |
| Built-in memory: `MEMORY.md` 2,200 chars + `USER.md` 1,375 chars, frozen snapshot per session, overflow returns an error so the agent consolidates | **BORROW** | EXEC-0.5 | A hard char budget with forced consolidation is a cheap bloat guard for any always-loaded profile slice. |
| Skills (agentskills.io format, progressive disclosure) + **Curator**: `active → stale (14 d) → archived (30 d)`, pinned and cron-referenced skills exempt, never-used grace period, `--dry-run`, LLM consolidation off by default | **PORT** | P2.2 Skill Miner, skill registry hygiene | Deterministic lifecycle with no model cost; matches "no generated skill may silently self-promote". |
| Self-evolution (DSPy + GEPA on `SKILL.md`, eval from synthetic or session history, constraint gates, output is a PR) | **PORT/RUN on one skill** | P2.2, MIE-0020, PA-gepa (was DEFER) | Ends in a reviewable PR, not self-promotion. Agent OS already has a GEPA-style optimizer for the foreman (`foreman_optimize.py`). |
| `/heartbeat` (idle-only, missed ticks coalesce, user messages win, cache-safe) and self-paced `/loop` (backoff while replies stop changing) | **BORROW** | EXEC-12, campaign driver | Same semantics fix several driver/GUI watch issues. |
| Session search (SQLite FTS5 over past conversations) | **BORROW** | EXEC-8 Rescue Mode | Agent OS already uses FTS5 for mail; extend to agent sessions/handoffs. |
| Voice mode, wake word, TTS, Discord voice | **RUN** (later) | EXEC-13 | Alternative to building a Siri gateway first. |
| Hooks: shell `pre_tool_call` (can block), signed outbound webhooks | **BORROW** | Event Bus | Signed lifecycle events are a ready shape for Event Bus emission. |
| Approval mining: `hermes approvals suggest` from approval history | **BORROW** | operator UX | Suggest allow rules from what was approved repeatedly; applies to Claude Code permission friction too. |
| Honcho / hosted memory providers | **SKIP** | — | Server-side user modeling conflicts with local-first privacy. |
| Personality/SOUL.md, skins, pets, Spotify, Google Meet, computer use | **SKIP** | — | Not on the roadmap; computer use is covered elsewhere. |

### Orchestrator OS

| Hermes capability (verified) | Mode | Agent OS item | Why / how |
|---|---|---|---|
| One-shot headless CLI: `hermes -z PROMPT -m MODEL --provider P -t TOOLSETS` | **RUN** as a worker adapter | P1.2A, IMP-0015 | A third coding-agent CLI for any model: local vLLM/Ollama (free), OpenRouter (paid, behind `allow_paid_spend`). Complements the Codex custom-provider path. |
| Credential pools: plan-limit → rotate now; transient 429 → retry once; 402 → 1 h cooldown; "model not supported" → bench that key for that model only | **BORROW** (mostly done) | provider_health | Agent OS now has quota cooldowns from the reset time, learned unavailable models and per-node failover; the per-model bench is the one piece to keep. |
| Fallback providers: primary benched until the stated reset; `min_switch_reset_seconds` to wait instead of switching when the primary reopens soon | **PORT** | router | Agent OS now waits for resets when nothing else can run; add the threshold so a cheap provider resetting in <N min is waited for rather than failing over to an expensive one. |
| Tool Search: deferred tool schemas behind `tool_search/describe/call` | **BORROW** | IMP-0018, P1.2D | Workers are third-party CLIs, so this applies only to the Hermes worker (`-t` minimal toolsets). Same lesson as Agent OS's lean Codex flags (455 KB → 31.7 KB request). |
| Prompt-cache invariant (stable prefix first) | **BORROW** (low value here) | IMP-0018 | Measured: Agent OS's own prompt is <1% of worker input (≈939 of 162,540 tokens); the CLIs' prefixes dominate and are already cached by the provider. Reordering our prompt yields little; do not prioritize. |
| Micro-compaction, context-engine plugin, compaction evals | **BORROW** (method) | IMP-0019 | Relevant to long-lived foreman sessions; reuse their eval method (fidelity vs cost), not the code. |
| Kanban: 90%-of-iteration-budget checkpoint notice; "a commit or diff alone never completes a task"; consecutive-failure circuit breaker | **BORROW** | engine | The budget checkpoint complements the new stuck-worker detector; the other two Agent OS already enforces. |
| Delegation delivery semantics (admission ≠ completion, at-least-once on restart) | **BORROW** | GUI Updates/Chat | Correct semantics for posting background results to the operator. |
| Mixture of Agents (aggregator + reference models) | **BORROW** (later) | escalated review | A possible variant of the stronger-reviewer escalation; measure before use. |
| Kanban board / `delegate_task` as the multi-agent runtime | **SKIP** | — | Duplicates Agent OS's engine without worktree isolation, validator gates or cross-provider review. |
| Terminal backends (Docker, SSH, Modal, Daytona), trajectory compressor, batch runner | **DEFER** | IMP-0015 | Useful for remote GPU workers and training-data export once those tracks start. |

## Risks and conditions

- **Pin a release**, install from Git with `uv` into a separate environment, and update
  deliberately: daily churn and no internal compatibility layer.
- **One writer per `HERMES_HOME`** (their rule). Agent OS gets its own Hermes profile.
- **Paid spend**: do not enable Nous Portal or OpenRouter unless the run/operator allows paid
  spend; the default Hermes worker uses a local model.
- **Exposure**: the gateway accepts inbound messages; DM pairing and platform allowlists are
  mandatory, and every send/act path stays behind Agent OS autonomy policy.
- **Two memories**: built-in `MEMORY.md`/`USER.md` writes would fork state. With the Agent OS
  provider plugin active, keep the built-in files minimal and treat them as cache.

## Install decision (2026-10-01)

Not installed. The operator allowed installation only for real efficiency gains, and this
PC has no GPU suitable for local models. Checked against the Hermes docs
(`codex-app-server-runtime.md`, `subscription-proxy.md`):

- the only way Hermes uses the ChatGPT subscription is its Codex app-server runtime, which
  wraps the Codex CLI and adds Hermes' composed prompt, memory and tool callback on top. As
  an orchestrator worker that is strictly more input per task than the lean direct Codex
  invocation (request 455 KB → 31.7 KB). It also registers itself in the operator's
  `~/.codex/config.toml`;
- the Claude subscription is not usable by Hermes; its other model routes (Nous Portal,
  OpenRouter) are paid and `allow_paid_spend` is off;
- the messaging front door (H3) adds reach, not savings, and every conversational turn would
  spend the ChatGPT subscription through the same wrapper.

Phases that need Hermes running (H1, H2, H3) are on hold until one of: a local or rented GPU
endpoint becomes the routine worker path (Hermes could then use it), the executive Event Bus
(P3) needs a messaging front door, or Hermes gains a direct subscription path without the
wrapper. Phases that port mechanisms into Agent OS (H4, H5, H6) proceed without installing it;
H6 landed as `wait_for_reset_seconds`.

## Phased plan (each phase has its own test)

1. **H0 — record** (this document, PA-hermes-agent, IMP-0020). Done.
2. **H1 — worker adapter** `hermes_cli` in `orchestrator/adapters/` (one-shot, minimal
   toolsets, local model). *Test:* synthetic adapter tests (argv, result parsing, quota
   classification); one live run of `orchestrate benchmark small_code_change` against Codex,
   comparing cost per validated task.
3. **H2 — memory bridge**: Agent OS memory-provider plugin for Hermes + Hermes mounting the
   Agent OS MCP server. *Test:* plugin unit tests against a fake Agent OS; a memory write
   becomes a candidate and never a canonical record; `prefetch` stays within the context
   budget.
4. **H3 — front door**: one gateway platform (Discord or Email) delivering a no-agent cron
   Daily Brief generated by an Agent OS script, and relaying run-card chat. *Test:* no model
   call for an empty brief; sends require approval; at-least-once delivery after restart.
5. **H4 — skills**: port the curator lifecycle to the Agent OS skill registry and check
   agentskills.io frontmatter compatibility. *Test:* deterministic transitions, pinned and
   referenced skills exempt, dry-run equals real report.
6. **H5 — self-evolution**: GEPA on one Agent OS skill with protected holdouts, output as a
   candidate change for review. *Test:* holdout score noninferior, no holdout leakage.
7. **H6 — router threshold**: `min_switch_reset_seconds`-style wait-or-switch. *Test:*
   synthetic quota with a near reset waits; a far reset fails over.

Promotion follows the existing rule: adopt only on noninferior validation and a measured
improvement (cost per validated task, reliability, or operator time).
