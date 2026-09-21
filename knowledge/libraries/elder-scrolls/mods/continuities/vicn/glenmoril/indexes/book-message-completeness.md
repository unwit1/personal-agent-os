# GLENMORIL BOOK / MESG completeness inventory

Source: raw `Glenmoril.esm`.

## BOOK records

Total BOOK records: **264**  
All 264 contain non-empty `DESC` text.

Raw BOOK text size: **161,476 characters**.

### Working provenance / function classes

- Yelem notes: **54**
- GLENMORIL narrative/original candidates: **43**
- reused official/reference: **30**
- mechanical BOOK records: **136**
- debug-structural: **1**

This matches the older BOOK completeness ledger and supersedes the provisional overlapping classification.

## Exact text progress

Already exact before this audit:
- all **54 / 54 Yelem notes**
- Black Book: Debug normalized structurally
- several high-priority letters/texts already summarized or partially transcribed

New exact source files imported during this audit:
- original/revision batch 01: **11**
- original/revision batch 02: **9**
- Professor Y / Secret Tale family: **13**
- remaining narrative/reference/debug source-file gap: **11**

**44 exact BOOK source files were added during this audit.**

The final 11 include:
- The Stray Khajiit of Chorrol
- Note from Lalanoah
- Black Book: Manners of Communion
- Black Book: KRMT
- Black Book: Debug
- Letter from Lalanoah
- Threatening Letter from Ja'zel
- Ancient Note
- Letter from Ja'zel
- Chronicles of the Hero of Kvatch, Volume III
- Snowmelt

This means the GLENMORIL-specific narrative/reference candidate layer now has exact ESM text preserved in the repository rather than relying on summaries alone.

## Reused official/reference material

The `zzzRevBookESO*` family plus `The Elusive Traveler` remains source-addressable but should resolve to canonical official/reference texts unless comparison proves Vicn-specific changes.

Do not attribute those texts to Vicn as original authorship.

## Mechanical BOOK records

The **136 mechanical BOOK records** remain the major BOOK-completeness backlog.

They include:
- spell tomes;
- hearts;
- ashes;
- persona coins;
- Dreamstride records;
- Lexicons;
- Heart Stones;
- guts/taproots;
- summon-token and related gameplay records.

Many have short but potentially lore-bearing descriptions.

They should be preserved in a compact machine-readable dataset rather than expanded into hundreds of prose pages.

## MESG records

Total MESG records: **144**

- non-empty `DESC`: **127**
- records with `ITXT` choices: **65**
- combined readable DESC + ITXT text: **18,667 characters**

### MESG batch 01

A high-value exact JSONL dataset now preserves **27 lore-bearing MESG records**:
- Egg parameter/status display;
- two Jhunal/Hamah sealing tablets;
- five early Maiden invocations;
- five later Maiden dossiers;
- thirteen revision data records;
- Laza-corpse data.

Path:
`data/messages/high-value-messages.jsonl`

## Next BOOK priority

Create a compact exact dataset for the **136 mechanical BOOK records**.

## Next MESG priorities

1. remaining lore-bearing quest/data messages
2. menu records whose choices encode story state
3. debug/error/UI-only records
4. final machine-readable 144-record completeness ledger
