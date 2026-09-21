# Clockwork

Sub-continuity for the Skyrim mod **Clockwork**.

- Continuity ID: `tes.mod.clockwork`
- Primary source: user-provided `Clockwork.esp`
- ESP SHA-256: `6850eb707a5b47f60fcec7bfb3494a4d7e909549c6c199cca81fc18780f73406`
- Continuity policy: mod-added lore may reference official Elder Scrolls material but must not overwrite or silently become Bethesda continuity.

## Ingested source corpus

- **13/13 BOOK** records preserved as individual files.
- **242 DIAL / 888 INFO** records represented; **1,103 effective response strings** after DNAM reuse.
- **12/12 QUST** records browseable.
- **22/22 SCEN** records now cataloged structurally.
- All **322** strict single-NPC INFO records have named-character transcripts.
- All **545** strict multi-candidate records are cataloged; **7** broad-Gilded records now additionally resolve to scripted Gilded01/02/03 quest roles.
- All **21** strict no-NPC-candidate records are semantically accounted for by scene/quest analysis.
- Core VMAD/script-property wiring and plugin record inventory are persisted under `technical/`.

## Browse

- `books/` — exact decoded in-game book/note text
- `raw/` — archival extracted dialogue and quest text
- `dialogue/` — strict transcripts plus ambiguity/supplemental attribution layers
- `quests/` — player-facing and internal/technical QUST records
- `events/` — dated history, player-story graph, knowledge unlocks
- `locations/` — location evidence pages
- `artifacts/` — quest objects/material culture
- `topics/` — evidence-backed lore topics
- `entities/` — characters and relationships
- `analysis/` — themes, reliability, revisions, character arcs
- `technical/` — SCEN, VMAD, record inventory, mechanics, and alias-role evidence
- `claim-seeds.json` — evidence-backed claim seeds
- `source-manifest.json` — source/book manifest and hashes

## Provenance rule

Clockwork testimony remains scoped to this continuity. Implementation evidence may corroborate narrative events but does not automatically establish metaphysical lore. Lamashtu's Red Mountain/Kagrenac statements remain character testimony rather than an objective solution to the canonical Dwemer disappearance.
