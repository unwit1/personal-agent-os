# OpenMuse Source-Reuse Inventory and Subsumption Audit

Date: 2026-10-15
Scope: candidate upstreams for Unified Life Hub, not a claim of completed implementation.
Parent: ../roadmap/unified-life-hub-openmuse-integration.md
Verification at this checkpoint: repository READMEs and GitHub directory trees were inspected; **individual upstream implementation files, test bodies, exact SHAs, compatibility and security properties must still be audited by the implementing agent before any source is copied**. Directory presence does not prove production readiness.

## Mandatory first rule

Use the repository's existing prior-art workflow: read ../research/prior-art/README.md, run the lookup/queries, record decisions, borrow **code and tests** rather than rewrite, and compare local Agent OS modules before introducing replacements. Existing Agent OS interfaces and its Git/Knowledge Engine/Executive/Orchestrator authority are not replaced. Prioritize smallest reusable upstream source slice that works with the existing Python/JS architecture; don't create a giant dependency tree just to display a chat box.

The operator explicitly asks for personal-use reuse-first development. Keep source/provenance and notices when importing code; do not spend the main research budget on hypothetical distribution. No proprietary API/project key should become a mandatory foundation. Use synthetic data before real mail, HR or financial accounts.

## Four upstreams, exact first files/directories to open

### 1. CopilotKit OpenMuse — https://github.com/CopilotKit/openmuse

Known README/structure: MIT alpha; apps/mobile shared iOS/Android/web UI; apps/server task runtime; apps/worker Playwright; apps/computer optional Linux workspace; packages/domain types, packages/integrations and packages/backends. CopilotKit Intelligence currently manages hosted threads; avoid its hosted persistence as the canonical Agent OS store.

Source entrypoints directly confirmed in the GitHub tree:
- apps/server/src/{agent.ts,app.ts,actions.ts,auth.ts,db.ts,rate-limit.ts,worker-entry.ts}
- apps/server/src/{browser.ts,browser-console.ts,computer.ts,computer-tools.ts,computer-routes.ts,workspace.ts,files.ts}
- apps/server/src/engine/ [read task and event lifecycle, cancellation, receipts]
- apps/worker/{src,tests,Dockerfile,README.md}
- apps/computer/, apps/mobile/, packages/{domain,integrations,backends}

Candidate imports in order:
1. AG-UI event types/transforms + tests → existing Executive event_bus + Orchestrator stream projection (not independent persistence).
2. Headless chat/run plan/rich card UX and PDF/browser console → reuse existing gui and add responsive clients.
3. Browser Playwright worker and profile/session takeover → compare existing browser_control first; keep optional worker service.
4. Bounded Linux sandbox + command/file receipts → integrate via Orchestrator capability adapters; no unrestricted terminal.

Before BORROW: inspect tests, Node runtime requirement, CopilotKit backend coupling, auth/request boundary, cancellation races, streaming retry and whether components work with a simple Agent OS API. Reject or wrap anything requiring permanent hosted thread authority.

### 2. nanoMuse — https://github.com/nano-muse/nanoMuse

Known structure: Python agent runtime, desktop harness, cloud relay and modified OpenMinis Android app; GPL-3.0-or-later and upstream NOTICE files; current README distinguishes shipped components from roadmap. In its own product the cloud relay is optional; device permissions/cross-network behavior need actual validation.

Source entrypoints directly confirmed:
- nanomuse/hub/{client.py,service.py,actions.py,profile.py} — device coordination
- nanomuse/sentinel/{gate.py,grants.py,policy.py,audit.py} — action gating
- nanomuse/computer/{hands.py,link.py,operator.py,screen.py} — desktop control
- nanomuse/{background.py,runtime.py,nudges.py,sandbox.py}
- nanomuse/{goals,reminders,triggers,memory,phone,bridge,channels,cloud,sync,skills,vault}/
- cloud/, web/, harness/dsh-nanomuse/, harness/desktop/, android/ — verify specific implementation files when needed

Candidate imports in order:
1. Device enrollment, heartbeat/capabilities/dispatch/resume envelopes → Agent OS device mesh, without creating another permanent agent loop.
2. Action "API/MCP/CLI → browser → screen" fallback ladder → existing tool selection, with explicit last-resort GUI permissions.
3. Desktop/phone link, queue and delivery receipts → control Agent OS run from phone, bounded by device enrollment.
4. Goals/reminders/feeds and editable memory UX → **views** over Agent OS canonical Executive/Knowledge Engine state, not copied memory files or separate diary.
5. Native accessibility worker only after user consent, threat model and fixture tests; do not make invasive screen capture a default.

Before BORROW: verify retry/idempotency, encryption, Android accessibility privilege and terms, device revocation, offline queue expiry, optional cloud relay trust, network requirements, desktop startup and update mechanism. Do not import all of OpenMinis as the main Python runtime.

### 3. tahodev/OpenMuse — https://github.com/tahodev/openmuse

Known structure: MIT alpha, src/openmuse, examples, docs, tests; source claims exact one-time approvals, secure secrets, bounded workers and keyed audit; README warns independent production security audit still pending.

Tests confirmed in directory listing, highest value:
- tests/{test_approval_service.py,test_approvals.py,test_approval_app.py,test_argument_validation.py}
- tests/{test_audit_verify.py,test_keyed_audit.py,test_audit_anchor.py,test_checkpoint_publisher.py}
- tests/{test_secret_service.py,test_keyring_keys.py,test_broker.py}
- tests/{test_fetch_url_security.py,test_container_worker.py,test_isolated_worker.py,test_bounded_process.py,test_path_race.py}
- tests/{test_scheduler.py,test_subagents.py,test_host_events_and_streams.py,test_safety_capabilities.py}

