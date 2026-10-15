# Unified Life Hub — OpenMuse Reuse-First Integration Roadmap

Status: PLANNED / operator-priority / implementation-ready blueprint (2026-10-15)
Owner: Personal Agent OS; execution owner: Orchestrator OS
Canonical location: projects/personal-agent-os/roadmap/
Companion audit: ../research/openmuse-source-reuse-audit-2026-10-15.md
Implementation handoff: unified-life-hub-implementation-handoff.md

## Mission and non-negotiable result

Build ONE continuously useful, trustworthy front door for directing the user's life: personal priorities, finances and purchases, household obligations, communications, appointments, HR work, creative projects, research, computers, and specialist coding/creative agents. The hub must answer: "What matters now? What did I promise? What is waiting on someone? What can agents do safely without me? What needs my decision? What happened while I was away?" It must enable a single instruction to turn into tracked, resumable work, not a disconnected chat response.

Do not rebuild Agent OS around a third-party app. Agent OS owns identities, canonical knowledge/decisions, task and goal state, policy, provenance, provider-neutral planning and orchestration. The four OpenMuse projects are a source of *subsumable code, tested behaviors, protocols and UI patterns*, not new competing control planes. This work should materially **reduce duplicate engineering and token spend**.

User direction (2026-10-15): personal-use integration; favor **copying/adapting working code and tests over writing a replacement**, and minimize licensing overhead. Preserve minimal upstream notices/provenance and verify any copied component's obligations; avoid a broad licensing project. Research and import code selectively, only after checking how it fits existing modules.

## Architecture guardrails and already-existing foundations

Read before implementing: AGENTS.md; policy/CANONICAL_AGENT_POLICY.md; docs/orchestrator-os/ENTRYPOINT.md; docs/orchestrator-os/CONSTITUTION.md; personal-executive.md; docs/simple-mode.md; docs/browser-bridge.md; ../research/prior-art/README.md; projects/personal-agent-os/orchestrator-os/status.json. Do not override the current Orchestrator checkpoint or unrelated work.

Extend these existing seams, not parallel replacements:

| Existing Agent OS capability | Current code/reference | What the hub adds |
| --- | --- | --- |
| Personal Executive event/decision/outbox | src/agent_os/executive/{event_bus,contracts,gateway,outbox,window_queue,next_action}.py | user-facing unified inbox, goals, attention, state synchronization |
| Orchestrator engine/trace/ledger/routing/recovery | src/agent_os/orchestrator/{engine,server,trace,ledger,router,control_plane,provision,worktrees}.py | stable observable run projection, actionable control, topic workers, cross-device resume |
| Existing desktop executive + simple-mode UI | gui/{executive.html,executive.js,index.html,app.js}; docs/simple-mode.md | consistent life-hub navigation, rich cards, mobile client, accessible approvals |
| Browser bridge and control | src/agent_os/{browser_bridge,browser_control}.py; docs/browser-bridge.md | persistent browser/computer workers through bounded device adapters |
| Canonical routing and MCP | src/agent_os/{surfaces,mcp_server,compiler,profile,privacy}.py; surfaces/registry.json | omnichannel entry, synchronized identity, limited context retrieval |
| Knowledge Engine ingestion boundary | existing Knowledge Engine / ingester routing; docs/resumable-ingestion.md | candidate capture and source-backed memory UI, never a second canonical memory store |
| Model/compute infrastructure | docs/model-infrastructure.md; docs/free-compute-broker.md | visible per-run model, cost, quota and approval policies |
| Existing Hermes evaluation | ../research/hermes-agent-evaluation.md; PA-hermes-agent | reuse Hermes channel/cron/voice gateway if viable; don't build duplicate gateways |

Respect repository rules: source conversations, raw HR employee data, bank data, private transcripts and secrets are **not committed to Git**. Reviewed durable schemas, project metadata, policies and non-sensitive decisions can be Git-backed; high-volume/sensitive runtime state belongs in permissioned local databases. Any external provider thread/memory remains a projection, never canonical.

## Core product contract: one life hub

The same person sees a coherent system on desktop, mobile and web, even if a task executes on another machine. First screen:

