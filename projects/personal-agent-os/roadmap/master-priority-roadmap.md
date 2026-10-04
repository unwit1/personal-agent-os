# Personal Agent OS — Master Priority Roadmap

Status: active / canonical priority order  
Owner: Personal Agent OS  
Reprioritized: 2026-09-19

## Purpose

This file defines the **implementation priority order** for Personal Agent OS.

Detailed subsystem requirements remain in the linked roadmaps. When a subsystem roadmap's internal numbering conflicts with this file, **this master roadmap controls what should be built first**.

The current optimization target is:

> Reduce unnecessary ChatGPT Work usage, model tokens, repeated OCR, repeated retrieval, repeated file scanning, and duplicated agent work before adding features that create more model demand.

The system should first become economical, resumable, selective, and deterministic. New executive/autonomy features should then inherit that efficient foundation.

## Priority rules

Use these rules when deciding what to implement next:

1. **Avoid model work entirely when possible.** Prefer deterministic code, indexes, exact matching, cached results, structured parsing, and validated reusable skills.
2. **Never repeat expensive work unnecessarily.** Every long crawl/import/document-analysis workflow should checkpoint, deduplicate, and resume.
3. **Minimize context before changing models.** Retrieve only the project/profile/history slices necessary for the current task.
4. **Use local computation before cloud reasoning when reliable.** Especially for OCR, hashing, classification, parsing, indexing, and document fingerprints.
5. **Measure before tuning.** Record privacy-safe usage/latency/cache/escalation telemetry when available; never invent unavailable metrics.
6. **Escalate only on evidence.** Start with the cheapest reliable path and move to stronger reasoning only after validation failure, ambiguity, conflict, or explicit quality requirements.
7. **Do not shift cost invisibly.** OpenAI/Anthropic API delegation is optional and separately billed. First exhaust savings that reduce total work instead of merely moving it to another bill.
8. **Preserve correctness and privacy.** Usage savings must not weaken validation, employee-data boundaries, provenance, or user approval controls.

---

## P0 — Agent-first execution and immediate usage reduction

This is the highest-priority work. P0.0 and P0.1 must be treated as the first implementation targets unless an urgent correctness/privacy bug intervenes.

### P0.0 — Universal Agent OS routing for chats and work projects

Status: **complete** (2026-09-21). All acceptance criteria met and covered by
regression tests; `validate` reports 0 errors and 0 warnings, and
`integration-health` reports every registered surface at or above its expected
tier. Remaining technical debt is recorded below rather than left implicit.

Verified on completion:
- machine-local path resolution, with canonical Git content free of machine
  paths (adapters render a `{{AGENT_OS_REPOSITORY}}` placeholder at install);
- multi-parent project inventory, including `job-applicant-dashboard`;
- deterministic skill deduplication (22 skills, 0 duplicates);
- generic router project resolution that still leaves genuinely ambiguous
  requests unresolved rather than inventing certainty;
- MCP lifecycle over stdio, served in the process the client spawned;
- token-budget pruning ordered by usefulness, preserving improvements and the
  handoff's next action at constrained budgets.

Known technical debt carried forward:
- ChatGPT chat/Work surfaces remain "partially bridged" by design; no
  automatic preflight mechanism exists for those hosts, and none is claimed;
- `mcp-compatible-client` is a server-side readiness entry, so it stays
  bridged until an individual client registers and carries a preflight;
- improvements/changes streams are empty for this project, so their pruning
  behavior is proven by fixtures rather than by production data.

Make Agent OS the default execution/context layer for every supported ChatGPT chat, Work project, coding-agent task, and other connected agent surface.

Goal:
- the user should not have to remember to manually tell an agent to consult Agent OS;
- every supported request should pass through a lightweight Agent OS preflight before substantial reasoning or implementation begins;
- Agent OS should resolve the likely project/domain, retrieve only relevant durable context, select applicable skills/policies, identify privacy boundaries, and create/update resumable handoff state;
- material outcomes should flow back through the candidate-memory/project-update pipeline rather than remaining trapped in a single conversation;
- GitHub remains canonical for durable reviewed project state while local/private stores retain sensitive or high-volume raw data.

Required execution path:

client/chat/work task
→ Agent OS preflight
→ project/domain resolution
→ selective context + skills + policy retrieval
→ workflow/stage routing
→ model/tool execution
→ validation/checkpoint
→ candidate durable update/handoff

Client-support requirement:
- where a client can call Agent OS directly through MCP/plugin/app/API integration, use Agent OS automatically as the default gateway;
- where a client cannot invoke Agent OS automatically, provide the thinnest available capture/bridge mechanism so the conversation or task can still produce a resumable handoff and durable candidate updates;
- never claim that an unsupported host can be invisibly intercepted or that Agent OS can hot-swap the model already running in the host.

Acceptance criteria:
- supported ChatGPT/Work/coding-agent entry points do not require the user to manually restate "check Agent OS";
- project-relevant context is automatically retrieved selectively;
- completed work emits a compact handoff/checkpoint and candidate durable updates when appropriate;
- privacy policies are applied before context leaves local/private zones;
- an integration-health command/report can show which client surfaces are fully routed, partially bridged, or not yet integrated.

Success signal:
- project continuity and Agent OS context become the default behavior rather than an opt-in prompt convention.

### P0.0A — Unified Connector Broker + cross-surface auto-provisioning

