# UESP ingestion reconnaissance

This document records source-structure findings that should shape the Elder Scrolls Knowledge Library importer.

## Findings

UESP lore articles frequently attach numbered references directly to individual statements. Those references can identify NPC dialogue, quest events, loading screens, item descriptions, in-game books, official external lore articles, and developer material. The importer should therefore preserve both the UESP passage and the underlying cited evidence rather than flattening the article into one secondary source.

UESP also explicitly distinguishes unofficial references on some lore pages. Those references remain useful for discovery and historical context, but the library must retain the warning and must not promote them to the same authority class as shipped-game evidence.

In-universe books require a separate epistemic layer. A book is primary evidence that a text exists in the setting and that its author/narrator makes particular statements. It is not automatically proof that every proposition in the book is objectively true. Language such as legend, belief, theory, speculation, allegory, and conflicting accounts should become qualifiers or contradiction candidates.

UESP cleanup categories are useful ingestion metadata. At least one Lore Places cleanup category explicitly says many member articles need in-game information removed. Membership should therefore trigger review metadata rather than being ignored.

Game-specific book pages and Lore book pages can represent the same underlying work at different layers. The game page may carry IDs, locations, collections, and other implementation metadata; the Lore page represents the work across appearances. Deduplication should use a work/appearance model instead of treating these as unrelated documents.

## Extraction stages

1. Fetch page plus revision identity and categories.
2. Classify page type and namespace.
3. Chunk prose without discarding citation markers.
4. Parse the References section into typed source records.
5. Resolve inline citation markers to those records.
6. Preserve epistemic language on the passage/claim.
7. Emit claim candidates only after exact evidence chunks exist.
8. Mark cleanup/unofficial/conflict signals.
9. Prefer direct underlying evidence during retrieval when it has been ingested.
10. Retain the UESP passage as the secondary provenance trail.

## Data-model additions suggested by reconnaissance

Add `reference_kind`, `authority_class`, `epistemic_status`, `container_source_id`, `underlying_source_id`, `work_id`, `appearance_id`, `revision_id`, and `quality_flags` to normalized provenance metadata. These can begin in JSON metadata without requiring an immediate SQLite migration.

## Representative cases

- Dariah: references include NPC dialogue, quest events, and a Loremaster's Archive.
- Kruntharth: UESP explicitly separates unofficial material from its ordinary references.
- Windsorrow: the article distinguishes a legend from later game events/dialogue that establish the spirit's existence.
- Khunzar-ri: Origin: the in-universe text itself foregrounds mutually contradictory origin stories.
- Wayshrines of Tamriel: an in-universe scholarly text includes beliefs and theories that should remain attributed.
- Lore Places cleanup category: category membership is a quality-control signal.
- Game-book vs Lore-book pages: preserve appearance metadata separately from the underlying work.

## Rule

Do not turn UESP prose into a flat canon database. The target is an evidence graph that can answer both “what does the setting say?” and “why do we believe that, and how reliable is the source?”
