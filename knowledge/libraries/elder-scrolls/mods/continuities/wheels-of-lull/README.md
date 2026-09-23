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
- **216/337 DIAL** topics and **269/410 INFO** records preserved in physical plugin order.
- **485/747 combined dialogue records** are now ingested.
- **550 prioritized source records** are checkpointed overall.

## Dialogue evidence already preserved

This pass completes the Dye Trader exchange, adds the remaining Cartwright riddle outcomes in this section, and reaches a concentrated block of Memory ambient dialogue.

Notable continuity-scoped material includes:

- The Dye Trader requests human hearts in exchange for colored dyes and refuses to explain why.
- The Cartwright continues to treat riddles as lethal gatekeeping for tram access.
- Memory says: "Know Love to avoid the Landfall."
- Memory identifies herself as "the mage" and "the clockmaker."
- Memory says the oceans hold thoughts and those thoughts hold salvation.
- Memory predicts that the Thalmor will ultimately win.
- Memory says "It will come in the form of screaming brass."
- Memory says that when the world cracks open, "at last we will know our destiny."

These remain attributed and, where appropriate, cryptic source statements rather than automatic Bethesda-canon conclusions.

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
- `raw/source-records-0501-0550.jsonl.gz` — records 501-550
- `raw/record-counts.json` — complete plugin record inventory
- `source-manifest.json` — extraction policy and corpus state
- `ingestion-checkpoint.json` — resumable cursor

## Next cursor

Dialogue combined record **486/747**:

- INFO `0529FCA1`
- Parent topic: `0529FC98 _Lull_MQ07_MemoryGreetings`
- Owning quest: `05005913 _Lull_MQ07`
- Response: `The c0da does not bend. The Digitals have seen to that.`

## Provenance rule

Statements from Wheels of Lull remain scoped to `tes.mod.wheels-of-lull`. Dialogue, books, quest text, and implementation records can support continuity-specific claims, but they do not automatically establish Bethesda-canon metaphysics or history. Character testimony remains attributed when the source presents it as testimony rather than objective narration.