Status: **on hold** (2026-10-04), awaiting operator decisions: the launch command written into native
client MCP entries, whether Agent OS may write client configuration (preview-first, confirm_write, backup),
credential value resolution, and live provider health checks. Fifteen no-input slices landed 2026-10-02..04
(reconcile plan, credential presence, native server names, change events and cursors, unregister,
conflicts, stale pruning, readiness, enable/disable, config-level native verification, subscribers).
Set back to in progress once those are decided. Earlier: (2026-09-23) Added the v1 provider-neutral connector
registry schema, empty canonical registry, strict privacy-checked loader, and
read-only `connector.list` MCP discovery with secret-reference redaction.
`connector.register` now previews metadata by default and supports an explicit,
serialized, idempotent write of desired-only metadata; it cannot mark provider
health or client registration as verified.
`connector.import_candidates` now scans registered client configuration files
read-only and returns only stable candidate IDs, server labels, executable
basenames, and surfaces; candidates remain unclassified until provider identity
and scopes receive explicit review, and no configuration is changed.
`integration-health` now reports registry-declared connector-provider health and
per-surface readiness reasons in a separate `connector_providers` section. Its
`surface_readiness` entries distinguish registry-ready-but-unverified from
blocked, naming reachability, registration, and provider-health gaps. A surface
filter narrows the readiness checks while retaining all configured connectors.
This reads declared status only and does not probe provider APIs or claim live
invocation. `connector.import` and `connector-import` now attach explicitly
reviewed provider, capability, scope, privacy-domain, and local secret-reference
metadata to a currently discovered candidate. The flow requires separate
`reviewed` and `confirm_write` flags, never copies client configuration or
credential values, and records only desired registrations until an adapter
verifies them. The Agent OS MCP server now re-imports edited code on the next
tool call (2026-09-24), so new connector tools become available without a
host-side restart. (2026-10-02): `connector.reconcile_plan` (MCP) and `connector-reconcile-plan` (CLI) now return a read-only per-registration action plan (none, investigate, provision_local_config, manual_host_setup, undetermined, unknown_surface) derived from desired registry state and each surface's declared connector capabilities; it applies nothing, resolves no credentials, and contacts no providers.
(2026-10-02): `connector.credential_status` (MCP) and `connector-credential-status` (CLI) now give a read-only, presence-only credential check per connector: `env:` references report present/missing, other secret-store backends report unchecked, and connectors without a reference report not_configured. They never return values or reference names and never contact providers.
(2026-10-02): connector.credential_status now probes windows-credential references (Windows Credential Manager existence check, credential blob never read) and macos-keychain references (security find-generic-password without -w) for presence, reporting present/missing or unchecked when the probe is unavailable on the host; keyring and secret-service remain unchecked, and credential resolution, adapter execution, and applied reconciliation remain open.
(2026-10-02): Registrations now accept an optional `server_name` (schema, validator, and the MCP register/import inputs) per decision (c): a connector is registered on a surface when reachable through its Agent OS bridge, and `server_name` additionally requests a native client MCP entry; `connector.reconcile_plan` reports `native_server_name`/`native_entry_requested` read-only. Writing native client config (preview-first, explicit confirm_write) remains next.
(2026-10-02): `connector.reconcile_plan` now reports a read-only `native_entry_status` per registration (not_requested, unknown_surface, not_inspectable, unreadable, present, absent) plus `native_entry_status_counts`, by reading only server names from each inspectable surface's declared client config files; it returns no paths, commands, or env and writes nothing. Writing native client config is blocked on a decision about where a native entry's launch command comes from (registry launch-spec field, a generic Agent OS bridge proxy command, or copying from a discovered config).
(2026-10-02): Confirmed connector registry changes now append secret-free local change events (connector.added, connector.updated, connector.removed) to .agent-local/connector-events.jsonl, readable via read-only `connector.events` (MCP) and `connector-events` (CLI); new `connector.unregister` / `connector-unregister` previews by default and, with confirm_write, removes only registry metadata, records connector.removed, and never revokes credentials or edits client configuration. Pushing events to orchestration/Personal Executive subscribers remains open.
(2026-10-03): `connector.conflicts` (MCP) and `connector-conflicts` (CLI) now give a read-only report of duplicate or conflicting registrations: the same provider active (desired/registered/error) more than once on a surface, colliding native `server_name`s on a surface, and credential references shared across connectors (backend kind only, never the reference). It deduplicates and repairs nothing automatically; applied reconciliation remains open.
(2026-10-03): `connector.prune_stale` (MCP) and `connector-prune-stale` (CLI) now repair stale registrations: they preview by default the registrations whose surface is no longer declared in the surface registry (the reconcile plan's `unknown_surface`), and with confirm_write remove only those registration entries under the registry lock, keep the connector, and record `connector.updated` events; they never revoke credentials, edit client configuration, or contact providers.
(2026-10-03): `connector.events` (MCP) and `connector-events --after-seq` (CLI) now support incremental subscriber polling: each event carries a stable `seq`, and callers pass the previous `next_after_seq` as `after_seq` to page forward oldest-first, with `latest_seq`, `has_more`, and `cursor_reset` in the response. The feed stays read-only and secret-free; wiring a specific orchestration/Personal Executive subscriber and push delivery remain open.
(2026-10-03): `connector.provisioning_readiness` (MCP) and `connector-provisioning-readiness` (CLI) now give a read-only ready/blocked/no_action verdict per connector registration, combining the reconcile plan, credential presence and conflicts into named blockers (unknown_surface, registration_error, manual_host_setup, surface_capability_undetermined, credential_missing, credential_unchecked, native_entry_absent, native_entry_unverifiable, conflict:<kind>) with readiness and blocker counts; it applies nothing, resolves no credentials and contacts no providers. Writing native client config (still waiting on the launch-command decision), push delivery to subscribers, and applied reconciliation remain open.
(2026-10-03): `connector.set_registration_state` (MCP) and `connector-set-registration-state` (CLI) now give a preview-first enable/disable control for one connector registration: with confirm_write they switch its state between desired and disabled under the registry lock (disable from any state, re-enable only from disabled), keep server_name and other fields, and record a `connector.updated` event; registered/error/unsupported cannot be set without adapter verification, and no credentials are revoked, client configuration edited, or providers contacted. Propagating enabled/disabled state into client configuration remains part of applied reconciliation.
(2026-10-03): `integration-health` now subscribes to the connector change event feed: `connector_providers.events` reports a read-only, secret-free summary of the most recent (up to 500) connector events (latest_seq, counts of connector.added/updated/removed, last_event_at, changed connector IDs, malformed count), so health checks discover connector additions and removals without a separate poll; wiring orchestration/Personal Executive subscribers and push delivery remain open.
(2026-10-03): `connector.verify_native` (MCP) and `connector-verify-native` (CLI) now provide preview-first, config-level adapter verification: with confirm_write they promote a desired registration to registered when its requested native `server_name` is observed in an inspectable surface's client config, and return registered to desired when that entry disappears, under the registry lock with `connector.updated` events; bridge-only and disabled/error/unsupported registrations are untouched, and nothing is invoked, no provider is contacted, and no client config is edited. Live invocation verification remains open.
(2026-10-03): `connector.subscriber_poll` / `connector.subscriber_ack` (MCP) and `connector-subscriber-poll` / `connector-subscriber-ack` (CLI) add durable named subscriber cursors over the connector event feed. Poll is read-only and returns events after the stored cursor. Ack previews by default and with confirm_write stores the cursor in .agent-local/connector-event-cursors.json under the registry lock. No secrets, registry metadata, or client config are touched. Push delivery and wiring specific orchestration/Personal Executive consumers remain open.
Keyring-family credential presence checks (pending a decision on the secret_ref to keyring service/user mapping), credential value resolution, surface adapters, applying reconciliation, live provider health checks, and cross-surface verification remain open. `agent.py validate` now loads the v1 connector registry as part of
its deterministic checks; this sparse worktree omits tracked project context,
state files, and schemas, so the overall command reports them missing. The
surface registry and `integration-health` now expose a
per-client connector capability matrix for local configuration inspection and
changes, credential transfer, and Agent OS bridge availability. Hosted-client
settings are marked inaccessible to local inspection or mutation, while bridge
status remains explicitly unknown when the local checkout cannot inspect it.

Make Agent OS the canonical provider-neutral connector registry and broker for
Claude, ChatGPT, Codex, desktop clients, mobile/voice clients, and future agent
surfaces.

User requirement:
- configure a connector once and make it available automatically in every
  supported agent surface;
- a connector configured while working in Claude should become usable from
  ChatGPT and other registered clients without repeating provider setup, and
  the same should work in the opposite direction wherever the host exposes
  sufficient integration/configuration APIs;
- connector availability should follow the user's Agent OS, not remain trapped
  in the application where the connection was first created.

Architecture:
- maintain one canonical **Connector Registry** in Agent OS containing
  provider identity, capabilities, scopes, health, owning privacy domain,
  registration state, and references to local secret-store entries;
- keep credentials/tokens out of Git. Git may store only non-secret connector
  metadata and desired-state declarations; credentials remain in approved
  local/OS secret stores or provider-managed stores;
- expose connected providers behind Agent OS's stable MCP/plugin/API bridge, so
  clients can connect once to Agent OS and automatically discover newly added
  underlying capabilities through tool discovery rather than registering each
  provider independently;
- add surface adapters that inspect supported Claude/Codex/desktop MCP
  registrations and reconcile them into Agent OS desired state, then
  provision/update compatible registrations for other installed surfaces;
- add a capability matrix for cloud-hosted surfaces such as ChatGPT. When a
  host does not permit Agent OS to import/export another application's
  credentials or mutate connector settings, keep the Agent OS bridge stable
  and expose the provider through that bridge instead of duplicating secrets;
- when a connector originates in a host whose connection cannot legally or
  technically be exported, detect that limitation explicitly and request only
  the minimum one-time Agent OS authorization needed rather than pretending
  synchronization occurred;
- support bidirectional reconciliation of connector metadata, enabled/disabled
  state, capability/scopes, health, and revocation where host APIs permit it;
- prefer one Agent OS-owned provider connection shared behind policy boundaries
  over multiple vendor-specific copies of the same credentials;
- propagate connector additions/removals as events so integration health,
  orchestration, the Personal Executive, and future proactive workflows can
  immediately discover changed capabilities.

Required workflows:

configure/import connector on any supported surface
→ normalize provider + capabilities
→ store/resolve credentials in approved secret store
→ update Agent OS Connector Registry
→ reconcile all registered client surfaces
→ expose provider through stable Agent OS MCP/plugin/API
→ verify tool discovery + least-privilege access
→ report per-surface availability and any host-imposed limitation

On startup and periodically/on configuration change:

discover local/client connector state
→ compare with canonical desired state
→ deduplicate equivalent registrations
→ repair stale registrations where authorized
→ health-check provider + Agent OS bridge
→ surface conflicts, expired auth, or unsupported host behavior

Acceptance criteria:
- adding a supported connector once makes its tools discoverable from Claude,
  Codex, ChatGPT, and other registered Agent OS surfaces without separately
  entering that provider's credentials in every client;
- iCloud Mail connected to Agent OS can be searched from any surface that can
  reach the Agent OS bridge, including ChatGPT once that bridge is connected;
- connectors already configured in Claude/Codex/other inspectable local clients
  can be detected and imported/reconciled without duplicate configuration;
- connector changes are idempotent and do not create duplicate MCP servers,
  duplicate provider accounts, or conflicting registrations;
- `integration-health` reports connector-provider health separately from
  surface-to-Agent-OS reachability and shows exactly why a connector is or is
  not available in a given client;
- revoking or disabling a connector propagates to all supported surfaces and
  stale registrations are removed or disabled where authorized;
- secret material is never committed to Git, copied into prompts, or exposed to
  another client merely to achieve portability;
- host limitations are represented as explicit capability constraints rather
  than silently breaking the configure-once expectation;
- regression tests cover Claude → Agent OS → ChatGPT availability, ChatGPT/
  external-host import where APIs permit it, unsupported-host fallback through
  the Agent OS bridge, revocation, deduplication, stale registration repair,
  credential isolation, and fresh-machine recovery.

Success signal:
- the user thinks in terms of "connect this service to Agent OS" rather than
  "connect this service separately to Claude, ChatGPT, Codex, and every future
  client."

Concrete high-priority provider adapter:
- [RTEC Applicant Pipeline / Agent OS Integration](rtec-applicant-pipeline.md) —
  Fillout remains upstream through the existing Google bridge; Agent OS attaches
  to the Applicant Dashboard's normalized/restricted workflow layer, with an
  EEO/self-ID firewall and approval-gated consequential actions.

### P0.1 — Staged Workflow Orchestrator + next-prompt/model handoffs

Status: **complete** (2026-09-21). Manifest schema, stage lifecycle, persisted
run state, evidence-driven escalation, next-prompt generation, and CLI + MCP
exposure are implemented and covered by 46 regression tests.

Acceptance criteria met:
- a multi-step job pauses after any stage and resumes in another agent from
  persisted state, with no conversation history reconstructed;
- the next prompt is generated from the run record, not from chat memory;
- low-complexity stages run at `deterministic` and cost no model tokens, while
  harder stages escalate only after a declared validator fails;
- the stage completion packet is compact and carries no transcript;
- `agent-os workflow-next` answers "what do I run next?" with a ready-to-paste
  prompt and a capability recommendation.

Measured on `repository-health-sweep`: 2 of 4 stages need no model at all, and
per-stage context stays inside each stage's own budget (549/553/1167/856
tokens). Staged context totals 3125 tokens against 2536 for a single unstaged
pass — staging costs somewhat more raw context and buys model-free stages,
transcript-free resumption, and bounded per-stage packets. It is not a raw
context reduction, and the tests assert a bound rather than a saving.

