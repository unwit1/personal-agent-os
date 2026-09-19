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

## P0 — Immediate usage-reduction foundation

This is the highest-priority work.

### P0.1 — Selective context and profile retrieval

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

### P0.2 — Shared document intelligence + local persistent extraction/OCR cache

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

### P0.3 — Resumable/checkpointed ingestion everywhere

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

### P0.4 — Deterministic/cache/skill-first execution policy

Make the default execution preference operational, not just documented:

1. existing deterministic utility;
2. cached result;
3. approved reusable skill;
4. cheap/fast model;
5. balanced/strong model;
6. high-reasoning/frontier model when justified.

Add deterministic validators wherever possible so expensive escalation is triggered by evidence rather than habit.

Success signal:
- repeated structured work increasingly bypasses LLM calls.

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

Unless an urgent bug or explicitly promoted user request intervenes, coding agents should pull work in this order:

1. selective profile/context retrieval with measurable context-size diagnostics;
2. exact page/file extraction + OCR cache and embedded-text-first document path;
3. dependency-aware cache invalidation and no-cache regression tests;
4. generalized checkpoint/deduplication utilities for imports/crawls, including iCloud backfill;
5. deterministic/cache/skill-first execution dispatcher;
6. local privacy-safe usage telemetry and usage report;
7. adaptive routing + validator-driven escalation;
8. automation miner;
9. skill miner + replay/evaluation;
10. Executive Event Bus / schemas / Next Action Engine;
11. capture + Rescue Mode;
12. communication/calendar intelligence;
13. proactivity/voice;
14. controlled autonomy;
15. reusable Knowledge Library / Elder Scrolls implementation;
16. mature Lorekeeper/live-writing systems.

## Gate for adding new features

Before implementing a major new model-driven feature, answer:

- Can existing deterministic code solve part of it?
- Can prior results be cached/reused?
- Can the work resume from checkpoints?
- Can context be retrieved selectively?
- Can it use an approved skill?
- How will usage be measured?
- What validates a cheap route before escalation?
- Will this create recurring model calls that should instead be event/rule driven?

If these questions have no satisfactory answer, improve the economy layer first.

## Related roadmaps

- `projects/personal-agent-os/roadmap/usage-intelligence-adaptive-routing.md`
- `projects/personal-agent-os/roadmap/personal-executive.md`

Design principle:

> **Make the agent cheaper to operate before making it do more.**
