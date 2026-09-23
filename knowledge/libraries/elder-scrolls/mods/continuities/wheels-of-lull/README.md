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
- **66/337 DIAL** topics and **69/410 INFO** records preserved in physical plugin order.
- **135/747 combined dialogue records** are now ingested.
- **200 prioritized source records** are checkpointed overall.

## Dialogue evidence already preserved

The corpus now extends through Archeron's Whitehorn dialogue and the beginning of the Boiling Foundry sequence.

Notable continuity-scoped testimony now includes:

- Whitehorn personnel describe Archeron as a former Psijic and skilled enchanter.
- Archeron explicitly discusses the Thalmor goal of destroying the world and frames it as a return to immortal pre-mortal forms.
- Archeron identifies Aetherial travel, soul gems, and the Wheels of Lull among his research interests.
- Llavados describes local tears in spacetime and places where the Wheels of Lull "poke out."
- Numinar identifies the Stone as the anchor that keeps a Tower working and says destruction of a Stone causes its Tower to cease operating.
- Numinar says loss of Towers destabilizes Nirn and identifies Snow-Throat as one of the last remaining Towers.
- Numinar attributes Archeron's unusual access to a combination of Sotha Sil's writings and Psijic training.
- The Boiling Foundry sequence introduces titanium as "the blood of Stendarr" and as a material capable of cutting through the Wheels of Lull.

These remain attributed source statements rather than automatic Bethesda-canon conclusions.

## Raw corpus

- `raw/source-records-0001-0005.jsonl` through `raw/source-records-0096-0100.jsonl` — records 1-100
- `raw/source-records-0101-0150.jsonl.gz` — records 101-150
- `raw/source-records-0151-0200.jsonl.gz` — records 151-200
- `raw/record-counts.json` — complete plugin record inventory
- `source-manifest.json` — extraction policy and corpus state
- `ingestion-checkpoint.json` — resumable cursor

## Next cursor

Dialogue combined record **136/747**:

- DIAL `0502EC86`
- Editor ID: `_Lull_MQ04_DoItMyself`
- Topic: `Why not do it yourself?`
- Owning quest: `05005910 _Lull_MQ04`

## Provenance rule

Statements from Wheels of Lull remain scoped to `tes.mod.wheels-of-lull`. Dialogue, books, quest text, and implementation records can support continuity-specific claims, but they do not automatically establish Bethesda-canon metaphysics or history. Character testimony remains attributed when the source presents it as testimony rather than objective narration.