Carried-forward technical debt is recorded in
`projects/personal-agent-os/roadmap/technical-debt.md`.

Immediately after universal routing, implement a first-class staged execution system for complex work.

Purpose:
- prevent one powerful model/session from carrying an entire multi-step workflow when earlier or later stages can be handled deterministically or by cheaper capability classes;
- make long jobs resumable across chats, computers, coding agents, and model providers;
- stop cleanly after bounded stages and tell the user/next agent exactly what should happen next.

Each workflow should be decomposable into machine-readable stages with fields such as:
- stage_id;
- goal;
- inputs/artifacts;
- required_context;
- preferred_execution_path;
- capability_class (deterministic, fast, balanced, reasoning, frontier);
- optional provider/model recommendation resolved at run time;
- reasoning/effort recommendation;
- allowed tools;
- budget/limits when measurable;
- validator/test;
- stop condition;
- expected outputs;
- checkpoint location;
- next_stage;
- generated next_prompt.

Stage lifecycle:

resolve workflow
→ run cheapest appropriate stage
→ validate
→ persist outputs/checkpoint
→ stop at the configured boundary
→ emit completion summary
→ emit exact next stage
→ emit recommended capability/model/effort
→ emit a ready-to-paste next prompt or machine-runnable handoff

Requirements:
- model recommendations should prefer provider-neutral capability classes; concrete model names are resolved from currently available/configured providers at execution time;
- stages must be restart-safe and idempotent where practical;
- context for each stage must be independently compiled rather than carrying the entire previous conversation forward;
- validators/tests determine whether escalation is required;
- a failed cheap stage may escalate within policy, but successful stages should not be re-run by a stronger model without reason;
- workflows packaged for coding agents may include stage manifests, prompts, compact context, artifacts, and checkpoint state;
- the orchestrator should support both manual "give me the next prompt/model" operation and later automatic execution/delegation;
- outputs should distinguish completed work, unresolved items, artifacts, validation status, and the exact next action.

Acceptance criteria:
- a multi-step project can be paused after any stage and resumed in another supported agent without reconstructing conversation history;
- the next prompt is generated from persisted stage state rather than from memory of the current chat;
- low-complexity stages can be assigned to lower capability classes while difficult stages are escalated intentionally;
- a stage completion packet is compact enough to avoid carrying full prior transcripts;
- the user can request "what do I run next?" and receive a ready-to-use prompt plus current model/capability recommendation.

Success signal:
- expensive models spend time primarily on the stages that actually require them.

### P0.2 — Selective context and profile retrieval

Status: **complete** (2026-09-21). EXEC-0.5 is implemented in
`src/agent_os/profile.py`, merged into the context compiler, exposed through
CLI and MCP, enforced by `agent.py validate`, and covered by 31 regression
tests.

Acceptance criteria met:
- a task receives relevant personal context without naming a profile file;
- unrelated profile information is excluded, and a task with no personal
  dimension retrieves nothing at all;
- retrieval is deterministic and testable, with measured token usage;
- profile facts carry provenance, confidence, sensitivity and recency, and
  remain reviewable in Git;
- tests cover relevance filtering, privacy exclusion, deduplication,
  superseded/stale facts, budgets, and diagnostics.

Measured: 105 facts indexed (93 retrievable, 12 restricted). Injecting the
profile whole would cost ~16,878 tokens; selective retrieval delivers ~293
tokens for an HR scanner task, ~332 for meal planning, ~158 for a finance
question, and 0 for an impersonal coding task.

Implement EXEC-0.5 before broad new Agent OS features.

Goals:
- stop injecting complete profiles, project histories, handoffs, or skill bodies when only a small slice is relevant;
- index canonical profile/project/memory facts by topic, domain, provenance, sensitivity, confidence, and recency;
- compile compact context packets with explicit size/token budgets;
- deduplicate overlapping facts and prefer newer/superseding canonical records;
- expose context diagnostics so agents can see what was retrieved and why without exposing hidden reasoning.

Success signal:
- common tasks receive materially smaller context packets without losing needed information.

Detailed design:
- `projects/personal-agent-os/roadmap/personal-executive.md`
- `projects/personal-agent-os/roadmap/personal-message-archive.md` — EXEC-0.5.

### P0.3 — Shared document intelligence + local persistent extraction/OCR cache

Status: **on hold here** (2026-10-04): the Agent OS side is complete and covered by consumer-contract tests; the remaining work lives in the ingester-engine repository (bounded concurrency, then page-level template reuse once the form registry has approved content) and needs a run targeting that repository. Earlier: **foundation complete; Agent OS now has tests for the page-cache lookup helpers, the cache privacy and key-exclusion rules, and the document-cache CLI commands, in addition to field-region contract coverage** (2026-10-04).
The cache/extraction foundation was implemented in `src/agent_os/documents.py` and
moved on 2026-10-01 to the Ingester Engine (`ingester_engine.cache`, shared per-user
cache, unchanged keys); this roadmap item continues there. It was
exposed through CLI and MCP, enforced by `agent.py validate`, and covered by 40
regression tests. The field-region seam is now covered from Agent OS by tests/test_field_region_contract.py (validation, cache reuse, re-OCR for a new region, count-only telemetry, persistence across cache instances, re-OCR for a different page or file hash, no cache path in results, OCR-failure handling, re-OCR when dpi/rotation change) and documented in docs/document-intelligence.md. Additional Agent OS-side tests cover the cache layer: tests/test_document_cache_lookup.py, tests/test_document_cache_privacy_contract.py, and tests/test_document_cache_cli.py. While HR-GUI branch review is complete (merged 0dbe36e); tests inside the ingester-engine repo (blocked on the deploy-key secret), approved registry content, and bounded concurrency remain open.

Delivered:
1. persistent exact-page cache keyed by content hash — **done**;
2. dependency/version-aware invalidation, so interpretation changes reuse
   OCR — **done**, and asserted structurally by test;
3. person-independent structural signatures — **done**. The sanitized form
   matcher now abstains when top registry scores are within 0.05; approved
   registry content, scanner integration, and page-level template reuse remain
   pending (the current registry is empty);
