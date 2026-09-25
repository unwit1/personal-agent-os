# Personal Message Archive / Text Intelligence Roadmap

Status: proposed / implementation-ready
Owner: Personal Agent OS
Track: MSG
Priority context: extends Master Roadmap P6 and EXEC-11.5 Personal Communication Gateway
Added: 2026-09-23

## Goal

Make the user's historical and future text-message history a first-class, privacy-preserving Personal Agent OS data source without requiring any paid software or paid cloud API.

The subsystem must turn legitimately obtained local message archives into a deterministic, resumable, searchable local knowledge source that can selectively support:

- personal profile refinement;
- people and relationship context;
- commitments and unresolved promises;
- projects, ideas, purchases, plans, and life events;
- communication-style understanding;
- Personal Executive next-action and rescue workflows;
- Proactive Insight Engine candidate discovery;
- cross-project retrieval when relevant.

Raw messages are evidence, not canonical profile facts. All durable learning follows the existing staged Candidate -> Validated -> Canonical model.

## Non-negotiable requirements

1. **Zero paid dependency.** The complete supported workflow must remain usable with free software. Paid utilities may never be required for import, indexing, search, profile extraction, or incremental updates.
2. **Local-first raw data.** Raw messages, attachments, contact identifiers, and high-volume indexes remain in local/private Agent OS storage by default and are never committed to Git.
3. **Immutable source preservation.** Original backups/exports are read-only evidence. Derived stores can be rebuilt from them.
4. **Selective retrieval.** Never inject a whole message archive into a model context. Retrieve only relevant conversations/messages/evidence spans under explicit budgets.
5. **Authorship awareness.** Distinguish account ownership from authorship and subject identity. A ChatGPT/mail/device account belonging to the user does not prove the user authored or is described by every record. Track actor state (`user`, `user_confirmed`, `other_account_user`, `third_party`, `organization_archive`, `automated`, `unknown`) and require reconciliation before non-user actor evidence can alter the personal profile.
6. **Third-party privacy boundaries.** Facts about other people are not automatically promoted into the user's canonical profile. Relationship context and third-party claims retain source attribution and stricter sensitivity controls.
7. **Evidence-backed learning.** Every derived profile/commitment/project/relationship candidate must link back to one or more stable message evidence records.
8. **Incremental and resumable.** Re-importing an archive must process only new or changed material, survive interruption, and never duplicate already-indexed messages.
9. **Provider-neutral interfaces.** Retrieval and analysis are exposed through Agent OS CLI/MCP/service contracts, not hard-coded to ChatGPT, Claude, Codex, or one model provider.
10. **No cloud requirement.** Search, normalization, FTS, deduplication, and baseline profiling must work without paid APIs. Optional semantic retrieval must support a local model path.
11. **Sensitive inference controls.** Credentials, authentication codes, financial account secrets, medical details, political preferences, sexual/private-intimacy information, and other high-sensitivity material must never be silently promoted into general canonical profile state.
12. **Synthetic tests only.** Repository fixtures/tests must use synthetic message data, never the user's real texts.

## Reference acquisition path

Windows + iPhone should have a zero-cost supported route:

iPhone
-> local Apple device backup
-> free/open-source extraction/import adapter
-> normalized Agent OS message store
-> FTS5 / optional local semantic index
-> selective retrieval
-> candidate analysis
-> validated/canonical Agent OS knowledge

The first reference adapter may use an open-source iOS/iMessage backup parser/exporter such as `imessage-exporter`, but the core schema and ingestion engine must not depend on one utility's output format. Support structured CSV/JSON/HTML/text exports where practical and keep adapter boundaries explicit.

Do not require iMazing or another paid export utility.

## Storage architecture

Recommended local layout:

```text
.agent-local/
  messages/
    sources/
    imports/
    attachments/
    messages.sqlite3
    semantic/
    checkpoints/
    manifests/
    logs/
```

Canonical Git may contain:

- schemas;
- importer code;
- fixtures;
- sanitized aggregate metadata;
- approved/validated derived profile facts under existing policy;
- roadmap/decisions;
- tests and documentation.

Canonical Git must not contain:

