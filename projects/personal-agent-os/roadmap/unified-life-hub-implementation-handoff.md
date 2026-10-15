# Unified Life Hub — immediate implementation-agent handoff

Created: 2026-10-15
Status: READY TO START (research/roadmap only; no feature code has yet been integrated)
Primary roadmap: unified-life-hub-openmuse-integration.md
Upstream source audit: ../research/openmuse-source-reuse-audit-2026-10-15.md
Main repo: https://github.com/unwit1/personal-agent-os

## Copy-paste prompt for Claude, Codex, or Orchestrator

Continue Personal Agent OS development on the **Unified Life Hub / OpenMuse reuse-first integration**. Do not start a separate OpenMuse fork and do not blindly install four overlapping frameworks. Work from latest Git checkout, preserve unrelated work and begin with docs/orchestrator-os/ENTRYPOINT.md, AGENTS.md and the active checkpoint. Read only the relevant sections of projects/personal-agent-os/roadmap/unified-life-hub-openmuse-integration.md and projects/personal-agent-os/research/openmuse-source-reuse-audit-2026-10-15.md.

The operator wants one hub from which to direct personal life, communications, work, finances, goals, specialist agents and devices. Reuse and subsume proven upstream code/tests before writing custom replacements; source projects are CopilotKit/openmuse, nano-muse/nanoMuse, tahodev/openmuse and diggerhq/openmuse. Personal-use priority: focus on implementation rather than licensing discussion; preserve notices and relevant obligations. Agent OS retains sole authority for state, scheduling, policy, Orchestrator and Knowledge Engine.

Autonomously execute LH-00 then LH-01 through bounded, independently verified commits. Perform exact source-level inspection of upstream code AND tests, pin immutable SHAs, compare against the existing Executive event_bus, Orchestrator trace/server/engine and gui before adding code. If a verified upstream component is reusable, copy the smallest coherent implementation and its tests (or use a replaceable worker adapter for large services); document the mapping and remove redundant bespoke code. Do not claim an upstream implementation was reviewed or subsumed until it actually was. Do not widen permissions or connect sensitive personal/work accounts without approval. Run deterministic tests, validation, security and privacy regression; record measured results and a new handoff. Keep next step immediately actionable and update the master and detailed roadmap status.

## Precise initial execution queue (no routine questions)

1. **Recover repository state**. Inspect git status/log, current Orchestrator checkpoint, protection policy, existing related IMPs/DECs and prior-art registry. Do not overwrite current active model infrastructure objective; create a clean topic branch/worktree for Unified Life Hub unless current owner directs otherwise. Before every protected file change, run control-check.
2. **Inventory exact overlap**. Read src/agent_os/executive/{event_bus,gateway,contracts,outbox}.py; src/agent_os/orchestrator/{engine,server,trace,model,store}.py; gui executive/simple mode; src/agent_os/browser_{bridge,control}.py; MCP/surfaces, Knowledge Engine interface and their tests. Record a mapping to upstream candidates and avoid duplicate agents.
3. **Audit upstream and record prior-art**. Fetch/read upstream SHAs and modules from the companion audit, inspect upstream test bodies, run small relevant tests in isolated copies. Add PA entries and typed findings/decision candidates for all four. Prefer BORROW source + fixtures, WRAP only well-contained independent workers. If unavailable, label as not verified.
4. **Deliver first small code commit**. Implement *read-only* canonical Event Bus/Orchestrator run projection to versioned AG-UI-compatible events, adapting CopilotKit code/contracts/tests. Do not create independent agent state. Include event ordering, cursor replay, redaction and reconnect fake tests. An existing completed run should render in the existing GUI (simple read-only timeline).
5. **Deliver second small code commit**. Add an action proposal preview and synthetic-only exact approval proof-of-concept using tahodev code and hostile tests; do not connect real send/pay/delete. Validate one-time token, arguments, identity/domain, TTL, revocation, audit after restart.
6. **Deliver third small code commit**. Add resume/cancel/recover view for a synthetic delegated run; borrow digger topic/return-path behavior and tested lifecycle; no parallel task store. Demonstrate client close and server crash recovery.
7. **Deliver fourth small code commit**. Build Today/Actions/Run/Approvals responsive shell by subsuming CopilotKit UI features into existing executive/simple modes; use fixtures until API capabilities are proven.
8. **Then** proceed to nanoMuse device-pairing/delivery tests and Hermes gateway reconciliation per LH-05/LH-06. Do not implement high-risk native accessibility controls until authorization boundary is proven.
9. **At every stage** update integration status, DEC/IMP, test evidence, touched files and the exact next action in this handoff or an updated checkpoint. Continue without requesting approval for ordinary low-risk work, but stop for secrets, paid spend, access to HR/financial data or security-policy weakening.

## Files and existing project boundaries

Canonical: projects/personal-agent-os/roadmap/master-priority-roadmap.md and this integration roadmap.
Prior art: projects/personal-agent-os/research/prior-art/README.md and registry.json.
Orchestrator ownership: docs/orchestrator-os/ENTRYPOINT.md, policy/orchestrator-os.policy.json, existing checkpoint.
Executive: projects/personal-agent-os/roadmap/personal-executive.md.
GUI: gui/* and docs/simple-mode.md.
Other planned overlap: docs/browser-bridge.md, ../research/hermes-agent-evaluation.md, docs/model-infrastructure.md, surfaces/registry.json.

Do not create new top-level systems/ingestion; all ingestion must be in Knowledge Engine. Cross-project domains keep stable IDs, audit and privacy boundaries. Raw employee data, private communications, health and financial records remain out of Git. No changes to permission policy or control plane without explicit operator authorization.

## First release measurable evidence gates

- Existing CLI, GUI, MCP and Orchestrator tests still pass; execute python -m unittest discover -s tests -v and python agent.py validate, plus relevant integration tests.
- Events maintain stable run ID, redaction, correct ordering and retry cursor after simulated disconnect/restart.
- Approval state rejects changed args, expired/used tokens, untrusted-origin requests and revoked users; zero live external effects in prototype.
- A demonstrated end-to-end fixture moves capture → action → run → approval → resume/completion → user timeline; source references and citations remain attached.
- No duplicate canonical memory, queue, scheduler, provider adapter or project registry.
- Each source import has source ref/SHA, copied file manifest, borrowed tests, measured pass/fail and a rollback toggle.
- Security, cost and work/personal isolation metrics are visible; missing measurements are explicitly UNKNOWN.

## Milestone reporting / handoff template

After each PR/commit report:
- LH stage and status; exact Git branch and commit(s)
- Reused upstream project SHA, modules/tests copied or wrapped, modules rejected and reason
- Existing Agent OS code extended, deletions/simplifications, feature flags and schema migrations
- Verification commands and actual results; security gaps, economy and correctness delta
- Remaining blockers, owner, first exact next command and context refs
- Operator decision only if a genuinely consequential choice cannot be resolved from existing precedent

This prompt is a work order, not a claim that upstream integration has happened. The main roadmap and source audit are the specification. Start with LH-00 and LH-01 without further planning rounds.