4. targeted field-region OCR — **done**. Shared `FieldRegion` validation and cached
   `extract_field_region` API are implemented, with count-only telemetry for
   region requests, OCR calls, and cache hits; Agent OS consumer contract coverage done (tests/test_field_region_contract.py, verified in docs/document-intelligence.md 'Scope actually delivered'); in-repo ingester-engine tests and HR-GUI branch review/merge remain;
5. bounded concurrency — **not started**, and correctly gated behind measuring
   the earlier steps.

Measured (40 pages, simulated OCR at 20ms/page): cold 0.65s, warm 0.14s
(4.5x repeat-run speedup, 78% avoided), classifier change 0.00s of OCR, OCR
engine upgrade correctly re-extracts.

HR-GUI is a separate repository. Its shared-cache adapter is on
`origin/main` (`cffccbb`); source-change invalidation and OCR-rotation fixes
were merged into HR-GUI `main` on 2026-10-04 (`0dbe36e`, pushed) after focused
synthetic regression tests (`b17e811`: mid-run source rewrite, rotation round-trip,
invalid rotation refusal, field-region fallback); 639 HR-GUI tests and all 63
scanner regressions pass. Its local zone
OCR now calls the shared field-region API on that branch (`91a1baf`), with the
existing local render/crop/OCR path as fallback. The shared API (`103f0b52`)
is merged into Agent OS `main` (2026-09-24); the HR-GUI integration is now on
the normal HR-GUI checkout. Zone definitions and OCR text remain local. Remaining debt is
recorded in
`projects/personal-agent-os/roadmap/technical-debt.md`.

Prioritize the reusable document-intelligence layer and HR-GUI scan optimization work.

Implementation order:
1. content-addressed exact file/page cache;
2. embedded-text extraction before OCR;
3. dependency/version-aware cache invalidation;
4. known-template/fingerprint reuse;
5. targeted field-zone OCR for validated templates;
6. bounded concurrency only after measuring the above.

Requirements:
- raw work documents, OCR text, page images, employee information, and private correction data remain workstation-local and gitignored;
- cache absence must never break correctness;
- scanner accuracy/regression tests remain authoritative;
- known-template reuse must never reuse employee-specific values.

Success signal:
- repeated scans and classifier-development passes perform progressively less OCR and less model-assisted analysis.

Detailed design:
- `projects/personal-agent-os/roadmap/usage-intelligence-adaptive-routing.md` — shared document intelligence, HR-GUI optimization, scanner learning loop.

### P0.4 — Resumable/checkpointed ingestion everywhere
Status: **on hold** (2026-10-04), awaiting operator decisions: every safe local/fixture seam is already wired to the ingestion ledger; the remaining text-message, feed and Discord adapters need (1) where to build them (ingester-engine vs agent_os.ingester_bridge), (2) each source's stable item ID, and (3) whether edited messages/updated entries are reprocessed under the same ID. Earlier: implemented in the P0.4 recovery foundation (`agent_os.recovery`), with
local compact checkpoints, Git fingerprints, cross-agent continuation, and a
generic incremental ledger. Ledger failure records now discard caller-supplied
error text to keep imported content, paths, and credentials out of runtime
metadata. Recovery checkpoints keep only validator pass/fail state, not raw
validator detail. Working-tree fingerprints hash symlink targets without
following them, so external file contents are not read. See
`docs/restart-recovery.md`.

Long-running imports and crawls must not lose progress or rescan completed material.

Apply stable IDs, fingerprints, ledgers, and checkpoints to:
- iCloud Mail backfill;
- Google Drive archive crawl;
- text-message imports;
- future Discord/content-feed imports;
- document-processing batches;
- knowledge-library ingestion.

Requirements:
- restart-safe;
- idempotent;
- deduplicated;
- explicit processed/queued/error states;
- incremental reprocessing only when content or relevant processing versions change.

Success signal:
- interruption or restart does not cause a full re-run.

Current bounded foundation (2026-09-22; moved 2026-10-01 to the Ingester Engine as
`ingester_engine.ledger`, unchanged format, imported via `agent_os.ingester_bridge`):
it provides
provider-neutral local ledgers with stable work/run/stage/item IDs, content and
processor fingerprints, deduplication, explicit item states, scalar
checkpoints, and recovery of interrupted claims. The iCloud Mail adapter,
shared document page batches, and canonical local search-index rebuild now
delegate work through that ledger. The curated local profile JSON importer now
also reuses a gitignored derived-fact cache through the same ledger, with
changed-source requeue and interrupted-claim recovery. The synthetic
Google Drive adapter now maps `(drive_scope, file_id)` identity and content
fingerprints through the ledger; messages, feeds, and other provider-specific
imports remain unwired. The local candidate-record
reader now uses a project-scoped ledger for resumable directory scans without
changing the explicit curation/promotion boundary. The local improvement-record
reader now uses the same project-scoped ledger for `IMP-*.json` scans,
preserving canonical improvement records while making status/search/capture
reads idempotent and restart-safe. Messages, feeds, and other provider-specific
imports remain unwired. The local change-record reader now
uses a separate project-scoped ledger for `CR-*.json` scans, preserving its
existing lifecycle and safe-projection behavior while making reads incremental
and restart-safe.
Mail (2026-09-23, branch `mail-multi-account`, `docs/integrations/mail.md`):
the iCloud adapter is generalized into read-only multi-account IMAP (iCloud +
EarthLink) with identity `provider/account/mailbox/UIDVALIDITY/UID`,
UIDVALIDITY rollover handling, a metadata-only overlap check instead of
trusting UIDNEXT, CONDSTORE flag updates when advertised, batched ledger
saves, logical-message/observation provenance shared with a PST archive
seam, threads, FTS5 search and a schema v1 migration.
The context compiler's project handoff reader now uses a separate
metadata-only ledger for newest-first canonical handoff scans, preserving
latest-handoff retrieval while recording interrupted scans and completed files.
The sanitized local form-registry reader now uses its own ledger item and
checkpoint, preserving the existing form-routing privacy boundary while
detecting changed registry content and recovering interrupted reads.
All currently identified safe local/fixture seams, including the synthetic
Google Drive adapter, are now covered. Workflow
run state remains intentionally outside this ledger because its existing stage
checkpoint/state machine is already canonical. The remaining P0.4 work is
text-message, feed, or future provider-specific adapter integration and
requires source identity plus changed-content semantics before implementation;
plain IMAP UID/UIDNEXT cursors remain deferred.

### P0.5 — Deterministic/cache/skill-first execution policy

Status: **complete for now** (2026-10-04). Deterministic-first selection with evidence-triggered model
fallback, the document-page cache route, and the reviewed-patch task cache (opt-in via run policy
`task_cache_enabled`, default off until hit/miss evidence justifies a default) are implemented; the skill
route is closed while every approved skill is instruction-only (a skill opts in by declaring a deterministic
command under the approved-skill rules in docs/orchestrator-os/task-cache-route.md). Reopen to flip the cache
default or when a skill declares a command.

Make the default execution preference operational, not just documented:

1. existing deterministic utility;
2. cached result;
3. approved reusable skill;
4. cheap/fast model;
5. balanced/strong model;
6. high-reasoning/frontier model when justified.

Add deterministic validators wherever possible so expensive escalation is triggered by evidence rather than habit.

The staged orchestrator in P0.1 should use this policy when selecting how each stage runs.

Current bounded implementation (2026-09-22, updated 2026-10-04): manifests may declare
`available_execution_paths`; the orchestrator deterministically selects and
persists the cheapest candidate in the economy order, while preserving the
backward-compatible single `preferred_execution_path` form. A bounded local
cache adapter now executes content-addressed document-page cache hits from the
workflow project's registered checkout and persists deterministic fallback to
the next declared route on misses; skill
execution remains caller-owned because the repository's approved skills are
instruction-only `SKILL.md` files without a reviewed deterministic invocation
interface. The staged orchestrator also supports an explicit deterministic to
model fallback after a command or task validator failure; model launches still
obey the run budget and review policy. Cache and skill routes remain outside
the orchestrator until their invocation adapters are reviewed. Task plans may
declare deterministic and model as available routes; the orchestrator chooses
the deterministic command first and preserves model as an evidence-triggered
fallback. A task cache route now exists behind run policy `task_cache_enabled`
(default off). Its key binds the normalized goal, sorted scope, in-scope base
blob hashes, validators, role and policy version. It stores only
reviewer-approved, scope-limited patches with validator evidence, and a hit
skips the worker and review only after a clean apply and passing validators,
otherwise falling back to model with a recorded miss reason (contract:
docs/orchestrator-os/task-cache-route.md). Operator decisions (2026-10-04) close the remaining items: `task_cache_enabled` stays default-off as a per-run opt-in until real-run hit/miss/fallback evidence justifies a default change (no policy version bump), and the skill route is closed as caller-owned because approved skills are instruction-only; a future skill opts in by shipping an approved deterministic command used through the deterministic route (docs/orchestrator-os/task-cache-route.md section 9). P0.5 is complete for this phase; revisit the cache default once run evidence exists.

