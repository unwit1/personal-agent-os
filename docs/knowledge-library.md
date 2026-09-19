# Knowledge Library Architecture

The Knowledge Library is a generic, provenance-first subsystem for large reference corpora. Elder Scrolls lore is the first implementation, but domain-independent storage and retrieval must remain reusable.

## Design rules

1. Canonical Git data stores configuration, source policy, schemas, overlays, crawl state, and reviewed decisions.
2. Large fetched corpora, indexes, embeddings, and SQLite databases are derived local artifacts and are rebuildable.
3. Claims are never stored as context-free truth. Every claim retains source and evidence provenance.
4. Retrieval is selective and token-budgeted. Prefer lexical/structured retrieval before embeddings or model calls.
5. Ingestion is resumable and idempotent using a crawl ledger.
6. Contradictory claims may coexist. The system records disagreement instead of silently resolving it.
7. Primary sources, secondary summaries, external/developer statements, and project canon overlays remain distinguishable.
8. Model escalation follows Agent OS routing: deterministic processing first, cheaper models for routine extraction, stronger reasoning only for ambiguity.

## Core records

- Source: a work/page/document and its provenance class.
- Entity: a normalized subject such as person, place, faction, text, event, artifact, deity, or concept.
- Claim: an atomic assertion attached to evidence.
- Relationship: a typed entity-to-entity assertion with provenance.
- Citation: location/fragment metadata connecting a claim to source evidence.
- Contradiction: an explicit conflict or tension between claims.
- Overlay: project-specific interpretation/canon that never mutates the underlying reference corpus.

## Initial query surface

- search_lore(query, filters, budget)
- get_entity(entity_id, budget)
- verify_claim(claim_text, budget)
- find_contradictions(entity_or_claim, budget)

These interfaces should return compact evidence packets, not entire source documents.

## Elder Scrolls pilot

Start with a small representative corpus before bulk crawling UESP. Include several source shapes: character, location, faction, deity/metaphysical concept, event, quest, and in-universe book. Benchmark retrieval relevance, evidence traceability, contradiction handling, latency, and context size. Bulk ingestion is blocked until the pilot demonstrates useful retrieval without context bloat.
