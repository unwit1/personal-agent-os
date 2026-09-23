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
- **116/337 DIAL** topics and **119/410 INFO** records preserved in physical plugin order.
- **235/747 combined dialogue records** are now ingested.
- **300 prioritized source records** are checkpointed overall.

## Dialogue evidence already preserved

This pass covers the end of the Brass Forest aftermath, the attack on Lull-Mor, Archeron's reveal beneath the Fyr disguise, Memory's intervention, and Llavados' extended explanation of Memory.

Notable continuity-scoped testimony includes:

- Numinar initially concludes that the player is the saboteur and a Thalmor agent.
- The figure posing as Divayth Fyr reveals himself as Archeron and says he used the fabricants' excavation to reach the Stone.
- Memory appears after the player's fall and tells them they are needed.
- Llavados says his apparent madness is partly a facade and that he knows more than the other Chronographers.
- Llavados identifies Memory as Sotha Sil's final creation: a child of mer, machine, and Lullian magic.
- Llavados says a future disaster will destroy the world and that Memory is intended to help people survive it and build a new world.
- Llavados says the Towers sustain Memory as well as stabilizing Nirn, and that destruction of Snow-Throat would kill her.
- Llavados says Archeron's understanding of the Wheels of Lull lets him alter himself and his experiments in ways that make them resistant to ordinary destruction.

These remain attributed source statements rather than automatic Bethesda-canon conclusions.

## Raw corpus

- `raw/source-records-0001-0005.jsonl` through `raw/source-records-0096-0100.jsonl` — records 1-100
- `raw/source-records-0101-0150.jsonl.gz` — records 101-150
- `raw/source-records-0151-0200.jsonl.gz` — records 151-200
- `raw/source-records-0201-0250.jsonl.gz` — records 201-250
- `raw/source-records-0251-0300.jsonl.gz` — records 251-300
- `raw/record-counts.json` — complete plugin record inventory
- `source-manifest.json` — extraction policy and corpus state
- `ingestion-checkpoint.json` — resumable cursor

## Next cursor

Dialogue combined record **236/747**:

- DIAL `0503E1A8`
- Editor ID: `_Lull_MQ06_Llavados8`
- Topic: `So I just escape, reach Archeron, and kill him, simple.`
- Owning quest: `05005912 _Lull_MQ06`

## Provenance rule

Statements from Wheels of Lull remain scoped to `tes.mod.wheels-of-lull`. Dialogue, books, quest text, and implementation records can support continuity-specific claims, but they do not automatically establish Bethesda-canon metaphysics or history. Character testimony remains attributed when the source presents it as testimony rather than objective narration.