Success signal:
- repeated structured work increasingly bypasses LLM calls.


### P0.6 — Skill/Economy Regression Test Suite
Status: implemented with a deterministic, privacy-safe fixed corpus, context
budget safeguards, workflow-route regression coverage, and synthetic A/B
comparison. See `docs/economy-regressions.md`.

Build an automated test/evaluation harness that proves the usage-saving skill layer actually saves context/usage and does not create its own bloat.

Status: **complete for the initial synthetic regression suite** (2026-09-22).

Completion evidence: skill matching now fails closed
below a default lexical relevance score of two, records that threshold in the
context packet, and has synthetic regression coverage for weak generic overlap.
An adversarial synthetic skill-count test also proves unrelated skills do not
increase selected-skill count or materially inflate the compiled packet, while
skill bodies remain unloaded by default. A representative synthetic corpus now
covers strong, project-specific, weak, and unrelated task queries through both
`skills.match` and `compile_context`. A staged workflow evaluation also proves
cheap successes are not rerun, partial unresolved work survives escalation, and
checkpoints/next prompts resume from persisted state. A synthetic economy
benchmark records baseline versus staged context tokens, model-free stage IDs,
validation parity, and bounded token overhead. An A/B fixture comparison also
records synthetic model-call/handoff avoidance and highest executed path without
calling live providers.

The four initial evaluation dimensions are covered by the focused regression
suite: selection accuracy, context-bloat resistance, staged workflow behavior,
and synthetic A/B economy comparison. Broader corpus expansion is optional
follow-up, not a reason to keep P0.6 open. The next safe roadmap stage is P1.1,
privacy-safe usage telemetry; it must keep raw traces local and record only
reviewed aggregate findings in Git.

Test four dimensions:

1. **Skill-selection accuracy**
   - maintain a fixed corpus of representative real task types;
   - assert which skills should match and which should remain dormant;
   - include SIMPLE, PLANNED, and STAGED cases;
   - test project-specific tasks such as scanner debugging, Drive crawling, iCloud import, artifact/ZIP generation, focused code fixes, and research-heavy work;
   - add a minimum relevance threshold so weak lexical overlap can produce "no sufficiently relevant skill" instead of forcing irrelevant matches.

2. **Context-bloat regression**
   - measure compiled packet characters/estimated tokens before and after skill additions;
   - assert full skill bodies remain unloaded by default;
   - assert unrelated skills do not materially increase task context;
   - stress-test discovery by adding many synthetic unrelated skills and confirming the correct skills still win;
   - enforce hard packet/token budgets and fail tests when regressions exceed configured thresholds.

3. **Workflow-behavior evaluations**
   - verify complexity triage chooses SIMPLE, PLANNED, or STAGED appropriately;
   - verify artifact reuse, targeted repository search, batching, cheap-route selection, validation/escalation, checkpointing, and next-prompt/model handoff occur only when appropriate;
   - verify successful cheap stages are not rerun with stronger models without a validation reason;
   - verify failed attempts preserve successful partial work and escalate only unresolved portions.

4. **A/B economy benchmarks**
   - run representative tasks through a baseline path and the Agent-OS economy/staged path;
   - compare estimated/actual context tokens when available, model-call count, highest capability class used, repeated file reads/OCR, retries, escalations, wall-clock duration, and validation outcome;
   - require quality/validation parity or improvement before treating usage reduction as a success;
   - permit the benchmark to conclude that a stronger/more expensive route was justified.

Initial hard safeguards:
- normal context compilation loads skill metadata only unless a skill body is explicitly required;
- no more than the configured small number of skill matches enter a context packet;
- adding unrelated skills must not materially inflate compiled context;
- packet size must remain within the requested token budget;
- a weak match should be omitted when it falls below the configured relevance threshold;
- regression fixtures must include at least one adversarial "many unrelated skills" case.

Implementation guidance:
- keep benchmark fixtures synthetic or privacy-safe;
- record deterministic measurements locally/CI where possible;
- use existing `context_measurement` output as the starting metric;
- extend tests around `skills.match`, `compile_context`, routing/triage, and staged handoff behavior rather than creating a disconnected test framework;
- add a compact economy report suitable for comparing before/after changes to skill and routing logic.

Acceptance criteria:
- a new skill cannot be considered safely integrated until selection and bloat tests pass;
- synthetic skill-count growth does not materially increase unrelated task context;
- representative tasks select expected skills and omit irrelevant ones;
- A/B benchmarks can demonstrate whether staged/skill routing reduces work while preserving validator/test success;
- CI/local validation fails on configured economy regressions.

Success signal:
- Agent OS can prove that adding more skills improves reuse/routing without steadily increasing prompt size or unnecessary model work.


---

## P1 — Usage telemetry and adaptive routing

Build after or alongside the P0 primitives so optimization is measured against real workflows.

### P1.1 — Privacy-safe usage telemetry

Current bounded implementation (2026-09-23): orchestrated runs record
per-run efficiency telemetry with normalized provider token usage (P1.2C), and
`agent-os orchestrate usage-report` / the GUI's "Model usage across all runs"
aggregate it across runs by role, tier, provider/model and origin, with
coverage and overhead share (P1.2D, `docs/simple-mode.md`). (2026-10-04): staged
workflows now record opt-in local telemetry for every completion path
(deterministic, cache hit, agent-reported model stage via complete_stage)
when the caller passes a `telemetry_store`; `complete_stage` also records
caller-reported token usage and provider/model labels. `telemetry-report`
reports token totals and unknown counts and supports opt-in
`--group-by project|category` (docs/staged-workflows.md). Still open: a
`--telemetry-path` option on the `workflow-run`/`workflow-complete` CLI commands
(today telemetry is enabled from Python only), chat-session telemetry, and live
provider usage adapters.
`src/agent_os/telemetry.py`
defines a strict metadata-only event schema and append-only JSONL store under
the gitignored `.agent-local/telemetry` tree. Synthetic tests prove compact
labels/counts round-trip, canonical repository paths are rejected, and raw
prompt/document/secret-like fields and free-form labels fail closed. Provider
usage adapters and live integrations remain future slices. Its count-only
aggregate report covers execution paths and validator outcomes without exposing
per-event records; the deterministic fixture workflow can opt into one local
event per executed stage without changing its state machine. Production
workflow/provider integrations remain future slices. The local
`telemetry-report --path <events.jsonl>` command exposes only those aggregate
counts; unavailable metrics are never fabricated.

Record, when exposed:
- task/project/category;
- provider/model/capability class;
- input/cached/reasoning/output tokens;
- duration and retries;
- cache/skill/deterministic path used;
- files/pages/items processed as counts;
- validator/test outcome;
- escalation count;
- correction/override.

Keep raw telemetry local. Git may contain only reviewed aggregate findings/policies.

Initial reports should answer:
- which workflows consume the most model usage;
- which repeat work that should be cached;
- where context is oversized;
- where a strong model is used for deterministic work;
- where retries/escalations are concentrated.

### P1.2 — Adaptive router

Status: **deterministic foundation complete** (2026-09-22). Provider-neutral
capability classes, cheapest-path selection, persisted fallback, validator-
driven one-rung escalation, bounded escalation, and observable route
explanations are implemented and regression-covered. No concrete deterministic
gap remains in the current scope; provider/model delegation remains outside
this foundation and P1.3.

Current deterministic slice (2026-09-22): workflow packets expose the
provider-neutral selected execution path, declared candidates, and a compact
route explanation. Provider/model delegation remains outside this slice.

The next safe deterministic roadmap stage is P2.1, Automation Miner.

Implement provider-neutral capability classes and validator-driven escalation.

The router should:
- pre-route before expensive work begins;
- delegate bounded subtasks when useful;
- select the cheapest path likely to satisfy validation;
- escalate on concrete failure/ambiguity signals;
- record an observable route explanation;
- never claim to hot-swap the model already running inside ChatGPT/Claude.

### P1.2A — Multi-agent coding orchestrator + control GUI

Status: **implemented, first release** (2026-09-22, merged to `main`; see
`docs/multi-agent-orchestrator.md`). Implemented:
- provider-neutral engine, with Claude Code and Codex CLI adapters whose flags
  were verified against the installed `--help`;