- raw text-message bodies;
- real attachments;
- phone numbers/contact identifiers unless already explicitly approved elsewhere;
- source backups;
- authentication material;
- raw model transcripts over private conversations.

## Normalized data model

The normalized store should support at minimum:

### message_sources
- source_id
- source_kind
- source_path_reference
- source_hash
- device/account metadata when safely available
- import adapter + version
- first_seen_at
- last_seen_at
- immutable_source flag

### conversations
- conversation_id
- stable source key
- service/type (iMessage/SMS/RCS/unknown)
- title/group name when present
- participant-set fingerprint
- first_message_at
- last_message_at

### participants
- participant_id
- stable normalized identity key
- display aliases
- contact identifiers stored locally
- ownership relation: self / other / unknown
- confidence/provenance

### conversation_participants
- conversation_id
- participant_id
- role/metadata

### messages
- message_id
- source_id
- conversation_id
- source_message_key
- sender_participant_id
- authored_by_self boolean/unknown
- sent_at
- received_at when available
- service
- normalized_text
- raw-content reference
- reply_to_message_id
- edited/deleted state when represented
- import/content hashes
- provenance/confidence

### reactions
- reaction_id
- target_message_id
- actor_participant_id
- reaction kind
- timestamp when available

### attachments
- attachment_id
- message_id
- source reference
- content hash
- filename/media type/size
- extraction status
- derived-text reference
- privacy/sensitivity flags

### import_runs
- run_id
- adapter/version
- source hash/version
- checkpoint
- counts
- started/completed timestamps
- warnings/errors

### derived_evidence
- evidence_id
- message_id or bounded message range
- evidence span/hash
- derivation kind
- candidate id
- extractor/version
- confidence

## Deterministic identity, deduplication, and incremental sync

Prefer stable source IDs when available. Otherwise build deterministic fingerprints from normalized conversation identity, sender, timestamp, service, body hash, attachment hashes, and reply/reaction metadata.

Distinguish:

- exact duplicate;
- same logical message from overlapping exports;
- edited version;
- reaction/update event;
- quoted/repeated text;
- genuinely distinct messages with identical bodies.

Maintain an import ledger compatible with the existing resumable-ingestion architecture. A repeated import with no source changes should become nearly no-op work.

## Retrieval

Implement local retrieval in layers:

1. exact ID / conversation lookup;
2. SQLite FTS5/BM25 lexical search;
3. structured filters: participant, date range, conversation, service, authored-by-self, attachment;
4. optional local semantic retrieval;
5. bounded surrounding-context expansion;
6. compact evidence packet generation.

Semantic retrieval must be optional. If implemented, use a local embedding path by default and keep the vector backend replaceable. The subsystem must remain useful with only SQLite + FTS5.

Suggested provider-neutral interfaces:

- `messages.sources`
- `messages.import`
- `messages.import_status`
- `messages.search`
- `messages.get_message`
- `messages.get_conversation`
- `messages.get_context`
- `messages.person_history`
- `messages.timeline`
- `messages.related`

MCP wrappers should expose the safe read operations and bounded import/status operations consistent with existing Agent OS policy.

## Profile-learning integration

Build a provenance-aware candidate extractor over selected messages. Candidate categories may include:

- preference / dislike;
- interest / hobby;
- routine / habit;
- goal;
- project / idea;
- commitment / promise;
- planned purchase;
- life event;
- place;
- possession;
- work history;
- communication preference/style;
- relationship context;
- recurring friction/problem;
- durable personal fact.

Every candidate must record:

- candidate id;
- type;
- normalized statement;
- evidence message ids/spans;
- whether evidence is user-authored, third-party, inferred, or mixed;
- first/last observed timestamps;
- recurrence count;
- confidence;
- sensitivity;
- contradiction/supersession links;
- suggested destination;
- promotion state.

### Evidence weighting

Prefer, roughly:

direct user-authored statement
> repeated user behavior or repeated direct statements
> confirmations/action evidence
> trusted correspondence directly involving the user
> third-party statement about the user
> automated/marketing content
> model inference.

Do not turn this ordering into an opaque numeric truth score; retain inspectable evidence and confidence reasons.

## People and relationship integration

