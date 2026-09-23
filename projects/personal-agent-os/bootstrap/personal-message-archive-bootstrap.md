# Bootstrap Prompt — Personal Message Archive / Text Intelligence

You are implementing a first-class Personal Agent OS subsystem in `unwit1/personal-agent-os`.

Read first:
- `projects/personal-agent-os/roadmap/personal-message-archive.md`
- `projects/personal-agent-os/roadmap/master-priority-roadmap.md`
- relevant sections of `projects/personal-agent-os/roadmap/personal-executive.md`
- existing mail/PST ingestion, resumable ingestion, profile/selective retrieval, candidate promotion, people/relationship, commitment/executive queue, project detection, proactive analysis, MCP/CLI, and privacy/local-state code.

## Mission

Build the Personal Message Archive / Text Intelligence subsystem end-to-end.

The system must ingest legitimately obtained historical iPhone/iMessage/SMS/RCS data into local Agent OS state, normalize and index it, retrieve only relevant evidence, and use that evidence to improve the Agent OS profile, people/relationship context, commitments, project detection, life-event context, Personal Executive, and Proactive Insight Engine.

The entire baseline workflow must remain usable with **zero paid software and zero paid cloud/API dependency**. Do not require iMazing or another paid exporter. A free/open-source iOS/iMessage extractor such as `imessage-exporter` may be the first reference adapter, but core contracts must remain adapter-neutral.

## Non-negotiable constraints

1. Raw messages, attachments, phone/contact identifiers, backups, private extracted text, and raw model traces stay in approved local/private storage and never enter Git.
2. Original backups/exports are immutable evidence.
3. Re-import must be incremental, resumable, idempotent, and deduplicated.
4. SQLite + FTS5 must provide a complete useful baseline. Semantic retrieval is optional and must have a free/local path.
5. Never inject an entire archive or giant conversation into model context.
6. Preserve authorship: self-authored, third-party, automated/system, quoted/forwarded, or uncertain.
7. Third-party claims are not equivalent to direct self-statements.
8. Candidate learning follows Candidate -> Validated -> Canonical. Import/analysis may not silently rewrite canonical state.
9. High-sensitivity material must not silently promote into general profile state. Reuse existing privacy/sensitivity policy.
10. Tests and committed fixtures must be synthetic only.
11. Reuse existing generic Agent OS machinery before inventing parallel systems.
12. Do not stop after every phase asking whether to continue. Continue autonomously until a real approval/architecture gate is reached.

## Work discipline

Before coding, inspect repository state and existing abstractions. Treat current repository decisions, ADRs, tests, and contracts as authoritative.

Work in bounded phases following MSG-0 through MSG-10 from the dedicated roadmap. A thin end-to-end vertical slice may combine tightly coupled parts of MSG-1/MSG-2/MSG-4, but do not skip MSG-0 privacy/contracts work.

Make frequent coherent commits. Prefer one commit per completed MSG phase or validated vertical slice. After each commit:
- run focused tests;
- run relevant repository validation;
- record/update handoff/checkpoint state with existing Agent OS conventions;
- continue automatically when no meaningful approval gate exists.

Never debug using the user's real private messages unless a later integration step explicitly requires them. Build and prove the architecture with synthetic fixtures first.

## First milestone

Deliver this vertical slice first:

synthetic iPhone-style message fixture
-> importer
-> normalized SQLite store
-> deterministic IDs/deduplication
-> FTS5 search
-> bounded CLI search
-> bounded MCP search
-> one evidence-linked profile candidate
-> no automatic canonical promotion
-> interrupted-import resume test
-> idempotent re-import test
-> privacy validation proving raw message content cannot enter canonical Git.

## Architecture guidance

Prefer repository conventions, but expect a subsystem roughly like:

```
src/agent_os/messages/
  schema.py
  store.py
  normalize.py
  identity.py
  retrieval.py
  candidates.py
  commitments.py
  people.py
  proactive.py
  cli.py
  importers/
    base.py
    ios_export.py
```

This layout is illustrative, not mandatory.

Recommended local state shape, adjusted to repository conventions:

```
.agent-local/messages/
  sources/
  imports/
  attachments/
  messages.sqlite3
  semantic/
  checkpoints/
  manifests/
  logs/
```

## Data model

Implement versioned normalized storage for:
- message_sources;
- conversations;
- participants;
- conversation_participants;
- messages;
- reactions;
- attachments;
- import_runs;
- derived_evidence.

Message records should retain stable/source identifiers, conversation, sender, self-authorship state, timestamp, service, normalized text, raw-content reference, reply relation, edit/delete state where represented, content/import hashes, provenance, and confidence.

Participant identity must support aliases and changed identifiers without destructive uncertain merges.

## Import behavior

The importer must:
- preserve source manifest/hash/version;
- stream or batch large archives;
- checkpoint regularly;
- normalize conversations/participants/messages/replies/reactions/attachments;
- record warnings without unnecessarily aborting the whole import;
- deduplicate overlapping exports;
- distinguish identical body text from identical logical messages;
- detect unchanged sources;
- resume interrupted work;
- expose deterministic counts;
- preserve last-good state on failure.

Reuse the existing resumable-ingestion ledger and stable-ID conventions wherever appropriate.

## Retrieval

