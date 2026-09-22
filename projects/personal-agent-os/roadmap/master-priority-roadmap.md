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
- `projects/personal-agent-os/roadmap/personal-executive.md` — EXEC-0.5.

### P0.3 — Shared document intelligence + local persistent extraction/OCR cache

Status: **foundation complete** (2026-09-21) — steps 1-3 of the five-step path.
Implemented in `src/agent_os/documents.py`, exposed through CLI and MCP,
enforced by `agent.py validate`, and covered by 40 regression tests.

Delivered:
1. persistent exact-page cache keyed by content hash — **done**;
2. dependency/version-aware invalidation, so interpretation changes reuse
   OCR — **done**, and asserted structurally by test;
3. template-level structural signatures that are person-independent — **done**;
4. targeted field-zone OCR — **not started**;
5. bounded concurrency — **not started**, and correctly gated behind measuring
   the earlier steps.

Measured (40 pages, simulated OCR at 20ms/page): cold 0.65s, warm 0.14s
(4.5x repeat-run speedup, 78% avoided), classifier change 0.00s of OCR, OCR
engine upgrade correctly re-extracts.

HR-GUI is a separate repository and was not modified; wiring its scanner to
this layer is the next concrete step. Remaining debt is recorded in
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

Current bounded foundation (2026-09-22): `src/agent_os/ingestion.py` provides
provider-neutral local ledgers with stable work/run/stage/item IDs, content and
processor fingerprints, deduplication, explicit item states, scalar
checkpoints, and recovery of interrupted claims. The iCloud Mail adapter,
shared document page batches, and canonical local search-index rebuild now
delegate work through that ledger. The curated local profile JSON importer now
also reuses a gitignored derived-fact cache through the same ledger, with
changed-source requeue and interrupted-claim recovery. Drive, messages, feeds,
and other provider-specific imports remain unwired. The local candidate-record
reader now uses a project-scoped ledger for resumable directory scans without
changing the explicit curation/promotion boundary.

### P0.5 — Deterministic/cache/skill-first execution policy

Make the default execution preference operational, not just documented:

1. existing deterministic utility;
2. cached result;
3. approved reusable skill;
4. cheap/fast model;
5. balanced/strong model;
6. high-reasoning/frontier model when justified.

Add deterministic validators wherever possible so expensive escalation is triggered by evidence rather than habit.

The staged orchestrator in P0.1 should use this policy when selecting how each stage runs.

Success signal:
- repeated structured work increasingly bypasses LLM calls.


### P0.6 — Skill/Economy Regression Test Suite

Build an automated test/evaluation harness that proves the usage-saving skill layer actually saves context/usage and does not create its own bloat.

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

Implement provider-neutral capability classes and validator-driven escalation.

The router should:
- pre-route before expensive work begins;
- delegate bounded subtasks when useful;
- select the cheapest path likely to satisfy validation;
- escalate on concrete failure/ambiguity signals;
- record an observable route explanation;
- never claim to hot-swap the model already running inside ChatGPT/Claude.

### P1.3 — Optional API delegation

Only after local/deterministic/context savings are functioning.

Use OpenAI/Anthropic APIs for bounded Agent-OS-owned subtasks when doing so is advantageous. Treat API spend and host-plan usage as separate budgets. Never require both providers.

---

## P2 — Turn repeated usage into reusable machinery

### P2.1 — Automation Miner

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

Detect repeated model/tool workflows and create candidate reusable skills.

Lifecycle:
observed pattern → candidate → replay/evaluation → review → approved/rejected.

No generated skill may silently self-promote.

### P2.3 — Prompt/context optimization

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
4. text-message import;
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
12. automation miner;
13. skill miner + replay/evaluation;
14. Executive Event Bus / schemas / Next Action Engine;
15. capture + Rescue Mode;
16. communication/calendar intelligence;
17. proactivity/voice;
18. controlled autonomy;
19. reusable Knowledge Library / Elder Scrolls implementation;
20. mature Lorekeeper/live-writing systems.

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
- Will this create recurring model calls that should instead be event/rule driven?

If these questions have no satisfactory answer, improve the economy layer first.

## Related roadmaps

- `projects/personal-agent-os/roadmap/usage-intelligence-adaptive-routing.md`
- `projects/personal-agent-os/roadmap/personal-executive.md`

Design principle:

> **Make the agent cheaper to operate before making it do more.**