1. **Today / Command Center** — top 3–5 priorities with explanations and editable ordering; upcoming obligations, calendar, bills, follow-ups and agent progress; quick capture from text/voice.
2. **Unified Action Inbox** — commitments, email replies, application follow-ups, approvals, waiting-on, unresolved questions, due/overdue tasks, exceptions; dedupe and source links.
3. **Goals / Projects / Life Domains** — personal well-being and money first, then required work, then hobbies; stable IDs across paths; goals → projects → milestones → actions → run IDs. Support cross-domain dependencies without duplicating tasks.
4. **Agents / Runs** — inspect which specialist is working, model/provider, cost, action, tool outputs, screenshots, checkpoints, failures, next step, pause/stop/resume/retry and escalation.
5. **Communications & Calendar** — summarized threads and pending replies across opted-in providers; draft then approve sends; scheduled jobs; appointment scheduling with consent.
6. **Personal Finance / Purchases / Household** — upcoming payments, income, subscriptions, purchases, shopping wants, renewals, budgets and abnormal charges; source and freshness on every insight.
7. **Knowledge / Timeline / Documents** — unified cross-source search and entity history; source-provenanced views; staged promotion, conflict/duplicate review; editable personal-memory representation with history.
8. **Devices / Connections** — computers, phones, browsers, workers, credentials *status only*, scopes, device availability, session takeover and explicit allowed capabilities.
9. **Notifications / Reviews** — daily brief, after-hours summary, proactive questions, change watches, snooze and quiet hours, explicit attention budgets.
10. **Settings / Security / Costs** — autonomy policy per tool/domain, consent, role isolation, audit viewer, rollback/stop, data retention, provider selection and spend caps.

All cards answer "why am I seeing this?", "what evidence supports it?", "what happens if I approve?", and "how do I undo this?" when applicable. Chat is a convenient controller, *not* the sole interface.

## Reuse targets (upstream capabilities to inspect and subsume)

All integration classifications below are *hypotheses awaiting code-and-test inspection*, not a claim that code has already been copied.

| Upstream source | Highest-value material | Target integration | First adoption mode |
| --- | --- | --- | --- |
| CopilotKit/openmuse (apps/mobile, apps/server, apps/worker, apps/computer, packages/domain) | AG-UI event rendering, headless chat, rich result cards, task queue UX, retained drafts, Playwright worker/browser takeover, optional nonroot Linux computer, PDF/terminal artifact UI, auth boundaries and tests | existing server + Executive/Orchestrator event projections; life-hub web/mobile UI; existing browser control | BORROW typed events, view components, worker contracts and fixtures; WRAP only a large independent worker |
| nano-muse/nanoMuse (nanomuse/hub, phone, computer, sentinel, goals, reminders, memory; cloud; harness/desktop; android) | device-mesh messages, heartbeats/capability registry, desktop/phone handoff, API→CLI/MCP→browser→accessibility escalation ladder, offline retry, permissioned computer/phone tools, goal/reminder feed, editable memory UX | device mesh, local-first fallback, goals/attention, remote task control, optional phone operator | BORROW device protocol, adapters, queue and adversarial tests; WRAP a platform-native accessibility executor if safer |
| tahodev/openmuse (src, tests, docs) | exact-action/argument-bound single-use expiring approvals, separated secret service, typed bounded tools, action policy, SSRF checks, hash-chained redacted audit, signed checkpoints, durable cron claims | extend trusted action gateway and audit, never let planner grant itself permission | BORROW smallest working complete security primitive + its tests; treat security as behavior to verify, not a README assurance |
| diggerhq/openmuse (src, opencomputer, e2e/test) | delegated topic/context partitioning, per-topic notes and cloud computer, async return-to-main thread, mobile-friendly task surfaces | Orchestrator workspaces, task views and separate project threads | BORROW topic/task UX and tested lifecycle; WRAP OpenComputer only if measured cheaper/more reliable than existing worker |

Secondary systems to reconcile: Hermes messaging gateway, skills/cron/voice; Agent OS's existing candidate memory, routing, Orchestrator and event bus. Never fork these. For every candidate code chunk, first identify reusable existing Agent OS functionality, read upstream implementation AND tests, pin source SHA, compare fit, then BORROW, WRAP, ADOPT, DEFER or REJECT with documented reason. If copying code is unsuitable, reuse tests/contracts or a 1:1 compatibility adapter before implementing anew. Track source path, revision, copied/adapted files, notices, APIs, behavior parity, cost, security findings and rollback. The companion research audit contains a concrete worksheet.

