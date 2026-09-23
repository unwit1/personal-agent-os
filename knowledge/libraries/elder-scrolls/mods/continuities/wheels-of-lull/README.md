# The Wheels of Lull

Sub-continuity for the Skyrim mod **The Wheels of Lull**.

- Continuity ID: `tes.mod.wheels-of-lull`
- Primary source: user-provided `WheelsOfLull.esp`
- ESP SHA-256: `230b102cd1ec13f2d104da8803d32c19227ef519eaca766a00b076c322aa78bb`
- Source header: version 6.0.0.3; original mod by Trainwiz, with later Chronographer Maintenance Team updates recorded in the plugin header.
- Continuity policy: mod-added lore may reference official Elder Scrolls material but must not overwrite or silently become Bethesda continuity.

## Current ingestion status

- **33/33 BOOK** records are preserved with exact decoded text.
- **17/32 QUST** records are preserved with quest stages, journal text, objectives, and provenance where present.
- **50 source records** are now checkpointed in deterministic five-record JSONL shards.
- Source inventory is complete: **337 DIAL / 410 INFO**, **32 QUST**, **75 NPC_**, **33 LCTN**, **103 CELL**, **53 MESG**, and **14 SCEN** records identified for later passes.
- Next cursor: QUST 18, `05005917 _Lull_DI_Fyr_Bagarn` ("Fyr and Bagarn's Dialogue").

## High-value source material already preserved

The source layer now includes the complete in-plugin book corpus, including the Chronography volumes, KINMUNE, Sybandis material, Archeron's notes/diary, memodermis references, fabricant death/rewinding material, and Chronographer technical texts.

The quest layer now includes the main sequence from **Deep Down** through **The Wheels of Lull**, preserving journal evidence for Lull-Mor, the Chronographers, Snow-Throat, Whitehorn Pass, Archeron, the Boiling Foundry, the Brass Forest, Memory, Masscroft, and the Stone of Snow-Throat.

## Browse

- `raw/source-records-0001-0005.jsonl` through `raw/source-records-0046-0050.jsonl` — first 50 source records
- `raw/record-counts.json` — complete plugin record inventory
- `source-manifest.json` — source metadata and extraction state
- `ingestion-checkpoint.json` — resumable cursor

## Provenance rule

Statements from Wheels of Lull remain scoped to `tes.mod.wheels-of-lull`. Dialogue, books, quest text, and implementation records can support continuity-specific claims, but they do not automatically establish Bethesda-canon metaphysics or history. Character testimony remains attributed when the source presents it as testimony rather than objective narration.