- a registry-driven router covering model and effort, user overrides and
  per-node failover;
- per-worker worktrees with serialization of overlapping scopes;
- validator-gated, review-gated integration;
- structured cross-review with repair and re-review;
- approval gates;
- bounded retry and escalation;
- restart reconciliation;
- Auto Continue;
- CLI and MCP surfaces, plus a loopback GUI.

Verified by 64 synthetic-provider tests and one live run (Claude Code
implements, Codex reviews) that reached COMPLETE. Remaining limits:
- Auto Continue runs only while a driver process is alive;
- routing does not yet learn from cross-run telemetry;
- the GUI is dependency-free web UI rather than Tauri, because no Rust
  toolchain is installed.

**P1.2B — token-economy routing (2026-09-22, branch
`p1.2b-orchestrator-routing`).** Changes:
- **Routing:** providers refresh their models from local discovery (the Codex
  model catalog, Claude tier aliases). The router picks the cheapest provider
  per class using registry `costs`, then the least loaded one.
- **Concurrency:** `tier_concurrency` caps expensive classes while cheap `fast`
  work fans out (Codex up to 6 workers, `max_parallel_editors` 6).
- **Planning:** the planner is told to cut goals into small, verifiable
  `fast` batches with targeted tests and optional escalation ladders.
  Planner-proposed commands must match approved patterns and run without a
  shell.
- **Escalation:** failures raise effort first, then move one class up.
  Repairs of minor review findings drop back to the planned class.
- **Review:** cross-provider review is mandatory, and reviewers check for
  waste, dead code and efficiency.
- **Durability:** short Windows-safe worktree paths plus `core.longpaths`,
  fixing the stuck run that failed with "Filename too long". A tick that
  raises still saves its progress. Workers are reattached after a driver
  restart, and MCP/GUI-created Auto Continue runs get a detached background
  driver.

**P1.2C — Simple Mode, Continue Roadmap, efficiency telemetry (2026-09-22).**
See `docs/simple-mode.md`. Changes:
- **Simple Mode GUI (default):** Continue Roadmap, Tell Me What To Press,
  plain-English steps/agents/activity, beginner-friendly problem cards with
  Advanced Details, immediate click acknowledgement (measured 6-7 ms).
- **Continue Roadmap / campaigns:** deterministic roadmap scan, resume of
  unfinished runs, skip of stages with another agent's unmerged branch,
  stage-only goal excerpt, landing behind Approve Commit, Auto Continue Until
  Done with repeat/run-count guards.
- **Telemetry:** per-run `telemetry.jsonl` + `transcript.log`; routing
  decisions with reasons; exact/estimated/unavailable token accounting.
  Fixed: Claude cache tokens were dropped (a 1,725,628-input-token planner call
  would have been recorded as 38).
- **Economy:** test results reused for identical code, no review of no-change
  work, loop guards; benchmark `agent-os orchestrate benchmark [--live]`.
- **Measured finding:** in a live run, the prompts Orchestrator wrote were
  ~939 tokens while the two agent CLIs consumed 162,540 input tokens (99.4%
  their own instructions, tools and exploration). Prompt-level context
  selection is therefore a small lever; the next economy work is per-call
  CLI overhead and avoiding calls (see P2.3).

**P1.2D — per-call CLI overhead (2026-09-23).** Adapters now send lean
worker invocations: Claude Code with a 6-tool set and skills disabled, Codex
with `--ignore-user-config` (carrying over `windows.sandbox`). Measured with
`agent-os orchestrate overhead`: fixed cost per Claude call 25,177 → 14,331
input tokens, per Codex call 19,007 → 14,022 (uncached ~15k → 3k). Live A/B on
a small code change (3 runs each, delivery verified): median task input
161,847 → 100,513 tokens; review calls ~84.6k → ~41.8k. Also fixed: a worker
reporting "done" with no changes was accepted (now a failed attempt unless it
reports `already_done`).

Additional hardening (2026-09-23): worker subprocesses carry an internal marker,
and orchestrator control entry points reject nested run/control calls before
they touch shared Git state. A direct live CLI model trial delivered with the
exact `codex` / `gpt-6-luna` / `fast` selection and completed without failures
(66,494 input and 789 output tokens). The connected MCP server's runtime
restart and through-MCP smoke remain unverified.

The original scope below is kept for reference.

Create an Agent OS control plane that can coordinate Claude Code, Codex CLI, and
future coding agents as independent workers on one larger task.

Core behavior:
- decompose a task into a dependency-aware stage/DAG plan and assign bounded
  roles such as planner, implementer, test author, adversarial reviewer, and
  integrator;
- launch agents through provider-specific CLI adapters while keeping the
  orchestrator core provider-neutral;
- resolve capability class -> provider -> concrete model -> reasoning/effort at
  launch time from a machine-local model registry;
- pass the selected model and effort to each CLI automatically, while exposing
  a user override before or during a run;
- use separate Git branches/worktrees for concurrently editing agents so one
  agent cannot silently overwrite another agent's half-finished work;
- reuse `work-check`, `work-claim`, notes/inbox, staged workflow checkpoints,
  compact context compilation, and validation before adding duplicate
  coordination machinery;
- support deliberate cross-review: Claude can review Codex work, Codex can
  review Claude work, findings are structured, and implementation changes
  require validation after review;
- preserve successful partial work and hand it to another provider if a quota,
  provider, or session ends instead of restarting the task.

Automatic model routing:
- workflow stages request provider-neutral capability classes and effort, not
  hard-coded vendor model names;
- a model registry maps capability classes to the currently recommended local
  CLI/provider model identifiers and supported effort controls;
- selection considers declared task type, validator history, context size,
  provider availability, configured usage/cost policy, prior success/failure
  telemetry, and explicit user preference;
- automatic routing must be explainable in compact metadata and must never
  silently rewrite the canonical recommendation registry from one anecdotal
  run;
- model names live in data/configuration, not in provider-neutral workflow code,
  so new Claude/Codex models can be adopted without rewriting manifests.

Auto-continue-until-done mode:
- add an explicit `auto_continue` run policy that repeatedly advances runnable
  stages, validates outputs, checkpoints state, launches the next approved
  agent/model, handles bounded retries/escalations, and continues until the
  task's completion criteria pass;
- do not require the user to paste the next prompt between normal safe stages;
- resume from persisted run state after GUI restart, CLI crash, quota cutoff, or
  provider switch;
- stop and ask for approval only at declared approval gates such as destructive
  actions, credential/secret entry, consequential external writes, policy-
  restricted operations, unresolved merge/conflict decisions, exhausted safety/
  cost limits, or ambiguity that would materially change the requested outcome;
- a provider/model failure is normally a routing event, not a reason to abandon
  the whole run: preserve the checkpoint and try an allowed alternate route;
- include a visible Pause/Stop/Kill control and never claim background execution
  once the local orchestrator process is no longer running.

GUI requirements:
- one-click **Start Recommended** launches the generated plan with automatic
  provider/model/effort selection;
- show each agent, role, branch/worktree, current stage, selected model/effort,
  status, validator result, usage when available, cross-review findings, and
  unresolved blockers;
- provide per-agent model/provider overrides and an overall economy/quality
  preference without forcing users to know CLI flags;
- expose Auto Continue, Pause, Resume, Retry, Reassign, Review Again, and
  Approve Merge controls;
- the GUI is a client of the Agent OS orchestration APIs/state machine, not the
  place where orchestration policy lives, so CLI/MCP/headless use remains
  possible.

Implementation constraints:
- never run two editing agents in the same worktree;
- do not auto-merge merely because both agents report success; declared tests,
  validators, and review gates remain authoritative;
- default to deterministic/local work before model calls and avoid using a
  frontier model as a planner for trivial routing decisions;
- keep raw prompts/transcripts out of canonical Git state; persist compact
  structured stage state, outputs, decisions, review findings, and handoffs;
- record provider/model identifiers in telemetry only where permitted and keep
  sensitive/raw traces local;
- preserve provider neutrality in core orchestration and isolate CLI syntax in
  adapters.

Acceptance criteria:
- one task can assign non-overlapping work to Claude Code and Codex
  concurrently in isolated worktrees and later integrate the validated results;
- the orchestrator can automatically launch the recommended concrete model and
  effort for both CLIs without manual `/model` interaction;
- a user override takes effect without editing workflow manifests;
- each agent can review the other's diff through a structured review stage;
- killing/restarting the GUI or losing one provider does not lose completed
  stage state;