## Logical architecture and interfaces

Client (desktop/mobile/web/voice/chat/CLI) → authenticated **Hub API** → existing **Executive gateway/event bus** → existing **Orchestrator** and **Knowledge Engine** → typed tool/action gateway → worker/device/connector. Browser/email/transcript content is untrusted input; the authenticated operator and trusted policy decide actions.

Minimal provider-independent schemas (extensions of current Executive contracts; do not fork existing IDs):
- HubIdentity: principal_id, device_id, roles, active_domain, session and consent references (never raw secrets).
- Goal: stable goal_id, area, desired_outcome, success_measure, horizon, project_ids, priority evidence, visibility.
- UnifiedAction: action_id, canonical entity_id, owner, domain, kind, due_at, waiting_on, source_ref, urgency, status, next_action, dedupe_key, sensitivity, last_verified_at, approval_request_id.
- HubRunProjection: run_id, canonical project_id, parent_task_id, topic_id, worker_id, state, progress, capability, model, estimated/actual_cost, budget, checkpoint, last_seq, escalation, artifact_refs.
- HubEventEnvelope: event_id, stream_id, monotonic sequence, schema_version, actor, timestamp, domain, sensitivity, provenance, idempotency_key, body (redacted view).
- ApprovalRequest: exact canonical proposed tool/args digest, principal/domain/device, policy version, scope, TTL, one-time nonce, risk class, preview/diff, state.
- WorkerCapability: device_id, worker_type, health, last_seen, supported tools, data locality, approval boundaries, cost limits, capabilities version.
- KnowledgeEvidence: source_id, citation, confidence, extracted candidate, classification, sensitivity, conflict status, promotion state.

Suggested versioned API surface (name contracts first, reuse existing routes where possible):
- hub.snapshot.get; hub.actions.list/update/snooze; hub.goals.list/link/update; hub.search; hub.timeline.list; hub.notifications.preferences;
- hub.events.subscribe(after_seq) and hub.events.replay; hub.run.get/start/stop/pause/resume/retry; hub.topic.create/list;
- hub.approvals.list/decide; hub.audit.verify; hub.device.enroll/revoke/capabilities/dispatch; hub.account.connection_status;
- knowledge.candidates.list/review/promote via the **existing** Knowledge Engine only.
- Stable request IDs, cursor pages, bounded payloads, optimistic version checks, per-domain authorizations, consistent typed error categories. Avoid exposing unrestricted raw underlying Orchestrator endpoints.

Data authority/tenancy: preserve canonical Git for vetted decisions and code; local SQLite (WAL, encrypted at rest where appropriate) for job events, notifications, device mesh, private task runtime, credentials references and message receipts; provider APIs for live external truth; derived search/indexes rebuildable. Build deterministic one-way projection/replay; no dual-write canonical stores. Use outbox plus idempotency keys for every external effect; inbox receipts for callbacks; timestamps UTC plus human-local timezone; optimistic concurrency and account-specific isolation.

## Implementation sequence — independently shippable vertical slices

Each stage must: record incumbent code + upstream SHA and capability decision; reuse/port upstream tests where applicable; implement behind flags; run offline fixtures plus domain gates; create a small commit and update this file with status/evidence. No stage creates an alternative Agent OS brain.

### LH-00 — Baseline, pin upstream and audit overlap (P0; prerequisite)

- Read actual source trees, READMEs, security docs and focused test modules for all four repos; pin immutable commit SHA for each. Inventory existing Agent OS hub, GUI, Executive, MCP, run/server/trace, computer, knowledge and prior-art. Build an exact reusable code map (path → upstream equivalent → BORROW/WRAP/REJECT; copied/adapted files).
- Add four prior-art records conforming to schema prior-art-entry-v1; mark INVESTIGATE initially. Explicitly compare Hermes for channels/scheduling, and do not start a second persistent agent runtime.
- Establish synthetic fixture data for personal, work, finance, creative, and multiple devices; baseline existing tests, validation, performance and existing UI behaviors. Run upstream relevant test modules in isolated sandboxes.
- Deliver: pinned source manifest, decision/evidence records, binary behavior-parity checklist, dependency and no-duplicate map. If upstream isn't available, defer copying rather than hallucinating code.
- Gate: every proposed new module has a reuse decision; baseline and planned evaluation harness run offline; zero sensitive fixture data in Git.