Message participants should resolve into the Agent OS people/relationship layer without conflating identifiers.

Support:

- aliases and changed phone/email identifiers;
- group chats;
- uncertain identity matches;
- relationship-context evidence;
- interaction timeline and recency;
- user-authored statements about a relationship;
- third-party facts separated from user facts.

Never make private third-party information globally canonical merely because it appears in a conversation. Identity confidence and relationship confidence are separate: knowing who someone is does not establish closeness, importance, or relationship type. Same-name matches stay separate until stable identifiers, contextual evidence, or user confirmation link them.

## Commitment / task integration

Detect candidate commitments from language and conversation state, including:

- "I need to..."
- "I'll..."
- "remind me..."
- promised follow-ups;
- appointments/plans discussed but not resolved;
- purchases or chores repeatedly deferred;
- unanswered requests directed at the user.

A detected commitment is a candidate, not automatically a live task. Reconcile against existing Executive Queue/tasks/commitments before creating duplicates.

Persist evidence, counter-evidence, due-date language, related person/project, and resolution signals.

## Project and idea detection

Feed repeated ideas, projects, hobbies, desired purchases, and unresolved work into the existing project-detection system.

Use the existing relationship classifier:

- NEW
- DUPLICATE
- EXTENDS
- CONFLICTS_WITH
- DEPENDS_ON
- SUPERSEDES

Do not create a new project for every passing thought. Require the existing project-candidate evidence threshold.

## Proactive Insight Engine integration

The postflight/proactive layer may query message-derived evidence when relevant.

It should be able to discover:

- recurring complaints/friction;
- abandoned/repeated commitments;
- repeated desired purchases;
- project candidates;
- recurring communication bottlenecks;
- changed preferences;
- contradictions in old vs newer profile evidence;
- repeated life/admin tasks suitable for automation.

Most imports should not create canonical changes. Candidate capture should be cheap; validation/promotion remains bounded and evidence-driven.

## MSG implementation phases

### MSG-0 — Contracts, privacy, and repository integration

- inspect existing mail, profile, people, commitment, proactive, resumable-ingestion, MCP, and privacy contracts;
- write message schema/contracts without duplicating existing generic primitives;
- register local storage paths and privacy boundaries;
- add synthetic fixtures;
- add validation that raw/private message storage cannot land in canonical Git.

Exit criteria:
- schemas and boundaries are explicit;
- `agent.py validate` or equivalent catches forbidden raw-message state;
- no paid dependency is introduced.

### MSG-1 — Reference iPhone/Windows import adapter

- implement a structured import path for an open-source iOS/iMessage export or local backup extraction;
- support adapter versioning;
- preserve source manifests and hashes;
- normalize conversations/participants/messages/replies/reactions/attachments where available;
- emit import-run stats and warnings.

Exit criteria:
- synthetic/reference fixture imports deterministically;
- repeated import is idempotent;
- interruption resumes from checkpoint.

### MSG-2 — SQLite/FTS5 message store

- normalized SQLite schema + migrations;
- FTS5 index;
- structured filters;
- deterministic IDs and duplicate reconciliation;
- import ledger integration.

Exit criteria:
- 100% synthetic fixture re-import produces no duplicate logical messages;
- exact and lexical retrieval are deterministic.

### MSG-3 — Attachments and rich conversation structure

- attachment inventory/hash/provenance;
- reply/reaction/edit relationships;
- bounded local text extraction for supported attachment types using shared document intelligence;
- no unnecessary OCR.

Exit criteria:
- rich message relationships survive import;
- attachments can be found without loading binary data into model context.

### MSG-4 — CLI/MCP retrieval surface

- implement bounded read APIs;
- add context-window expansion;
- expose provenance;
- enforce explicit result/context limits.

Exit criteria:
- another Agent OS component can retrieve a relevant message packet without direct SQLite knowledge;
- MCP never dumps the whole archive by default.

### MSG-5 — People/identity resolution

- resolve self vs other;
- alias/contact clustering;
- confidence + manual correction path;
- integrate with existing people context.

Exit criteria:
- changed identifiers can map to one person without destructive merge;
- uncertain matches stay uncertain.

