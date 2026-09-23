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
- **159/337 DIAL** topics and **176/410 INFO** records preserved in physical plugin order.
- **335/747 combined dialogue records** are now ingested.
- **400 prioritized source records** are checkpointed overall.

## Dialogue evidence already preserved

This pass moves through ambient Lull-Mor dialogue and into the Wailway side quest.

Notable continuity-scoped testimony includes:

- Numinar says he was once an overclocker/mechanic and that after the Clockwork City died he was shipped out with the other Chronographers.
- Llavados says fabricant culture accepts experimentation on one another and themselves, with casualties treated as an expected risk.
- The Wailway locomotive identifies itself as a soul bound into an engine for transport.
- The locomotive attributes the Wailway project to the Reman-era Diolkos/Resource Men and describes punitive transformation of dissidents into industrial machinery.
- It says other Wailway engines hoped service might eventually earn them a final death.
- It says Reman later sold it to a "dark elven clockmaker," who studied and dismantled pieces of it before abandoning it.
- The locomotive asks the player to destroy its mechanical shell to release it.

These remain attributed source statements rather than automatic Bethesda-canon conclusions.

## Raw corpus

- `raw/source-records-0001-0005.jsonl` through `raw/source-records-0096-0100.jsonl` — records 1-100
- `raw/source-records-0101-0150.jsonl.gz` — records 101-150
- `raw/source-records-0151-0200.jsonl.gz` — records 151-200
- `raw/source-records-0201-0250.jsonl.gz` — records 201-250
- `raw/source-records-0251-0300.jsonl.gz` — records 251-300
- `raw/source-records-0301-0350.jsonl.gz` — records 301-350
- `raw/source-records-0351-0400.jsonl.gz` — records 351-400
- `raw/record-counts.json` — complete plugin record inventory
- `source-manifest.json` — extraction policy and corpus state
- `ingestion-checkpoint.json` — resumable cursor

## Next cursor

Dialogue combined record **336/747**:

- DIAL `0504DF3B`
- Owning quest: `05039182 _Lull_SQ_Wailway`

## Provenance rule

Statements from Wheels of Lull remain scoped to `tes.mod.wheels-of-lull`. Dialogue, books, quest text, and implementation records can support continuity-specific claims, but they do not automatically establish Bethesda-canon metaphysics or history. Character testimony remains attributed when the source presents it as testimony rather than objective narration.