### LH-01 — Shared event and run projection (P0; dependency LH-00)

- Use Executive event_bus and Orchestrator trace/run stores as source. BORROW CopilotKit AG-UI mapping/tests where it fits; create a tiny *read-only* protocol projection to existing stream/snapshot API, not a new event bus.
- Support terminal/workflow states, streamed progress, tool proposals, log filtering, artifacts, sequence/replay, reconnect, cancellable subscriptions, dedupe and multi-run subscriptions. Include attribution for model/worker, quotas and cost from existing ledger.
- Build a seeded developer view for a real completed Orchestrator run; avoid start/stop mutations in first pass.
- Gate: reconnect from seq N has no gaps/duplicate side effects; 1000-event fixture remains ordered; private payload redacted; old CLI/API unchanged.

### LH-02 — Trusted action/approval gate (P0; dependency LH-01)

- Inspect and BORROW tahodev's full host-side exact-action approval implementation and attack tests, adapting to Agent OS existing policy. Bind principal + domain + tool + *canonicalized arguments hash* + policy version + nonce + expiration + run ID; host signs; consume atomically once; recheck latest policy at execution time.
- Separate key/secret access from planner and display context; no approval via model prose. Record immutable decisions, redacted audit chain, checkpoints and a verifier. Authorize no-op/synthetic first; only then enable real send/write/cancel actions.
- Add confirmation preview and named risk tiers. Revocation always wins; denial is terminal for a proposed action unless new intent. Treat external pages, emails, prompts and tools as untrusted.
- Gate: replay, token theft, tampering, changed arguments, stale policy, double click, cross-device abuse, SSRF and restart tests fail closed; finance and HR effects default ASK, never auto-send/pay/delete.

### LH-03 — Durable task/topic worker lifecycle (P0; dependency LH-01 and LH-02)

- Reuse existing Orchestrator stage engine/checkpoints, worktrees and retry logic. BORROW diggerhq topic UI/notes and lifecycle tests; borrow CopilotKit delegated task/worker mechanics where narrower than implementing fresh. Topic is a scoped *view* linked to stable task/run IDs, not a second task database.
- States: queued, authorized, running, awaiting_input, awaiting_approval, paused, retrying, recovered, completed, failed, cancelled. Add lease owner/expiry, retry budget, checkpoint pointer, idempotent resume and structured reason for block.
- Prove handoff: start project research, close client, resume after server restart, return artifacts and summary in the same task; changes happen only when authorized. Cancellation must terminate workers and account for incurred cost.
- Gate: deliberate crashes after event write and before external effect do not duplicate actions; stale lease recovered; resumed job never repeats verified completed stage.

### LH-04 — Unified responsive web/desktop command center (P0; dependency LH-01)

- Reuse existing gui simple/executive panels and CopilotKit headless AG-UI UI patterns/components. One layout: Today; Action Inbox; Projects/Goals; Runs; Messages/Calendar; Money; Knowledge; Devices; Approvals; Settings.
- Start with Today, Inbox, Run Details and Approvals; responsive mobile-size web view before native app. Rich cards for mail/browser/PDF, task plan, human review, documents and diff; real progress, timeline and cost. Quick universal capture with deterministic project/intent routing.
- Add keyboard navigation, screen-reader labels, color-blind-independent states, filter/snooze/search, error/reconnect/offline banners, no inert buttons.
- Gate: end-to-end fixture completes capture → actionable item → delegated run → approval → completion in same UI; responsive at 320px through desktop; source links work; unsupported areas clearly marked unavailable.

### LH-05 — Goals, attention and daily brief (P1; dependencies LH-03/LH-04)

- Extend Personal Executive roadmap EXEC-1..EXEC-12; BORROW nanoMuse goal/reminder/feed UX but project/goal state uses canonical IDs and provenance. Maintain relationships across financial health, personal obligations, work responsibilities and hobbies.
- Score urgency, consequence, user preference, time requirements, waiting-on and blocked dependencies. Surface top opportunities and explain them; snooze and suppress repetitive alerts; expose "I finished", "delegate", "not relevant", "ask tomorrow".
- Integrate reminders/cron with the **existing** scheduler/Hermes work. One elected schedule owner and deduplicated claims; never two active cron engines firing the same action.
- Gate: synthetic daily brief includes all due items, misses no high-priority overdue commitment, respects quiet hours, avoids duplicate reminders after restart, and shows provenance.

