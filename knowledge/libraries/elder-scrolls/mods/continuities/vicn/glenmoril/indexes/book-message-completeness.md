# GLENMORIL BOOK / MESG completeness inventory

Source: raw `Glenmoril.esm`.
SHA-256: `5669018c81acf13147ff489f486963ecc3c57515a73ed9afd210c7ede85e1cc8`

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

Total MESG records: **144**.

- non-empty `DESC`: **127**
- records with `ITXT` choices: **65**
- combined readable `DESC` + `ITXT` text: **18,667 characters**
- exact source-addressable rows preserved: **144 / 144**

Exact dataset:
`data/messages/messages-01.jsonl`
through
`data/messages/messages-06.jsonl`.

Each shard contains **24** records, so **6 × 24 = 144 / 144**.

Every row preserves:
- source plugin;
- stable local source ID;
- observed FormID;
- record type;
- EditorID;
- title when present;
- continuity;
- exact `DESC`;
- ordered `ITXT` choices;
- a working retrieval category.

### Working MESG categories

| working category | count |
|---|---:|
| lore-data-candidate | **67** |
| plain-message | **38** |
| menu-story-or-gameplay | **29** |
| system-debug | **10** |

These categories are retrieval aids, not canon-strength labels. A menu or debug-classified record may still contain lore-bearing wording, and lore-data candidates still require contextual interpretation before promotion into entity/relationship claims.

## MESG-layer status

**Raw MESG inventory: 144 / 144.**

**Exact MESG preservation: 144 / 144.**

The prior sampling backlog is closed. Remaining work is semantic promotion: connect high-value messages to characters, locations, concepts, quests, contradictions, and provenance-aware claims without treating UI text or in-world claims as automatically objective fact.
