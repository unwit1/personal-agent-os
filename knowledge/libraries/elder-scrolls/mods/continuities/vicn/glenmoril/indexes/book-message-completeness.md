# GLENMORIL BOOK / MESG completeness inventory

Source: raw `Glenmoril.esm`.

## BOOK records

Total BOOK records: **264**
All 264 contain non-empty `DESC` text.

Raw BOOK text size: **161,476 characters**.

### Provenance / function classes

- Yelem notes: **54**
- GLENMORIL narrative/original candidates: **43**
- reused official/reference: **30**
- mechanical BOOK records: **136**
- debug-structural: **1**

Total: **264 / 264 classified**.

## Exact BOOK progress

- Yelem notes: **54 / 54 exact**
- narrative/reference audit: exact ESM source text preserved for the GLENMORIL-specific candidate layer
- mechanical records: **136 / 136 exact**
- debug book: normalized
- reused official/reference records: source-addressable and classified; canonical-source comparison remains provenance work

Mechanical exact dataset:
`data/books/mechanical-books-01.jsonl`
through
`data/books/mechanical-books-17.jsonl`.

The mechanical BOOK backlog is therefore **closed**.

## MESG records

Total MESG records: **144**

- non-empty `DESC`: **127**
- records with `ITXT` choices: **65**
- combined readable DESC + ITXT text: **18,667 characters**

### Existing MESG high-value pass

The earlier high-value pass identified **27 lore-bearing MESG records**, including:
- Egg parameter/status display;
- Jhunal/Hamah sealing tablets;
- Maiden invocations/dossiers;
- revision data records;
- Laza-corpse data.

## Current priority

Build a deterministic **144 / 144 exact MESG ledger** preserving:
- source ID;
- EditorID;
- title when present;
- exact `DESC`;
- ordered `ITXT` choice text.

Then classify:
1. lore-bearing/data;
2. story-state menu;
3. gameplay/system;
4. debug/error/UI-only.

This replaces sampling with full MESG completeness.