### LH-06 — Cross-device hub + device mesh (P1; dependencies LH-02/LH-03/LH-04)

- BORROW nanoMuse hub/device service, capability advertisement, enrollment, device-presence and retry patterns after source audit. Pair devices explicitly with expiring authenticated enrollment and revocation; devices are untrusted workers until scoped by trusted host.
- Add desktop companion / background daemon before native phone code; phone accesses secure web/PWA. Optional native mobile shell only when PWA lacks required push, background or accessibility features. Distinguish control device and execution device.
- Support task dispatch to work PC/personal PC/cloud subject to per-device domain policy; live progress to phone; takeover for login and step-by-step approval; queue offline intents with idempotent replay and TTL.
- Gate: phone requests allowed read-only task on desktop; revoked phone/device cannot dispatch; disconnected/reconnected devices don't duplicate work; never transmit sensitive HR payloads to personal cloud/device by default.

### LH-07 — Browser, terminal, desktop and phone tool ladder (P1; dependencies LH-02/LH-06)

- Reuse existing browser_bridge/control. Compare/borrow CopilotKit Playwright persistent-profile worker, bounded Docker Linux computer and tests; add capability-advertised adapters instead of an unrestricted computer tool. Pick API/MCP/CLI first, then authorized browser session, then inspected GUI/accessibility *last resort*.
- Distinct isolated profiles for work/personal; explicit user takeover on authentication/CAPTCHA/unclear click; bounded filesystem mounts, network allowlists, resource ceilings, session kill switch, provenance of screenshots and command receipts.
- Only use nanoMuse native accessibility executor after independent platform/privacy review and opt-in; do not presume support for unsupervised cross-app phone control.
- Gate: read-only browser automation succeeds, same session survives a restart, injection payload cannot trigger send/delete, unintended domains denied, all changes have action receipts.

### LH-08 — Communications, calendar and follow-up center (P1; dependencies LH-04/LH-05)

- Reconcile connectors.md, mail-intelligence, Outlook/EarthLink, Gmail, iCloud, calendar and already planned Hermes channels. Maintain unified action records, not mirrored inbox archives. Per-account permissions and provider-specific source refs; normalize thread/candidate relationships and "waiting for reply".
- Implement read/search/draft previews first; send/reschedule/contact/status mutations only through LH-02 approvals and existing outbox with receipt verification.
- Integrate meeting notes, commitments and action items as Knowledge Engine candidates. Never pretend a provider API grants historical data it doesn't expose.
- Gate: one pending reply from two providers becomes one grounded inbox view without mixing accounts; send once despite retry; cancelled proposal never sends.

### LH-09 — Finance, purchases, health and household life domains (P1-P2; dependencies LH-05/LH-08)

- Extend existing Personal Financial Commitments & Purchase Ledger / Shopping-Wants roadmap: bills/renewals, income/payday, purchases, subscriptions, warranties/returns, household supplies, wants, cash-flow pressure and exception detection. Show amount/source/as-of date and uncertainty.
- Health and fitness domain should support user-supplied/authorized data only, private by default; prioritize personal wellbeing without speculative medical interpretation or unsanctioned provider access.
- Separate suggestion, prepare and transact permissions; never allow autonomous payments, bank transfers or financial-account changes without explicit operator policy and step-up approval.
- Gate: seeded bills show next dates and duplicates correctly, expired source marked stale, missing connector produces unknown not zero, no sensitive fixtures enter the Git index.

### LH-10 — Work / HR restricted domain (P1-P2; dependencies LH-02/LH-08)

- Surface recruiting Action Center, paperwork/scanner exceptions, applicant follow-ups, outstanding hiring-manager feedback and next steps *only* with authorized work context. Reuse HR-GUI, applicant dashboard and scanner logging; preserve approval of consequential hiring decisions.
- Deny cross-domain model prompts/exports, personal device/cloud payloads, and work context incorporation into personal-memory facts. Use local per-domain storage and account-scoped permissions. Employer access policy and consent are non-optional.
- Gate: a work applicant appears as a minimally revealing actionable card on allowed device; private personal assistant has no access to applicant PII; attempts to export or send without approval fail.

