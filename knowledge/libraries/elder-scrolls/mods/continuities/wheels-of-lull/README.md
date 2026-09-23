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
- **139/337 DIAL** topics and **146/410 INFO** records preserved in physical plugin order.
- **285/747 combined dialogue records** are now ingested.
- **350 prioritized source records** are checkpointed overall.

## Dialogue evidence already preserved

This pass completes more of Llavados' Bottom-of-the-World guidance, the final Archeron confrontation, the post-fight Llavados/Numinar material, and transitions into ambient guard dialogue.

Notable continuity-scoped testimony includes:

- Llavados says Archeron cannot be killed by ordinary means because he has "hacked" himself into the Wheels of Lull.
- Llavados says equipment at the Bottom of the World can "unwind" Archeron's modifications.
- After Archeron's defeat, Llavados describes the location as past the bottom of the world, the core of Nirn, Magnus' workshop, Sotha Sil's central mainframe, and Memory's room.
- Llavados says Archeron's soul became integrated into the world mechanism after death.
- Llavados hints that he has walked "in the shoes of a god," calls himself a godfather to Memory and an architect, and says he and the Dragonborn will meet again at Landfall.
- Numinar reiterates that the Chronographers fix problems and move on rather than celebrating them.
- Archeron's combat taunts claim control of the World Mechanism and compare his strength to Sotha Sil.

These remain attributed source statements rather than automatic Bethesda-canon conclusions.

## Raw corpus

- `raw/source-records-0001-0005.jsonl` through `raw/source-records-0096-0100.jsonl` — records 1-100
- `raw/source-records-0101-0150.jsonl.gz` — records 101-150
- `raw/source-records-0151-0200.jsonl.gz` — records 151-200
- `raw/source-records-0201-0250.jsonl.gz` — records 201-250
- `raw/source-records-0251-0300.jsonl.gz` — records 251-300
- `raw/source-records-0301-0350.jsonl.gz` — records 301-350
- `raw/record-counts.json` — complete plugin record inventory
- `source-manifest.json` — extraction policy and corpus state
- `ingestion-checkpoint.json` — resumable cursor

## Next cursor

Dialogue combined record **286/747**:

- INFO `050488A4`
- Parent topic: `050488A2 _Lull_Misc_GuardGreetings`
- Owning quest: `05005918 _Lull_Misc`

## Provenance rule

Statements from Wheels of Lull remain scoped to `tes.mod.wheels-of-lull`. Dialogue, books, quest text, and implementation records can support continuity-specific claims, but they do not automatically establish Bethesda-canon metaphysics or history. Character testimony remains attributed when the source presents it as testimony rather than objective narration.
