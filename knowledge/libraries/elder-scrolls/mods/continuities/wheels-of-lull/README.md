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
- **182/337 DIAL** topics and **203/410 INFO** records preserved in physical plugin order.
- **385/747 combined dialogue records** are now ingested.
- **450 prioritized source records** are checkpointed overall.

## Dialogue evidence already preserved

This pass finishes the Wailway farewell and moves through additional Fyr, Yagrum, Avarri/Stoker, and Arms Merchant material.

Notable continuity-scoped testimony includes:

- The Wailway locomotive welcomes its destruction as release from its engine-bound existence.
- Divayth Fyr describes himself as a millennia-old wizard lord with experience in Sotha Sil's mechanisms.
- Yagrum Bagarn explicitly titles himself the Last Living Dwarf after years of finding no other Dwemer.
- Avarri says he bound the Stoker into his mind to learn clockwork smithing; the Stoker identifies itself as a foundry-running, steel-shaping intelligence.
- Avarri describes deep-down protective packs as standard equipment for soldiers.
- Ganaran-21, the Arms Merchant, identifies himself as a fabricant using an FRF to speak.
- The Arms Merchant describes a clandestine trade in recovered fabricant body parts and permanent augmentations, including aetherial glass eyes, secondary mystic hearts, and quartz ligaments.

These remain attributed source statements rather than automatic Bethesda-canon conclusions.

## Raw corpus

- `raw/source-records-0001-0005.jsonl` through `raw/source-records-0096-0100.jsonl` — records 1-100
- `raw/source-records-0101-0150.jsonl.gz` — records 101-150
- `raw/source-records-0151-0200.jsonl.gz` — records 151-200
- `raw/source-records-0201-0250.jsonl.gz` — records 201-250
- `raw/source-records-0251-0300.jsonl.gz` — records 251-300
- `raw/source-records-0301-0350.jsonl.gz` — records 301-350
- `raw/source-records-0351-0400.jsonl.gz` — records 351-400
- `raw/source-records-0401-0450.jsonl.gz` — records 401-450
- `raw/record-counts.json` — complete plugin record inventory
- `source-manifest.json` — extraction policy and corpus state
- `ingestion-checkpoint.json` — resumable cursor

## Next cursor

Dialogue combined record **386/747**:

- INFO `0526796C`
- Parent topic: `05267904 _Lull_SQ_ArmsMerchant_GetEye`
- Topic: `(Purchase the Aetherial Glass Eye)`
- Owning quest: `055400DA _Lull_SQ_ArmsMerchant`

## Provenance rule

Statements from Wheels of Lull remain scoped to `tes.mod.wheels-of-lull`. Dialogue, books, quest text, and implementation records can support continuity-specific claims, but they do not automatically establish Bethesda-canon metaphysics or history. Character testimony remains attributed when the source presents it as testimony rather than objective narration.
