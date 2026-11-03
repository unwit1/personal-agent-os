# Paperclip and adjacent agent-coordination systems: adoption study

**Research date:** 2026-10-10. **Canonical referent:** [PaperclipAI/paperclip](https://github.com/paperclipai/paperclip) (MIT). Operator typed 'papercliped'; this is the most likely target, but avoid conflating it with unrelated similarly named projects. **Status:** research/proposal only. No install, database, third-party worker, remote listener or expenditure.

## Sources and upstream reality

- Official [Paperclip README](https://github.com/paperclipai/paperclip) describes a Node.js API server + React UI (embedded PostgreSQL for local use), goals/projects/issues, org charts/agent roles, scheduling via heartbeats, costs and quotas, scoped secrets/connections, per-org separation, approval gates, revisioned config, skill studio and import/export company/team templates. Supports Codex, Claude Code, Gemini CLI, OpenCode, Hermes, and custom endpoints.
- [Paperclip heartbeat skill](https://github.com/paperclipai/paperclip/blob/master/skills/paperclip/SKILL.md) documents authenticated agent identity, scoped wake payload fast path, atomic issue checkout, approval-triggered wake and routine triggers (cron/webhook/API), concurrency/catch-up policies.
- [Gas Town](https://github.com/gastownhall/gastown) is an MIT multi-agent development orchestrator emphasizing persistent issue state, worktree isolation, convoys and merge queue, with [Beads](https://github.com/gastownhall/beads) as issue graph.
- [OpenHands SDK](https://github.com/OpenHands/software-agent-sdk) provides Python agent runtime and remote isolated workspaces; [Hatchet](https://github.com/hatchet-dev/hatchet) provides durable queues/retries/rate limiting/Postgres; [LangGraph](https://github.com/langchain-ai/langgraph) provides checkpointed agent graphs and HITL.
- [Vibe Kanban](https://github.com/BloopAI/vibe-kanban) has useful visual PR/workspace review but **officially announces sunsetting**. Borrow UI principles only; no new long-lived dependency on a sunset project.
- [OpenCode](https://github.com/anomalyco/opencode) is a candidate worker runtime with model selection and plan/build permissions; [OpenClaw](https://github.com/openclaw/openclaw) is a messaging gateway, not a substitute for the Orchestrator's canonical job database.

## How Paperclip would integrate

**Recommendation: BORROW individual reliability concepts now, investigate WRAP as an optional human-facing control plane later. DO NOT replace Orchestrator core or create competing canonical state.** Existing `IMP-0015` includes routing/capability registry, EVR/CAP evals, budget gating, durable checkpoint and delegation; the user explicitly values simplicity, cost savings, and no duplicated work.

| Paperclip capability | Agent OS/Orchestrator existing element | Gap to probe | Candidate integration |
|---|---|---|---|
| Atomic task checkout | status/checkpoint + task run model | Parallel workers racing for same issue | Persistent task lease with atomic compare-and-swap, owner, epoch, expiry, idempotency key; tests under crash/stale worker |
| Heartbeats and scoped wake | resume snapshots, next-prompt, scheduler and jobs | Context overhead per wake, lost wake-ups | Signed scoped delta with issue ID, lease token, last revision, changed fields; no full reread when fresh |
| Org chart / goal ancestry | metadata-driven project ID + domain boundaries | Explain why a task supports project goal | Optional goal->epic->task trace; not standalone 'companies' db |
| Agent/project/company budgets | Compute Broker quote/budget and approval | Budget visibility, rolling subscription quota control | Hierarchical per-run/project/provider ceilings and pauses; no autonomous spending approval |
| Scoped API connections | secret references and authorization gates | Per-agent eligibility, easy revocation | Human identity -> connected account -> action scopes -> project/domain -> agent run; expire and audit |
| Skills Studio/testing | Knowledge Engine/skill mining/EVS | Compare skill versions with saved test cases | Versioned skill manifest + replay test corpus + rollback; import templates only after security review |
| Run timeline/phone dashboard | Orchestrator run visibility | Read-only mobile run oversight | Optional status/approval UI, redacted tool/trace view; direct web exposure only behind authenticated private channel |
| Config revision/rollback | Git and ADR, protected control plane | Revert UI-config edits safely | Deterministic config diff + reversible migrations + approval on policy/budget changes |
| Org templates | project templates + metadata | Repeatable agent team profiles | Declarative templates with ID remapping, no credentials, no implicit permissions |
| Scheduled routines | automation triggers + task queue | Race, catch-up semantics | Cron/webhook/API trigger with idempotent enqueue, catchup policy and max overlap |

## Optional Paperclip adapter design (only after a spike demonstrates benefit)

```text
Agent OS Canonical Project / Task / Goal IDs
  -> Paperclip Bridge (optional, feature flag off)
       - Map AgentOS task ID <-> Paperclip issue ID with version/ETag
       - Project scope + authorized read-only mirror first
       - Signed webhook/event in; prevent echo loops, dedup by event ID
       - Assignments -> Orchestrator create/start-recommended (approval gated)
       - Model routing remains Orchestrator Model Infrastructure Manager
       - Results/artifacts/status -> scoped Paperclip issue annotations
       - Permissions -> intersect Paperclip agent role with Agent OS deterministic policies
  -> Existing CAP/EVR evidence + run ledger remain canonical
```

Prototype phases:

1. **Gap audit (zero dependency):** run existing Orchestrator concurrency/crash and budget tests, record what fails. Compare latency, run recovery, error rate and operator workload.
2. **Borrow with bounded change:** deterministic atomic checkout and lease renewal (if missing), signed scoped wake with revision delta, session resume, structured task ancestry and auth tests; no front-end/server rewrite.
3. **Shadow adapter:** a local Paperclip test instance with synthetic projects and fake API keys; create/read mirrored issues only, measure desync/replay/conflicting writes and count extra resources.
4. **Canary optional UI:** expose read-only phone-view status and explicit approving operator flow. Require exact domain, SSO, audit redaction, retention and local privacy threat review.
5. **Decision gate:** WRAP only if measurable user value exceeds maintenance, dependency, duplicated state and data exposure. Reject if own Orchestrator already meets requirements with less complexity.

## Test matrix

- Two workers attempt checkout of the same task at once -> exactly one winner; stale heartbeat cannot mutate task after lease epoch changes.
- Crash after checkout but before completion -> lease reclamation and resume without duplicate commit, credit-spending or external message.
- Retried webhook / reconnect / repeated routine -> no duplicate workflow dispatch or missing audit record.
- Approval rejected while background agent running -> deterministic stop/no side effects; refusal to grant permissions through generated text.
- Cross-project/domain access -> no read/write/secret escape, even if UI company/role claims access.
- Budget exceeded across parallel agents -> atomic reservation and rejection, not only a dashboard alert.
- Skill/template import includes embedded network hook/secrets -> reject/quarantine; no implicit connection grants.
- Model rerouted from API to subscription -> enforce interactive-vs-background terms, rate limit and credentials.
- Provenance of borrowed code/license -> preserve license notices and upstream revisions, security scan each import.

## Similar project comparison and stance

| Repo | Distinct advantage | Decision |
|---|---|---|
| [Paperclip](https://github.com/paperclipai/paperclip) | Management UI, goals, budgets, agent roles, skills, heartbeats, connection governance | BORROW now, optional WRAP trial |
| [Gas Town](https://github.com/gastownhall/gastown) / [Beads](https://github.com/gastownhall/beads) | Agent workspace isolation, dependency tracking and merge pipeline | BORROW merge/worktree mechanics if needed |
| [OpenHands](https://github.com/OpenHands/software-agent-sdk) | Remote sandboxed coding agent SDK | Optional worker adapter |
| [Hatchet](https://github.com/hatchet-dev/hatchet) | Production queue and durability | Compare to existing code; avoid a second engine |
| [LangGraph](https://github.com/langchain-ai/langgraph) | Explicit graph checkpoint/HITL | Already in prior-art registry, reuse failure tests only |
| [OpenCode](https://github.com/anomalyco/opencode) | Provider-flexible CLI coding runtime | High priority worker adapter benchmark |
| [Vibe Kanban](https://github.com/BloopAI/vibe-kanban) | Worktree+PR review UX | BORROW UI, SUNSETTING upstream |
| [OpenClaw](https://github.com/openclaw/openclaw) | Mobile/chat gateways, scheduled channels | Optional authorized channel adapter, avoid new principal store |

**Supply-chain/ops assessment:** Paperclip MIT but backend is Node + PostgreSQL + React; installing its stack is a material new dependency and operational responsibility. Running in trusted local mode is NOT an authorization boundary; remote/mobile access needs authenticated/private-network deployment. Leave anonymous telemetry off in privacy-sensitive environments; check the upstream telemetry config. Review new dependencies/packaged skills before enabling. Do not infer company/employee authority from agent role labels.

**Why this matters to the model project:** Paperclip's model-per-agent support can supply an intuitive management surface, but Orchestrator's own price/benchmark evidence and capability router must remain vendor-agnostic and canonical. Measure task-level cost with exact API key ownership, plan eligibility, source model and bill rather than only displaying 'tokens used'.

**Followup owner:** Orchestrator Orchestration/Run Visibility + IMP-0015, reuse existing prior-art/decision metadata. Record relationships as EXTENDS existing rather than new control plane. No public benchmark or runtime comparisons executed in this desk-research pass.