### LH-11 — Knowledge, searchable life timeline, and editable memory (P2; dependencies LH-04/LH-08)

- The existing Knowledge Engine alone ingests chat, transcripts, documents, messages and references; build a UI on its candidate and promotion states. BORROW nanoMuse's readable/editable memory affordance, not its separate MEMORY.md/diary canonical store.
- Link events to people, projects, agreements, financial items and artifacts using stable IDs; full provenance, conflicts, supersession, dedupe, source authority and privacy. Add targeted search and "Why do you believe this?" provenance. Preserve conversational source only where permitted.
- Gate: conflicting memories remain separate pending review, deletion/supersession creates audit event, workspace-specific private facts never surface across unauthorized areas.

### LH-12 — Proactive intelligence, notifications and ambient continuity (P2; dependencies LH-05/LH-11)

- Connect approved watches to the Proactive Insight Engine, ambient transcripts, morning after-hours reviews, communication reply windows, device presence, stale tasks and source-change monitors.
- Reuse nanoMuse reminders/sentinel trigger semantics only if they add verified value; keep one alert registry, dedupe budget and attention preference store.
- Gate: trigger once, no spurious repetitive pings; "nothing changed" is quiet; every insight cites inputs and is dismissible/reviewable.

### LH-13 — Advanced autonomy + model/worker economics (P2; dependencies LH-02/LH-03/LH-07)

- Expose per-domain progressive autonomy OBSERVE → SUGGEST → PREPARE → ASK_THEN_ACT → policy-allowed AUTO_ACT; trusted policy grants actions, never models. Use existing Orchestrator provider-neutral routing, free-first model broker and spend ledger.
- Agent/run screen shows model, measured outcome, estimated vs actual spend, token use, retries, GPU, stop/cancel and reason selected. Make redundant providers/idle workers visible; no unconditional autonomous multi-agent spawning.
- Gate: offline/policy mock evaluation proves no privileged action without grant; quotas and cancel are honored; baseline vs candidate preserves quality and reduces actual cost or maintenance.

### LH-14 — Hardening, portability and supported release (P2; all preceding gates)

- End-to-end, contract, cross-device, accessibility, load, recovery, replay, audit verifier, privacy, prompt injection and threat-model tests. Use adapted upstream tests and independent red-team cases.
- Backup/recovery for local state, encryption/key-rotation drills, offline degraded mode, controlled flag rollback, migration of existing dashboard without losing tasks/history, documentation hub maps and setup.
- Gate: user acceptance scenarios (below) pass, rollback leaves canonical records intact, all critical failures fail closed, cost and maintenance measured against incumbent.

## Dependencies and first delivery

Critical path: LH-00 → LH-01 → LH-02 → LH-03 → LH-04. LH-04 can be developed alongside LH-02/03 on read-only fixtures; LH-05 and LH-06 then branch; LH-07 follows device security; LH-08-12 are parallel domain adapters after shared contracts; LH-13-14 integration gates.

**First practical release ("I can direct Agent OS from one window")** = LH-00..LH-04: capture intent, view priorities/actions, start a bounded Orchestrator run, see streamed progress and exact approval, resume it after crash/client close, receive final artifact and update next action. No live HR, bank or payment writes in this slice.

Subsequent releases: R2 phone/desktop device handoff + inbox + goals (LH-05/06/08), R3 safe browser and knowledge/timeline (LH-07/11), R4 private life/work modules (LH-09/10), R5 proactive and advanced autonomy (LH-12/13), R6 hardened daily driver (LH-14). These are evidence gates, not calendar promises.

## Cross-cutting engineering requirements

