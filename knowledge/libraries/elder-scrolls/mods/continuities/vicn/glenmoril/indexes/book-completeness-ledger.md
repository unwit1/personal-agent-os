# GLENMORIL BOOK completeness ledger

Source: raw `Glenmoril.esm`
SHA-256: `5669018c81acf13147ff489f486963ecc3c57515a73ed9afd210c7ede85e1cc8`

## Raw inventory

**264 BOOK records**
**264 text-bearing**
**0 empty**

## Classification

| class | count | current handling |
|---|---:|---|
| Yelem notes | **54** | **54/54 exact-transcribed** |
| GLENMORIL narrative/original candidates | **43** | exact ESM source text preserved by the narrative/reference BOOK audit |
| reused official/reference | **30** | source occurrences classified; resolve against canonical official/reference copies without attributing authorship to Vicn |
| mechanical BOOK records | **136** | **136/136 exact-preserved in 17 JSONL shards** |
| debug-structural | **1** | Black Book: Debug normalized |

Total: **264**

## Mechanical exact dataset

Paths:
`data/books/mechanical-books-01.jsonl`
through
`data/books/mechanical-books-17.jsonl`

Each shard contains 8 source-addressable BOOK records.

**17 × 8 = 136 / 136**

Every row preserves:
- source plugin;
- stable local source ID;
- observed FormID;
- record type;
- EditorID;
- title;
- continuity;
- provenance class;
- exact ESM `DESC` text.

## Yelem families

Pailune 6; Sithis 8; Lizard 4; Laza 8; Kyne 9; Shezarr 13; CsO 6.

## Narrative/original candidates — 43

Includes the Yelem School/Pailune/Laza/Owl/Ja'bal books, Professor Y family, Book of Radiance, Lalanoah/Ja'zel letters, Romion's last note, Words of Jhunal, Snowmelt, and related source-specific texts.

## Reused/reference set — 30

The `zzzRevBookESO*` family plus `zzzRevESOElusiveTraveler`.

These remain GLENMORIL source occurrences but should resolve to canonical official/reference texts where possible. Do not promote reused ESO text as Vicn-original authorship.

## BOOK-layer status

**Raw classification: 264 / 264.**

**Mechanical exact-text preservation: 136 / 136.**

**Yelem exact-text preservation: 54 / 54.**

The remaining BOOK work is provenance/reference reconciliation for reused texts and retrieval/claim promotion, not discovery of unclassified BOOK records.
