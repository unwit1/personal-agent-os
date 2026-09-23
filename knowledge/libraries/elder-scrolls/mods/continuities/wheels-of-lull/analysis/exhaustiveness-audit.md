# Wheels of Lull Exhaustiveness Audit

Continuity: `tes.mod.wheels-of-lull`  
Source: `WheelsOfLull.esp`  
SHA-256: `230b102cd1ec13f2d104da8803d32c19227ef519eaca766a00b076c322aa78bb`  
Audit date: 2026-09-23

## Scope and result

The verified source ESP was traversed physically from byte 0 through EOF with recursive TES5 `GRUP` handling, compressed-record inflation, `XXXX` extended subrecord sizes, and source offsets retained. The traversal reproduced the repository inventory exactly: **36,824 records**, including the original **1,090-record core lore corpus**.

The audit then inspected every record class outside the original core corpus for safely decodable text-bearing fields and also ran a deep printable-string sweep over subrecord payloads, including VMAD/script payloads.

Final result:

- **1,090** core narrative/source records;
- **370** unique implementation-evidence records outside that core;
- **1,460** unique persisted source-evidence records total;
- **16** field augmentations attached to already-counted records;
- **0** natural-language VMAD/script payloads found by the deep sweep.

## Implementation-evidence corpus

The first supplement pass preserved 328 omitted records. A final exhaustive pass added every remaining record class with player-facing `FULL` text, including cosmetic labels because this layer is explicitly implementation evidence rather than narrative canon.

| Type | Records |
| --- | ---: |
| ACTI | 43 |
| ALCH | 2 |
| AMMO | 2 |
| ARMO | 57 |
| CLFM | 3 |
| CONT | 8 |
| DOOR | 7 |
| ENCH | 10 |
| FACT | 6 |
| FURN | 1 |
| HDPT | 15 |
| KEYM | 14 |
| MGEF | 33 |
| MISC | 36 |
| PERK | 5 |
| PROJ | 2 |
| RACE | 26 |
| REFR | 3 |
| SHOU | 1 |
| SPEL | 35 |
| TACT | 7 |
| VTYP | 20 |
| WEAP | 33 |
| WRLD | 1 |
| **Total** | **370** |

Storage:
- base supplement: `raw/implementation-text-supplement.jsonl.gz` — 328 records;
- final augmentation: `raw/source-evidence-augmentation.jsonl` — 42 additional records plus 16 field augmentations;
- machine manifest: `analysis/implementation-text-supplement.json`.

The base deterministic gzip SHA-256 remains `e7ce7982e058679f1c61fc5360a506d0f330fb3f02751a5e871d4437c5ad3c8f`.

## Deep text-field closure

The embedded-string pass produced **2,008 phrase candidates / 1,796 unique strings**. After classification:

- normal BOOK, QUST, DIAL, INFO, CELL, LCTN, MESG, and NPC text was already represented in the core corpus;
- **14 MGEF `DNAM` descriptions** were genuine omitted player-facing prose and are now preserved as field augmentations;
- one INFO `NAM2` voice-direction string — “courier making a delivery - cheerful, then appropriately somber” — is now preserved;
- one INFO `RNAM` prompt — “Ask the first riddle.” — is now preserved;
- **no natural-language VMAD/script payloads** were found;
- apparent text from `MHDT`, `NVNM`, `DATA`, and `XRGD` binary regions was rejected as binary false positives.

This closes the text-field gap exposed by the first implementation supplement.

## High-value additions

The implementation layer includes:

- all 6 faction records, including **Chronographers** and **Whitehorn Thalmor**;
- all 7 talking-activator records, including **Train**, **The Skull**, **The Cartwright**, and **The Analyst**;
- all 20 custom voice-type records used as dialogue-resolution evidence;
- all 10 named enchantment records and all 14 player-facing key records;
- player-facing names/descriptions for Lullian, Clockwork, memodermic, harquebus, Chronographer, Watchman, security-pack, visor, Unwinder, Rod of Ohm, Artophysical Manipulator, and related technology;
- creature/race implementation labels such as **Familyman**, **Bonestrider**, **Machinary**, **The Whistling King**, and **Old Tho Mahalis**;
- three named placed references missed by the original type filter: **Whitehorn Pass**, **Stonehole Mine**, and **Strange Shore**;
- cosmetic implementation evidence for Memory/Yagrum/Fyr head parts and color forms, retained as implementation evidence rather than lore claims.

The TES4 header independently confirms author `Trainwiz`, plugin version text `6.0.0.3`, the phrase “That which turns, turns well,” and the listed Chronographer Maintenance Team update credits. This is source metadata, not in-world lore.

## Exclusion policy

The audit does **not** bulk-promote implementation-only records into narrative lore. The largest excluded classes are references, navmeshes, statics, packages, dialogue branches/views, constructible objects, texture/model records, leveled lists, art/effect records, and similar engine structures. Their strings are predominantly editor identifiers, asset paths, procedural parameter names, animation events, or duplicate display labels.

In particular:

- **34,042 REFR** records are not treated as 34,042 lore documents; only the three REFR records with distinct player-facing `FULL` names are represented in the implementation supplement;
- model/texture paths are implementation provenance, not lore assertions;
- PACK parameter strings such as `Location`, `Bool`, `Float`, `Topic`, and `SingleRef` are procedure metadata;
- NAVM/CELL/WRLD binary payloads that happen to contain printable byte runs are not text evidence;
- HDPT/CLFM labels are preserved only as explicitly cosmetic implementation evidence;
- duplicated vanilla-derived descriptions must not be mistaken for new Wheels-specific claims.

## Integrity closure

The two previously unreadable dialogue shards were deterministically regenerated from this exact ESP. Their recovered ranges contain **52 INFO** records. Strict CTDA resolution reproduces the old readable baseline exactly (**288 resolved / 70 unresolved across the prior 358 INFO**) and adds **44 resolved / 8 unresolved** from the repaired ranges, for **332 resolved / 78 intentionally unresolved across all 410 INFO**.

This audit exhausts the currently supplied ESP as a local source. Remaining work is external provenance/edition research for historical BOOK witnesses and an optional fresh checkout rebuild of deterministic retrieval derivatives—not unprocessed Wheels of Lull plugin content.
