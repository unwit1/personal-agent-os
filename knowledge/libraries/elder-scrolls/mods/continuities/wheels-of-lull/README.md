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
- **91/337 DIAL** topics and **94/410 INFO** records preserved in physical plugin order.
- **185/747 combined dialogue records** are now ingested.
- **250 prioritized source records** are checkpointed overall.

## Dialogue evidence already preserved

The corpus now reaches the first Divayth Fyr / Yagrum Bagarn sequence following the Brass Forest and Unwound encounter.

Notable continuity-scoped testimony in this pass includes:

- Numinar says the Boiling Foundry lies in the deeper parts of Sotha Sil and was once connected to Lull-Mor by an elevator station.
- The drilling teams break into previously unknown catacombs of Sotha Sil populated by hostile undead fabricants.
- Numinar characterizes those dead fabricants as ancestors who understand the needs of the machine and should not normally attack the Chronographers.
- Divayth Fyr introduces himself as an old friend of Sotha Sil and identifies his companion as Yagrum Bagarn.
- Yagrum identifies himself as the last living Dwemer.
- Fyr attributes Yagrum's Third Era physical condition to Corprus and says the disease receded after Dagoth Ur's demise enough for Fyr to restore him.
- The characters warn that a saboteur may be active and that a rogue fabricant could be dangerous.

These remain attributed source statements rather than automatic Bethesda-canon conclusions.

## Raw corpus

- `raw/source-records-0001-0005.jsonl` through `raw/source-records-0096-0100.jsonl` — records 1-100
- `raw/source-records-0101-0150.jsonl.gz` — records 101-150
- `raw/source-records-0151-0200.jsonl.gz` — records 151-200
- `raw/source-records-0201-0250.jsonl.gz` — records 201-250
- `raw/record-counts.json` — complete plugin record inventory
- `source-manifest.json` — extraction policy and corpus state
- `ingestion-checkpoint.json` — resumable cursor

## Next cursor

Dialogue combined record **186/747**:

- DIAL `05038EE7`
- Editor ID: `_Lull_MQ05_FinalTopicTopic`
- Owning quest: `05005911 _Lull_MQ05`

## Provenance rule

Statements from Wheels of Lull remain scoped to `tes.mod.wheels-of-lull`. Dialogue, books, quest text, and implementation records can support continuity-specific claims, but they do not automatically establish Bethesda-canon metaphysics or history. Character testimony remains attributed when the source presents it as testimony rather than objective narration.
