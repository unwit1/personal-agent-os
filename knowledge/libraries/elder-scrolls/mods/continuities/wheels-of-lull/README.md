# The Wheels of Lull

Sub-continuity for the Skyrim mod **The Wheels of Lull**.

- Continuity ID: `tes.mod.wheels-of-lull`
- Primary source: user-provided `WheelsOfLull.esp`
- ESP SHA-256: `230b102cd1ec13f2d104da8803d32c19227ef519eaca766a00b076c322aa78bb`
- Source header: version 6.0.0.3; original mod by Trainwiz, with later Chronographer Maintenance Team updates recorded in the plugin header.
- Continuity policy: mod-added lore may reference official Elder Scrolls material but must not overwrite or silently become Bethesda continuity.

## Current ingestion status

- **33/33 BOOK** records preserved with exact decoded text.
- **32/32 QUST** records preserved with quest stages, journal text, objectives, and provenance where present.
- **42/337 DIAL** topics and **43/410 INFO** records preserved in physical plugin order.
- **85/747 combined dialogue records** are now ingested.
- **150 prioritized source records** are checkpointed overall.

## Dialogue evidence already preserved

The current dialogue corpus covers the opening Llavados/Numinar material, the Analyst sequence, Numinar's Whitehorn plan, and Subori's Upgate introduction.

Notable continuity-scoped testimony includes:

- Numinar describes the Chronographers as fabricant servants of Seht who monitor time and space.
- Snow-Throat is identified with the Throat of the World and described as a Tower/world mechanism.
- The Analyst describes itself as an intelligence that once ran data collection in Sotha Sil.
- The three investigative sites are the Greybeards, College of Winterhold, and Thalmor.
- The Analyst identifies Thalmor activity at Whitehorn Pass.
- Numinar describes infiltration rather than direct assault as the preferred response.
- Subori describes the Upgate as the Chronographers' surface-travel mechanism and says their team lacks a helicarrier.

These remain attributed source statements rather than automatic Bethesda-canon conclusions.

## Raw corpus

- `raw/source-records-0001-0005.jsonl` through `raw/source-records-0096-0100.jsonl` — records 1-100
- `raw/source-records-0101-0150.jsonl.gz` — records 101-150, gzip-compressed UTF-8 JSONL
- `raw/record-counts.json` — complete plugin record inventory
- `source-manifest.json` — extraction policy and corpus state
- `ingestion-checkpoint.json` — resumable cursor

## Next cursor

Dialogue combined record **86/747**:

- DIAL `05024257`
- Editor ID: `_Lull_MQ03_ToadyIntroTopic`
- Owning quest: `0500590F _Lull_MQ03`

## Provenance rule

Statements from Wheels of Lull remain scoped to `tes.mod.wheels-of-lull`. Dialogue, books, quest text, and implementation records can support continuity-specific claims, but they do not automatically establish Bethesda-canon metaphysics or history. Character testimony remains attributed when the source presents it as testimony rather than objective narration.