Implement:
- exact message lookup;
- conversation lookup;
- FTS5/BM25 lexical search;
- participant filter;
- date range;
- service filter;
- authored-by-self filter;
- attachment filter;
- bounded surrounding-message context;
- person history;
- timeline;
- compact evidence packets.

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

Follow existing CLI/MCP naming and authorization patterns if they differ.

## Profile learning

Create evidence-backed candidates for durable facts such as:
- preferences/dislikes;
- interests/hobbies;
- routines/habits;
- goals;
- projects/ideas;
- commitments;
- planned purchases;
- life events;
- places;
- possessions;
- work history;
- communication style/preferences;
- relationship context;
- recurring friction/problems.

Every candidate must include:
- normalized statement/type;
- stable evidence IDs/spans;
- self-authored vs third-party vs inferred evidence class;
- first/last observation;
- recurrence;
- confidence with inspectable reasons;
- sensitivity;
- contradiction/supersession links;
- intended destination;
- promotion state.

Prefer direct self-authored evidence and repeated behavior over third-party claims or model inference.

Do not invent opaque precision.

## Commitments

Detect possible unresolved commitments such as:
- "I need to..."
- "I'll..."
- "I should..."
- "remind me..."
- promised follow-ups;
- appointments/plans;
- requests awaiting action;
- repeatedly deferred chores/purchases/admin tasks.

Reconcile against existing commitments/tasks/Executive Queue before creating another candidate. Track resolution/counter-evidence.

## People / relationships

Integrate participants with the existing people/relationship layer. Support alias clustering, group chats, uncertainty, changed identifiers, relationship context, and interaction timeline.

Do not make private facts about third parties globally canonical just because they appear in a conversation.

## Projects / ideas

Feed durable repeated ideas and projects into existing project-candidate detection. Reuse relationship semantics:
NEW, DUPLICATE, EXTENDS, CONFLICTS_WITH, DEPENDS_ON, SUPERSEDES.

Do not promote every passing thought into a project.

## Proactive Insight Engine

After retrieval/candidate extraction is dependable, allow message evidence to contribute selectively to:
- recurring friction;
- forgotten/repeated commitments;
- persistent interests;
- desired purchases;
- project candidates;
- communication bottlenecks;
- changed preferences;
- contradictions in old vs newer self-statements;
- recurring tasks suitable for automation.

Deduplicate against existing roadmap items, commitments, profile candidates, projects, skills, and prior proactive findings. Most messages should produce no durable update.

## Personal Executive

Expose selective APIs so Executive systems can use validated message-derived context without coupling directly to the message database.

Examples:
- Rescue Mode surfaces a forgotten commitment with evidence;
- Next Action Engine sees a validated unresolved commitment;
- Communication Intelligence retrieves only the relevant conversation around a follow-up;
- relationship context explains who someone is without loading years of texts.

## Testing

Build synthetic fixtures covering:
- one-to-one chats;
- group chats;
- self vs other authorship;
- replies/reactions;
- identical body text in distinct messages;
- edited/deleted variants if supported;
- attachments;
- alias/identifier changes;
- overlapping exports;
- interrupted import;
- changed source;
- corrupt row;
- repeated preferences;
- superseded/contradictory self-statements;
- third-party claim about the user;
- unresolved then resolved commitment;
- project candidate;
- high-sensitivity content that must not auto-promote.

Regression coverage must include import idempotency, retrieval bounds, identity uncertainty, privacy/redaction, candidate promotion boundaries, and downstream integration.

## Performance

Measure before tuning:
- messages/sec import;
- cold vs unchanged re-import;
- duplicate handling on overlapping fixtures;
- FTS latency;
- evidence/context packet size;
- candidate-analysis input size;
- resume overhead.

Optimize deterministic/local work before adding more model use.

## Documentation

Add a nontechnical Windows guide explaining:
1. how to obtain a local source using a no-cost path;
2. where Agent OS expects it;
3. exact import command;
4. import health/status;
5. search examples;
6. refresh/update workflow;
7. what stays local;
8. how to rebuild derived indexes;
9. what can/cannot enter Git;
10. how candidate learning and promotion work.

## Roadmap/status maintenance

Update `projects/personal-agent-os/roadmap/personal-message-archive.md` as phases are implemented. Add evidence/status, not just claims.

When safely editing related roadmaps, keep the master priority roadmap and Personal Executive integration references aligned.

Create ADRs only for genuine architecture decisions.

## Stop conditions

Pause for user input only when:
- a consequential architecture choice has no repository precedent and is not safely reversible;
- destructive handling of a real archive is proposed;
- credentials/secrets are required;
- a paid dependency appears unavoidable (redesign first);
- real private message access becomes necessary after synthetic implementation is complete;
- a consequential external write requires approval.

Ordinary code, tests, documentation, refactors, debugging, and safe local fixture work should continue without repeated confirmation.

## Definition of done

Do not call this complete until the dedicated roadmap acceptance criteria pass.

The mature outcome is a free, local, incremental Personal Message Archive that Agent OS can search selectively and use as provenance-backed evidence to understand the user's preferences, people, projects, commitments, life events, recurring problems, and communication context—without exposing raw private conversations, conflating third-party claims with self-authored facts, or silently promoting weak inferences into canonical memory.