- with `auto_continue` enabled, a fixture workflow proceeds across multiple
  model stages without manual next-prompt copy/paste and stops only when
  complete, blocked by a declared gate, or explicitly paused/stopped;
- regression tests prove worktree isolation, model-resolution fallback,
  validation-gated continuation, bounded escalation, provider handoff, and
  no-auto-merge-on-self-reported-success.

Success signal:
- the user can submit a substantial coding goal once, select **Start
  Recommended + Auto Continue**, and Agent OS coordinates the cheapest suitable
  Claude/Codex workers, cross-checks their work, preserves checkpoints, and
  drives the task to validated completion with human intervention only at
  meaningful approval gates.

### P1.3 — Optional API delegation

Only after local/deterministic/context savings are functioning.

Use OpenAI/Anthropic APIs for bounded Agent-OS-owned subtasks when doing so is advantageous. Treat API spend and host-plan usage as separate budgets. Never require both providers.

---

## P2 — Turn repeated usage into reusable machinery

### P2.1 — Automation Miner

Status: **deterministic foundation complete** (2026-09-22).

Completion evidence: five repository-evidenced repeated deterministic seams were
extracted into normal reusable code with synthetic or existing regression
coverage: local-path privacy checks, text normalization, UTC ISO timestamps,
project collection paths, and shared record-import counters. The changes keep
caller-specific policies and interfaces intact and do not infer automation from
unvalidated behavior. Larger repeated import-loop structures remain outside
this bounded foundation because extracting them would require an architectural
design decision.

Prioritize normal code for repeated deterministic tasks such as:
- hashing/fingerprinting;
- normalization;
- parsing;
- naming;
- schema validation;
- repository indexing;
- exact/regex extraction;
- straightforward file transformations.

### P2.2 — Skill Miner

Status: **deferred** pending a reviewed deterministic skill-runner contract and
validated replay traces. Canonical approved skills remain instruction-only
`SKILL.md` files, so no executable skill automation is inferred here.

Detect repeated model/tool workflows and create candidate reusable skills.

Lifecycle:
observed pattern → candidate → replay/evaluation → review → approved/rejected.

No generated skill may silently self-promote.

### P2.3 — Prompt/context optimization

Current bounded implementation (2026-09-23): the orchestrator planner now gets
a local goal-focused repository map (with companion files), an exploration
budget, medium effort, tool-restricted read-only mode and an explicit working
directory; Continue Roadmap goals carry only stage-relevant handoff items.
Measured with `agent-os orchestrate planner-bench` on a real goal: mean planner
input 507k -> 253k tokens, list cost $0.54 -> $0.26, time halved, plan
completeness unchanged (`docs/simple-mode.md`, "Planner context"). Retrieval
for implementers/reviewers, handoff compaction beyond filtering, and
telemetry-driven capability selection remain open.

Next safe deterministic stage: begin with synthetic prompt/context measurement
over the existing compiler, skill-selection, telemetry, and handoff fixtures;
do not require live providers, models, or raw traces.

Use telemetry and corrections to improve:
- retrieval queries;
- context packet composition;
- handoff compactness;
- prompt templates;
- validation;
- model capability selection.

Success signal:
- future runs of known task types consume less context/reasoning while retaining or improving validation results.

---

## P3 — Executive Core

Once the economy layer is dependable, build the core personal-executive features on top of it.

Order:
1. EXEC-0 schemas/contracts;
2. Event Bus;
3. EXEC-1 Next Action Engine;
4. basic Executive Queue;
5. explainability and provenance.

Every executive action should use selective retrieval and the adaptive execution path rather than loading broad context by default.

Detailed design:
- `projects/personal-agent-os/roadmap/personal-executive.md`.

---

## P4 — Capture, memory refinement, and Rescue Mode

Implement:
- EXEC-2 Knowledge-Gap / Interview Engine;
- EXEC-3 Brain Dump Processor;
- EXEC-8 Rescue Mode;
- candidate-memory/profile update flow;
- compact project-resumption packets.

Goal:
make it cheap and easy to recover forgotten commitments, project state, and one concrete next action without re-explaining history.

---

## P5 — Attention, delegation, and daily brief

Implement:
- EXEC-4 Executive Prioritizer;
- EXEC-5 Attention Manager;
- EXEC-6 Delegation Engine;
- EXEC-7 Daily Executive Brief;
- EXEC-9 Outcome Learning.

Outcome learning should feed P1/P2 so the system learns both **what helps the user** and **what execution path accomplishes it economically**.

---

## P6 — Life and communication integrations

Build on the same incremental/checkpointed local ingestion foundation.

Order:
1. finish/solidify iCloud Mail ingestion and MCP/Agent-OS bridge;
2. EXEC-11 Communication Intelligence;
3. calendar intelligence;
4. Personal Message Archive / Text Intelligence (`projects/personal-agent-os/roadmap/personal-message-archive.md`) — free/local iPhone/iMessage/SMS/RCS ingestion, SQLite/FTS5 retrieval, incremental refresh, and evidence-backed profile/commitment/project/relationship integration;
5. Discord authorized archive/API ingestion;
6. Universal Following Feed core;
7. additional content adapters.

Raw personal communications remain local by default. Durable Git state receives sanitized derived facts, schemas, subscriptions, routing rules, and approved memories—not credentials or raw archives.

---

## P7 — Proactivity and voice

Implement after the event, retrieval, routing, and attention layers are mature:
- EXEC-12 Proactive Executive;
- EXEC-13 Voice/Siri gateway.

Proactivity should batch low-value events and avoid model calls merely to decide that nothing needs to happen when deterministic rules can do so.

---

## P8 — Controlled autonomy

Implement EXEC-14 only after sufficient outcome history, auditing, idempotency, approval policy, and kill-switch support exist.

Autonomy should reduce user labor, not create uncontrolled background usage. Per-action budgets and execution policies should apply.

---

## P9 — Knowledge libraries and creative intelligence

Lower implementation priority than the economy/executive foundation, but design them to reuse it.

### Reusable Knowledge Library subsystem

Create a generic evidence/provenance-backed library architecture that can support:
- Elder Scrolls Lore Library as the first major implementation;
- UESP and Imperial Library ingestion;
- later direct game-data extraction;
- structured entities/relationships/claims;
- contradictions and unreliable-source handling;
- BM25/vector or other hybrid retrieval;
- project-specific canon overlays;
- MCP/API access such as search/get entity/verify claim/find contradictions.

It must use incremental ingestion, persistent local indexes, selective retrieval, and compact evidence packets so large libraries do not become prompt bloat.

### EXEC-15 — Lorekeeper / Creative Intelligence

Dream Eater and other writing projects should reuse the same selective/evidence-backed architecture for lore, provenance, canon state, contradictions, wiki generation, knowledge-gap questions, critique, and eventual live-writing observation.

---

## Candidate roadmap initiatives

The following durable themes have surfaced but are not yet ordered in the
current engineering queue. They should be scoped and prioritized through the
existing roadmap process; recording them here does not promote them above the
active foundation work.

### Relationship Graph + Unified Personal Event Timeline

Extend per-person dossiers into a provenance-backed graph connecting the user,
people, organizations, projects, places, conversations, and events. Resolve
personal and cross-system events into a timeline with participants, dates,
identity confidence, and source provenance. Support relationship history,
interaction patterns, introductions, and queries such as "how do I know this
person?" Raw source material stays within its owning privacy boundary.

### Universal Capture Status + Intake Reliability

Give browser and other capture surfaces a read path into Agent OS so they can
show whether an item is already known, watched, saved, ingested, rejected, or
archived. Make intake observable end to end with acknowledgements and states
from capture through classification and promotion, plus deduplication,
retry/error reporting, and reconciliation when a capture is missing downstream.

### Transactional Shopping

Capture Amazon items individually and support importing selected items into a
cart. Prepare carts and checkout details as reviewable drafts; cart changes and
purchase submission remain behind explicit user approval. Preserve item-level
identity, price/source provenance, and execution status for safe retries.

### Vehicle + OBD-II Intelligence

Add a vehicle-data capability for authorized OBD-II and related maintenance
data, with vehicle and sensor identity, timestamped readings, diagnostic-code
history, provenance, and useful maintenance/event timelines. Keep device access
permissioned and separate observed data from inferred diagnoses or actions.

### Personal Communications + Mobile Ingestion

