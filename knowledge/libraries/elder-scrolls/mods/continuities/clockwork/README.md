# Clockwork

Sub-continuity for the Skyrim mod **Clockwork**.

- Continuity ID: `tes.mod.clockwork`
- Primary source: user-provided `Clockwork.esp`
- ESP SHA-256: `6850eb707a5b47f60fcec7bfb3494a4d7e909549c6c199cca81fc18780f73406`
- Continuity policy: mod-added lore may reference official Elder Scrolls material but must not overwrite or silently become Bethesda continuity.

## Ingested source corpus

- **13/13 BOOK records** are preserved as individual files in `books/`.
- **242 DIAL topics / 888 INFO records** are represented in the raw dialogue corpus.
- **520 direct response strings** expand to **1,103 effective response strings** after Skyrim `DNAM` response-data reuse.
- **12/12 QUST records** are now browseable: 7 player-facing quests and 5 internal/technical quest records.
- All **322 single-NPC-resolved INFO records** have browseable named-character transcripts.
- All **545 multi-candidate INFO records** are explicitly cataloged.
- The strict resolver's **21 no-NPC-candidate records** are all accounted for by supplemental scene/quest resolution.
- Narrative chronology, spoiler-aware knowledge gates, locations, relationships, and quest-critical artifacts are indexed as separate retrieval layers.

## Browse

- `books/` — exact decoded in-game book/note text
- `raw/` — archival dialogue and quest record text extracted from the ESP
- `dialogue/` — strict speaker transcripts, ambiguity pools, and supplemental diegetic attributions
- `quests/` — all QUST records, separated into player-facing and internal/technical
- `events/` — dated history plus reconstructed player-story graph
- `locations/` — location index and evidence pages
- `artifacts/` — quest objects and material-culture index
- `topics/` — evidence-backed Clockwork lore topics
- `entities/characters/` — character pages
- `entities/relationships.md` — relationship index with evidence/status
- `claim-seeds.json` — evidence-backed claim seeds
- `source-manifest.json` — source/book manifest and hashes

## Provenance rule

Clockwork testimony remains scoped to this continuity. In particular, Lamashtu's statements about Kagrenac, the Heart of Lorkhan, and her own death remain character testimony rather than an objective answer to the canonical Dwemer disappearance.
