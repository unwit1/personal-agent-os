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
- **196/337 DIAL** topics and **239/410 INFO** records preserved in physical plugin order.
- **435/747 combined dialogue records** are now ingested.
- **500 prioritized source records** are checkpointed overall.

## Dialogue evidence already preserved

This pass completes the immediate Arms Merchant purchase responses, covers Avarri's clockwork crafting requests, and reaches the opening Dye Trader interaction.

Notable continuity-scoped material includes:

- The Arms Merchant supports purchasable permanent fabricant augmentations, including the Aetherial Glass Eye, Secondary Mystic Heart, Quartz Ligaments, and Sehtian Hydraulics.
- Avarri can construct multiple clockwork weapons from supplied materials, including a mace, drill, sword, clockwork shots, several specialized harquebuses, and an experimental Lullian harquebus.
- The crafting dialogue is linked to the existing in-plugin crafting-list books already preserved in the complete BOOK corpus.
- The Dye Trader sequence begins immediately after this batch.

These remain source-scoped implementation/dialogue evidence rather than automatic Bethesda-canon conclusions.

## Raw corpus

- `raw/source-records-0001-0005.jsonl` through `raw/source-records-0096-0100.jsonl` — records 1-100
- `raw/source-records-0101-0150.jsonl.gz` — records 101-150
- `raw/source-records-0151-0200.jsonl.gz` — records 151-200
- `raw/source-records-0201-0250.jsonl.gz` — records 201-250
- `raw/source-records-0251-0300.jsonl.gz` — records 251-300
- `raw/source-records-0301-0350.jsonl.gz` — records 301-350
- `raw/source-records-0351-0400.jsonl.gz` — records 351-400
- `raw/source-records-0401-0450.jsonl.gz` — records 401-450
- `raw/source-records-0451-0500.jsonl.gz` — records 451-500
- `raw/record-counts.json` — complete plugin record inventory
- `source-manifest.json` — extraction policy and corpus state
- `ingestion-checkpoint.json` — resumable cursor

## Next cursor

Dialogue combined record **436/747**:

- INFO `0527701E`
- Parent topic: `0527701D _Lull_SQ_DyeTrader_IntroTopic`
- Owning quest: `055400D9 _Lull_SQ_DyeTrader`
- Response begins: `(Beeping that implies a trade request)`

## Provenance rule

Statements from Wheels of Lull remain scoped to `tes.mod.wheels-of-lull`. Dialogue, books, quest text, and implementation records can support continuity-specific claims, but they do not automatically establish Bethesda-canon metaphysics or history. Character testimony remains attributed when the source presents it as testimony rather than objective narration.
