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
- **35 DIAL/INFO source records** ingested in physical plugin order: **18 DIAL + 17 INFO**.
- **100 prioritized source records** are checkpointed in deterministic five-record JSONL shards.
- Source inventory remains **337 DIAL / 410 INFO**, **75 NPC_**, **33 LCTN**, **103 CELL**, **53 MESG**, and **14 SCEN** records.

## High-value evidence already preserved

The source layer now includes the full book corpus and complete quest corpus, plus the opening dialogue sequence for Llavados and Numinar.

Numinar's dialogue explicitly presents the Chronographers as fabricants serving Seht, says they monitor time and space, identifies Snow-Throat with the Throat of the World, and describes Towers as essential mechanisms or "pinpoints" of the Wheels of Lull. These statements remain attributed dialogue evidence inside this continuity rather than automatic Bethesda-canon conclusions.

## Browse

- `raw/source-records-0001-0005.jsonl` through `raw/source-records-0096-0100.jsonl` — first 100 prioritized source records
- `raw/record-counts.json` — complete plugin record inventory
- `source-manifest.json` — source metadata, extraction policy, and corpus state
- `ingestion-checkpoint.json` — resumable cursor

## Next cursor

Dialogue source record 36/747 combined DIAL+INFO records:

- INFO `05019E5A`
- parent topic: `05019E59 _Lull_MQ02_CanHelp`
- owning quest: `0500590E _Lull_MQ02`

## Provenance rule

Statements from Wheels of Lull remain scoped to `tes.mod.wheels-of-lull`. Dialogue, books, quest text, and implementation records can support continuity-specific claims, but they do not automatically establish Bethesda-canon metaphysics or history. Character testimony remains attributed when the source presents it as testimony rather than objective narration.