Candidate imports in order:
1. Atomic single-use approval token tied to canonical tool+argument digest + caller/policy/TTL. Import relevant tests FIRST and prove they reject hostile inputs.
2. Secret broker separation and typed action argument validation with policy checks before execution.
3. Redacted keyed hash-chain audit and independent verification/checkpoint code.
4. Cron's atomic claims and bounded process worker *only* if existing Agent OS/Hermes cannot do the same.

Before BORROW: read actual security boundary implementation and tests for concurrency, persistent nonce consumption, key rotation, log truncation and rollback, process isolation, SSRF with redirects/private IPs and TOCTOU. Never assume that copying security snippets alone yields a secure deployment.

### 4. diggerhq/OpenMuse — https://github.com/diggerhq/openmuse

Known structure: TanStack Start and OpenComputer Serverless Agents; separate project topics with editable notes and cloud computers, return path into main conversation; hosted service dependency would not be canonical.

Source tree confirmed:
- src/lib/{topics,return-path,conversation,events,store,state,memory,auth}/
- src/lib/{oc,owner.ts,transcript.ts}
- src/{components,routes,hooks}/, opencomputer/, e2e/, test/

Candidate imports in order:
1. Per-topic UX, source-linked notes, run-summary return path and handoff/rejoin tests.
2. Durable delegated-task status/lease/error contracts that are compatible with current Orchestrator, not a new agent scheduler.
3. OpenComputer adapter as optional provider if measured cheaper/reliable vs Agent OS worker; avoid vendor-locked canonical task storage.

Before BORROW: inspect agent lifecycle, recovery after browser close, server restart, cloud worker teardown, authentication, retention and task/workspace isolation. Prefer adapting small view components and receipts rather than deploying its entire stack.

## Local Agent OS reuse crosswalk (inspect implementation and tests next)

| Desired feature | Existing home to audit first | Upstream donor | Reuse decision gate |
| --- | --- | --- | --- |
| Event streaming, progress, active runs | src/agent_os/executive/event_bus.py; src/agent_os/orchestrator/{trace,server,engine}.py | CopilotKit AG-UI | Map current events; never fork event bus |
| Task state and persistence | src/agent_os/orchestrator/{engine,model,store,retry,worktrees}.py | digger topics; CopilotKit server engine | Adapter, no second work queue |
| Approval, decision, outbound effects | src/agent_os/executive/{gateway,outbox,contracts}.py; policy/orchestrator-os.policy.json | tahodev approvals | Port complete behavior + attack tests |
| Audit, usage, costs | src/agent_os/orchestrator/{trace,ledger,usage,control_plane}.py | tahodev audit | Combine receipt trail, don't duplicate usage |
| Existing hub and simple GUI | gui/{index.html,executive.html,app.js,executive.js}; docs/simple-mode.md | CopilotKit UI, digger topics | Reuse components or accessibility patterns |
| Browser, web capture, desktop | src/agent_os/{browser_control,browser_bridge}.py | CopilotKit worker; nanoMuse hands | Inspect existing work before worker copy |
| Memory, context and file knowledge | src/agent_os/{compiler,profile,ingester_router}.py and Knowledge Engine | nanoMuse UI, digger notes | User-editable projections only |
| Cross-provider connector routing | src/agent_os/{connectors,surfaces,mcp_server}.py; surfaces/registry.json | nanoMuse hub; Hermes channels | One broker, no duplicate credentials |
| Notifications, reminders, commitments | src/agent_os/executive/{event_bus,window_queue,next_action}.py | nanoMuse reminders | One elected scheduler/task owner |
| Coding, evaluation and compute | src/agent_os/orchestrator/* | digger delegation UI | Keep Agent OS routing and validators |

## Borrow/Wrap evaluation card required for each candidate

Fill one per copy target under this audit or in typed prior-art/DEC records:
- Candidate ID; upstream repository URL, commit SHA, exact source files and test files.
- Claimed capability vs source-verified behavior, maintenance/compatibility and missing production gates.
- Existing Agent OS equivalent; redundant code eliminated and remaining glue needed.
- Decision BORROW / WRAP / ADOPT / DEFER / REJECT; why it is better than writing from scratch.
- Vendor import method (small copied implementation plus notices and tests; git subtree only for large actively updated dependency; optional adapter for external service).
- Behavior/parity tests, policy/privacy tests, upstream test result and performance; report UNKNOWN if not run.
- Feature flag, canonical state ownership, errors/restarts/rollback.
- Files changed, API and data migrations, upstream updates/rebase strategy, source attribution and final commit.

## First source-audit batch: bounded and independently useful

Batch A: extract CopilotKit streaming event contract/UI components and harness from apps/server/src/engine and mobile; map to existing Executive event_bus. Deliver read-only run timeline proof.

Batch B: extract tahodev approval tests and host-side implementation. Port into a separate fixture prototype with no actual send, finance or work writes. Deliver tamper/replay/resume test report.

Batch C: extract nanoMuse hub protocol service/client and desktop link. Demonstrate read-only device heartbeat with a fake pair of clients; no screens or credentials.

Batch D: extract digger topic and return-path tests. Map exactly to an existing Orchestrator run_id and output artifact without parallel topic memory storage.

Proceed with code integration only when tests document compatibility and value. Record failures, failures after restart, and why any upstream chunk is rejected. Nothing in this audit asserts these implementations have been subsumed already.