Handle oversized phone-backup parsing through bounded, restart-safe extraction
and indexing. Add iOS/mobile capture paths and permissioned Messages/iCloud-style
communications bridges that feed the local personal archive and shared
timeline. Keep raw messages and backup contents local by default; expose only
approved, provenance-backed derived facts across project boundaries.

### Permissioned Cross-Device Computer + Remote Control

Keep computer interaction across devices as a future candidate capability,
not a confirmed high-priority requirement. If pursued, define explicit device
enrollment, scoped user-granted permissions, visible session state, auditable
actions, and approval gates for consequential operations before enabling
remote viewing or control.

### Project-Specific Importers

Keep Cosmere, Elder Scrolls/TES, and HR importer implementation work in their
respective project roadmaps. Promote only genuinely reusable ingestion
architecture or privacy controls into this global Agent OS roadmap.

---

## Current engineering queue

Unless an urgent correctness/privacy bug or explicitly promoted user request intervenes, coding agents should pull work in this order:

1. universal Agent OS preflight/routing for supported ChatGPT chats, Work projects, coding agents, and connected agent surfaces;
2. integration-health/fallback bridge so unsupported or partially supported clients still produce compact handoffs/candidate updates;
3. staged workflow manifests, checkpoints, validators, stage-completion packets, and generated next-prompt + capability/model/effort recommendations;
4. selective profile/context retrieval with measurable context-size diagnostics;
5. exact page/file extraction + OCR cache and embedded-text-first document path;
6. dependency-aware cache invalidation and no-cache regression tests;
7. generalized checkpoint/deduplication utilities for imports/crawls, including iCloud backfill;
8. deterministic/cache/skill-first execution dispatcher used by the staged orchestrator;
9. skill/economy regression suite: relevance threshold, selection corpus, bloat stress tests, workflow evals, and A/B economy benchmarks;
10. local privacy-safe usage telemetry and usage report;
11. adaptive routing + validator-driven escalation;
12. multi-agent coding orchestrator + control GUI: isolated worktrees, automatic CLI model/effort routing, cross-review, resumable provider handoff, and auto-continue-until-done;
13. automation miner;
14. skill miner + replay/evaluation;
15. Executive Event Bus / schemas / Next Action Engine;
16. capture + Rescue Mode;
17. communication/calendar intelligence + Personal Message Archive / Text Intelligence (MSG-0 through MSG-10);
18. proactivity/voice;
19. controlled autonomy;
20. reusable Knowledge Library / Elder Scrolls implementation;
21. mature Lorekeeper/live-writing systems.

## Gate for adding new features

Before implementing a major new model-driven feature, answer:

- Can existing deterministic code solve part of it?
- Can prior results be cached/reused?
- Can the work resume from checkpoints?
- Can context be retrieved selectively?
- Can it use an approved skill?
- How will usage be measured?
- What validates a cheap route before escalation?
- Can this be broken into bounded stages with cheaper capability classes for some stages?
- Does every long stage emit a resumable checkpoint and exact next-step handoff?
- Can independent agents use isolated worktrees and structured cross-review instead of racing in one checkout?
- Can safe stages auto-continue from persisted state while still stopping at meaningful approval gates?
- Will this create recurring model calls that should instead be event/rule driven?

If these questions have no satisfactory answer, improve the economy layer first.

## Related roadmaps

- `projects/personal-agent-os/roadmap/usage-intelligence-adaptive-routing.md`
- `projects/personal-agent-os/roadmap/personal-executive.md`

Design principle:

> **Make the agent cheaper to operate before making it do more.**


## Operator-priority: Model Infrastructure Manager / Compute Broker

**Priority: HIGH — requested 2026-09-29.** Canonical detailed specification:
[model-infrastructure-manager.md](model-infrastructure-manager.md) (IMP-0015).

This is the provider-neutral, plug-and-play model and cloud-compute layer for
Orchestrator OS. It covers automatic model research/benchmarking and intelligent
routing across subscription/API/open-weight/abliterated models; RunPod-first but
multi-provider compute provisioning; local secret management; quote/budget gates;
image generation and image/ML/LoRA training; voice/audio/ASR/TTS and future voice
training/adaptation; artifact/checkpoint persistence; and continuous discovery of
new models/providers. The current Orchestrator status marks this as the active
operator-requested next action. Paid compute remains budget/approval gated.

**2026-09-30 expansion:** IMP-0015 now includes a high-priority, measurement-first
third-party optimization track for model swapping, delegation, and GPU/runtime
efficiency: SkyPilot + a native RunPod fast path; TensorZero; PydanticAI-style
isolated subagent delegation; AgentScope team/router patterns; RouteLLM-style
calibrated escalation; LiteLLM as borrow/optional isolated adapter; vLLM vs
SGLang runtime A/B testing; LMCache cache reuse; and AIBrix/llm-d when
multi-replica or multi-GPU scale makes them worthwhile. Promote integrations
only when Agent OS EVR/CAP evidence shows noninferior validation and material
improvement in cost per verified successful task, utilization, reliability,
latency, or useful development throughput.

**2026-10-01 ASAP expansion — OpenRouter free-compute maximization:** before
spending substantial effort or money on additional paid inference capacity,
implement the FreeComputeBroker slice in the detailed roadmap. Dynamically
discover current OpenRouter free models, empirically specialize them by task
family, route verifiable low-risk work free-first, fan out disposable free
workers where validation is cheap, and use otherwise-expiring free quota for
useful checkpointable backfill. Track useful progress per free request,
validator/review acceptance, retries, escalations, paid fallbacks avoided, and
estimated paid cost avoided.

Also implement read-only OpenRouter account/quota/credit awareness. Current
provider guidance verified 2026-10-01 says adding at least USD 10 in credits
raises the free-model daily allowance from roughly 50 to roughly 1,000 requests
while retaining a 20 RPM limit; failed requests may consume allowance. Treat
those figures as versioned provider policy, not constants. Detect the actual
account/quota state and alert the operator if a top-up is genuinely required to
obtain/maintain the higher free allowance. Do **not** equate a remaining balance
below USD 10 with needing a top-up unless current provider policy/account state
supports that conclusion, and never purchase credits or enable auto-recharge
without explicit approval. This slice is **ASAP within IMP-0015** and may proceed
independently of later paid RunPod/runtime experiments using existing router,
telemetry, CAP/EVR, validation, budget, and Research Radar primitives.


## Operator-priority: Context Efficiency & Token Amplification

**Priority: HIGH — requested 2026-09-29.** Canonical specification:
[context-efficiency-token-amplification.md](context-efficiency-token-amplification.md) (IMP-0018).

Measure cumulative context growth across long-running and multi-agent workflows,
including repeated history, tool-output retention, worker fan-out, retries,
reviews, cache behavior, and checkpoint/resume. Establish deterministic baselines
first. Promote only context-retrieval, deduplication, compaction, caching, or
worker-scoping changes that reduce total tokens/cost/latency while preserving
noninferior validation and provenance. Existing EVR-0013 / DEC-0018 results
(~68% lower token use and latency for focused delegate attachments at equal
accuracy) make this a high-value area for immediate testing.


## Operator-priority: Episodic Agent Rotation

**Priority: HIGH experimental track — requested 2026-09-29.** Canonical
specification: [episodic-agent-rotation.md](episodic-agent-rotation.md)
(IMP-0019).

Test whether ending long-lived workers at semantic boundaries and starting
fresh task-scoped workers can reduce cumulative context processing. Measure the
full tradeoff: context avoided versus worker bootstrap, structured-handoff,
retrieval, rediscovery, retries, reviews, and coordination. Begin with a shadow
rotation advisor and synthetic/replay benchmarks. Promote automatic rotation
only when total cost per validated completion improves with noninferior quality.
Explicitly identify the point where additional worker rotation produces
diminishing returns.


## Operator-priority: Hermes Agent integration

**Priority: HIGH — requested 2026-10-01.** Evaluation:
[hermes-agent-evaluation.md](../research/hermes-agent-evaluation.md) (IMP-0020,
PA-hermes-agent).

Run Hermes Agent as the executive front door (messaging gateway, scheduled
jobs including no-agent jobs, voice) and as an optional any-model orchestrator
worker, with Agent OS canonical through MCP and an Agent OS memory-provider
plugin. Port its skill-curator lifecycle and fallback wait-or-switch threshold;
borrow its prompt-cache and footprint rules. Do not adopt its multi-agent board
as a runtime: the orchestrator's worktree, validator and review gates stay.
Phases H1-H6 each carry their own test; promotion follows the usual
noninferior-validation rule.
