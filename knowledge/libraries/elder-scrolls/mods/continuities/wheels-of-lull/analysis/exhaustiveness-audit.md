# Wheels of Lull Exhaustiveness Audit

Continuity: `tes.mod.wheels-of-lull`  
Source: `WheelsOfLull.esp`  
SHA-256: `230b102cd1ec13f2d104da8803d32c19227ef519eaca766a00b076c322aa78bb`  
Audit date: 2026-09-23

## Scope and result

The verified source ESP was traversed physically from byte 0 through EOF with recursive TES5 `GRUP` handling, compressed-record inflation, `XXXX` extended subrecord sizes, and source offsets retained. The traversal reproduced the repository inventory exactly: **36,824 records**, including the original **1,090-record core lore corpus**.

The audit then inspected every record class outside the original core corpus for safely decodable text-bearing fields and strict printable NUL-terminated strings. It found **1,328 omitted records** with at least one safe editor/name/description field and **5,290 strict C-string instances** (2,429 unique strings). Most of those strings are implementation metadata: editor IDs, model/texture paths, package parameter labels, animation event names, and engine wiring. Those are not promoted as lore claims.

A separate implementation-text supplement now preserves the **328 omitted records** that are either player-facing or materially useful for lore/source interpretation:

| Type | Records |
| --- | ---: |
| ARMO | 57 |
| ACTI | 43 |
| MISC | 36 |
| SPEL | 35 |
| MGEF | 33 |
| WEAP | 33 |
| RACE | 26 |
| VTYP | 20 |
| CONT | 8 |
| DOOR | 7 |
| TACT | 7 |
| FACT | 6 |
| PERK | 5 |
| REFR | 3 |
| ALCH | 2 |
| AMMO | 2 |
| PROJ | 2 |
| FURN | 1 |
| SHOU | 1 |
| WRLD | 1 |
| **Total** | **328** |

Canonical supplemental file: `raw/implementation-text-supplement.jsonl.gz`  
Deterministic gzip SHA-256: `e7ce7982e058679f1c61fc5360a506d0f330fb3f02751a5e871d4437c5ad3c8f`

## High-value additions

The supplement closes source-evidence gaps that the original priority set left implicit:

- all 6 faction records, including **Chronographers** and **Whitehorn Thalmor**;
- all 7 talking-activator records, including **Train**, **The Skull**, **The Cartwright**, and **The Analyst**;
- all 20 custom voice-type records used as dialogue-resolution evidence;
- player-facing names/descriptions for Lullian, Clockwork, memodermic, harquebus, Chronographer, Watchman, security-pack, visor, Unwinder, Rod of Ohm, Artophysical Manipulator, and related technology;
- creature/race implementation labels such as **Familyman**, **Bonestrider**, **Machinary**, **The Whistling King**, and **Old Tho Mahalis**;
- three named placed references missed by the original type filter: **Whitehorn Pass**, **Stonehole Mine**, and **Strange Shore**.

The TES4 header independently confirms author `Trainwiz`, plugin version text `6.0.0.3`, the phrase “That which turns, turns well,” and the listed Chronographer Maintenance Team update credits. This is source metadata, not in-world lore.

## Exclusion policy

The audit deliberately does **not** bulk-promote implementation-only records into narrative lore. The largest excluded classes are references, navmeshes, statics, packages, dialogue branches/views, constructible objects, texture/model records, leveled lists, art/effect records, and similar engine structures. They remain recoverable from the verified ESP and were checked for text, but their strings are predominantly editor identifiers, asset paths, procedural parameter names, or duplicate display labels.

In particular:

- **34,042 REFR** records are not treated as 34,042 lore documents; only the three REFR records with distinct player-facing `FULL` names were added to the supplement.
- model/texture paths are implementation provenance, not lore assertions;
- PACK `ANAM` strings such as `Location`, `Bool`, `Float`, `Topic`, and `SingleRef` are procedure metadata;
- duplicated vanilla race descriptions are retained only where the record itself is useful for implementation identity and must not be mistaken for new Wheels-specific claims.

## Integrity closure

The two previously unreadable dialogue shards were deterministically regenerated from this exact ESP. Their recovered ranges contain **52 INFO** records. Strict CTDA resolution reproduces the old readable baseline exactly (**288 resolved / 70 unresolved across the prior 358 INFO**) and adds **44 resolved / 8 unresolved** from the repaired ranges, for **332 resolved / 78 intentionally unresolved across all 410 INFO**.

This audit exhausts the currently supplied ESP as a local source: remaining open work is external provenance/edition research for historical BOOK witnesses, not unprocessed Wheels of Lull plugin content.