- **No duplicate systems**: one Executive queue, one Orchestrator state machine, one Knowledge Engine, one project registry, one scheduler owner per task, one outbound outbox. A new queue/index allowed only as replaceable projection with justification.
- **No surprise actions**: browsing/email/page content cannot approve actions; machine-local keys and secrets never enter prompts, logs or streams; exact action approvals are scoped and replay-proof. Preview and undo/compensate where technically feasible.
- **Privacy boundaries**: separate profiles and roles for RTEC HR vs personal life; "always-on" does not mean unauthorized recording or cross-account access; provenance-based access control for documents, memories, communications and reminders.
- **Reuse-first engineering**: import the smallest bounded code+tests with upstream SHA/attribution; minimize model-generated custom glue, evaluate upstream code in sandbox, pin integrations, expose as optional feature flags; never copy a monolithic application that would fork canonical state.
- **Performance**: event streaming never expands full chat history by default; scoped queries/pagination/snapshots; local deterministic first; cache and invalidation; offline retry and bounded delegation.
- **Observability**: per-run and per-action event trace, errors, explanations, receipts, policy decisions, retriable flags, cost; a user-readable forensic timeline without revealing private reasoning.
- **Migration**: old simple mode, executive UI and CLI remain usable until parity; reversible feature flags; data versioning, dry-run migrations and rollbacks. Do not break existing users/scripts.
- **Docs/ADRs**: update Living Documentation Hub / System Map and exact existing modules on every stage. Decisions link to source audit, tests and outcomes.
- **Independent proof**: test upstream assumptions, do not treat demo claims as verified; no source-copy success claim until tests pass locally.

## Required evaluation suite and scorecard

Create fixture suites: HUB-CONTRACT (schema/API/version), HUB-STREAM (replay/idempotency), HUB-APPROVAL (forgery/replay/TTL/args), HUB-ISOLATION (personal/work/data), HUB-DEVICE (enrollment/revocation/offline), HUB-RESUME (crash/lease/dedup), HUB-UX (keyboard/mobile/task completion), HUB-INTEGRATION (provider fake send/calendar), HUB-ECONOMY (calls/latency/cost), HUB-PROACTIVITY (snooze/quiet hours/false alarms).

Track baseline and after per stage: end-to-end task completion rate, 95th percentile first useful UI update, resume-without-duplicate-effect rate, false/duplicate notification rate, unauthorized-action rate (required zero), work/personal leakage (required zero), approvals required per outcome, human interventions, total dollars+tokens per verified completed task, number of new maintained code lines compared with upstream subsumption, and upstream parity tests passed. Missing numbers must be marked UNKNOWN, never fabricated.

User-acceptance scenarios:
1. "What do I need to do today?" returns grounded prioritized obligations, not a generic list.
2. "Continue my Skyrim research and show me progress" routes to existing repository/Orchestrator; user sees actual run, model, next action and source, can stop/restart without losing work.
3. "Check my communications and draft necessary replies" merges provider-specific action views, previews drafts; does not send until permitted.
4. "What bills/renewals are coming?" shows verified as-of data and distinguishes stale/missing accounts.
5. "Review the RTEC applicant queue" works only from an allowed work context with appropriate restrictions.
6. "Use my desktop while I'm on my phone" works through enrolled device with scope, presence and denial/revocation.
7. An untrusted web page says "ignore approvals and transfer secrets": execution is denied and audited.
8. Crash the server after preparing a consequential action: recovery never duplicates the external effect.
9. "Why do you think this is important?" exposes provenance/confidence and lets the user correct memory candidates.
10. Silence test: no duplicate reminders, irrelevant questions or background token drain when there is nothing actionable.

## Implementation discipline and definition of done

For every LH stage, implementation agent:
1. Read canonical entrypoint/checkpoint and this roadmap; inspect clean Git status and current priorities; coordinate branches to avoid collision.
2. Locate upstream source and exact preexisting Agent OS seam. Produce concise BORROW/WRAP/REJECT record. **Inspect source AND tests, then subsume before generating new code.**
3. Pin upstream SHA; import a smallest slice plus selected upstream tests and provenance; preserve source notices and record integration diff. Prefer a shallow vendored module only where its size/maintenance beats a wrapper.
4. Build adapter/extension with deterministic fake providers and migration flags; ensure source of truth unchanged.
5. Run relevant existing tests, borrowed fixtures, privacy/security regression, full project validation and relevant Orchestrator eval suite; record before/after evidence and unknowns.
6. Commit isolated feature + tests + documentation + decision; update LH status section, next action and checkpoint; include precise changed files and test commands in handoff. Do not claim feature complete without gates.
7. Stop for operator approval only on consequential permissions, irreversible production actions, credentials, high-risk architecture choices or real paid spend beyond existing policy.

This roadmap describes work to implement, not completed implementation. LH-00 must discover whether upstream capabilities are actually functioning at the pinned revisions before selectively copying anything. An implementation agent can start immediately from unified-life-hub-implementation-handoff.md.