### MSG-6 — Profile candidate extraction

- deterministic extraction first where possible;
- model-assisted extraction only on bounded selected evidence;
- Candidate -> Validated -> Canonical integration;
- contradiction, recurrence, recency, and sensitivity handling.

Exit criteria:
- synthetic messages generate evidence-linked candidates;
- third-party assertions are visibly distinct from self-authored evidence;
- no candidate silently becomes canonical.

### MSG-7 — Commitments, projects, life events, and relationship context

- candidate commitment extraction/reconciliation;
- project/idea detection;
- life-event timeline candidates;
- relationship-context candidates.

Exit criteria:
- repeated or unresolved synthetic commitments are surfaced once, with evidence;
- project candidates deduplicate against existing work.

### MSG-8 — Proactive Insight Engine integration

- message source available to proactive postflight when relevant;
- recurrence clustering;
- contradiction/change detection;
- roadmap/skill/automation candidate generation through existing staged persistence.

Exit criteria:
- bounded synthetic cross-chat/message evidence can produce a candidate systemic insight;
- low-confidence noise remains ephemeral or candidate-only.

### MSG-9 — Incremental refresh and automation hooks

- detect changed/new backup/export inputs;
- process only deltas;
- run locally on explicit command or approved scheduler hook;
- surface import health/status.

Exit criteria:
- unchanged refresh is nearly no-op;
- changed source imports only new/changed records;
- failures preserve last-good state and resume safely.

### MSG-10 — Quality, benchmarks, and user-facing diagnostics

Add:
- import throughput benchmark;
- FTS query latency benchmark;
- duplicate/idempotency benchmark;
- context-size/token estimate diagnostics;
- candidate precision/review fixture suite;
- privacy regression suite;
- fresh-machine rebuild test from immutable source fixture.

Exit criteria:
- implementation can be rebuilt, verified, and audited without access to the user's real messages;
- no paid product/API is required anywhere in the tested path.

## Reuse before invention

Before adding new machinery, inspect and reuse:

- existing mail/PST indexing patterns;
- existing SQLite/FTS conventions;
- resumable ingestion/checkpoint utilities;
- document extraction/cache system;
- selective profile retrieval;
- candidate-memory promotion;
- Personal Executive queue/commitment contracts;
- Proactive Insight Engine contracts;
- project-candidate detection;
- MCP server conventions;
- privacy/secret/local-state validation;
- Orchestrator run visibility and checkpoint patterns.

Where mail and messages share generic primitives, extract reusable communication-ingestion abstractions rather than copying code. Do not force unlike semantics into one table merely for reuse.

## Acceptance criteria for the complete subsystem

The track is complete when:

1. A user can create a local iPhone message source with no paid software and import it into Agent OS.
2. The original source remains immutable and locally private.
3. Re-import is incremental, resumable, and idempotent.
4. Messages are searchable by words, person, date, conversation, and authorship.
5. Retrieval returns compact evidence packets, not broad dumps.
6. The agent can answer personal-history questions with traceable message evidence.
7. Profile candidates distinguish self-authored evidence from third-party claims.
8. Message-derived profile changes follow Candidate -> Validated -> Canonical.
9. Commitments/projects/life events/relationship insights integrate with their existing Agent OS systems.
10. The Proactive Insight Engine can use message evidence selectively and deduplicate findings.
11. High-sensitivity material is restricted from silent general-profile promotion.
12. Raw messages and attachments never enter Git or normal prompt logs.
13. Synthetic regression tests cover privacy, identity uncertainty, deduplication, edited/replied/reacted messages, interrupted imports, and candidate promotion.
14. Baseline operation uses only free/local software; optional paid/cloud capabilities are non-required extensions.
15. Documentation gives a nontechnical Windows user a deterministic import/update workflow.

## Definition of success

The user can legitimately import years of text history once, refresh it cheaply later, and ask Agent OS questions that benefit from that history without manually searching conversations or repeatedly uploading archives. Agent OS learns durable facts only when evidence and promotion policy justify them, preserves uncertainty and third-party privacy, and uses the archive to recover commitments, projects, preferences, relationships, and recurring problems without turning raw private conversations into indiscriminate model context.
