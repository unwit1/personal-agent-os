# GLENMORIL BOOK / MESG completeness inventory

Source: raw `Glenmoril.esm`.

## BOOK records

Total BOOK records: **264**  
All 264 contain non-empty `DESC` text.

Raw BOOK text size: **161,476 characters**.

### Working provenance / function classes

- mechanical spell/heart/ash/tome records: **122**
- Yelem Note family: **54**
- reused ESO book records: **29**
- Professor Y / Secret Tale family: **13**
- Ja'bal cycle: **5**
- Book of Radiance cycle: **4**
- other GLENMORIL-original/revision books, notes, letters and black books: **35**
- other/reused edge records: **2**

These classes are operational and may be refined as provenance is verified.

## Exact text import progress

### Original-book batch 01 — 11 records
Imported:
- The Yelem School
- A City Sunken in the Desert
- The Three Owls
- Laza and the Owls
- Rolly-Polly, Ja'bal the Cat
- Ja'bal and the Chickens
- Ja'bal and the Chicks
- Ja'bal and the Eggs
- The Book of Atatami
- Words of Jhunal
- The Blue Star

### Original-book batch 02 — 9 records
Imported:
- Romion's Last Note
- Book of Radiance, Vols. 1–4
- Laza
- The People of Grasslands
- To Slumber
- Black Book: The Gardener

### Professor Y / Secret Tale batch — 13 records
Imported:
- Professor Y, Vols. 1–5
- The Secret Tale of Professor Y, Vols. 1–7
- An Overview of the C0DA Document

**New exact BOOK texts imported during this audit: 33.**

Previously normalized families such as the Yelem Notes, Black Book: Debug, Threatening Letter from Ja'zel and Letter from Lalanoah remain separate existing source material and should not be double-counted merely because they also occur in the 264-record raw inventory.

## Professor Y evidence discipline

The Professor Y family mixes:
- direct observations of physical remains/locations;
- experimental interpretations;
- deliberately speculative metaphysics;
- future/past time-displacement reasoning;
- jokes and unreliable extrapolation.

Promote direct observations separately from Professor Y's hypotheses.

Examples:
- direct: a living ship with Argonian-compatible anatomy is examined;
- attributed inference: the Hist built it;
- direct: Hamah is physically present as Professor Y's captive specimen;
- attributed inference/testimony: her soul belonged to a prior Snow-Elf experiment and Anem rebirthed her;
- direct: C0DA text is said to be stored in Apocrypha with an author name obscured from perception;
- attributed inference: the author is a renowned mystic hiding research inside fiction.

## Reused official material

The `zzzRevBookESO*` family remains in the raw inventory but should use provenance class **reused-official** unless record comparison shows modified text.

Do not promote reused ESO text as GLENMORIL-original authorship.

## Mechanical BOOK records

The 122 spell/heart/ash/lexicon/dreamstride-style BOOK records require a separate pass.

Many are gameplay containers with short descriptive lore rather than conventional readable books. Preserve their `DESC` text, but index them separately from narrative books.

## MESG records

Total MESG records: **144**

- with non-empty `DESC`: **127**
- with one or more `ITXT` menu-choice strings: **65**
- combined readable DESC + ITXT text: **18,667 characters**

The MESG layer includes:
- menu choices;
- debug/error prompts;
- item/character data summaries;
- tablets and warnings;
- revision/revenant data displays;
- quest interfaces.

## Next BOOK priorities

1. remaining GLENMORIL-original/revision books and letters
2. mechanical spell/heart/ash descriptions
3. reused-official verification by text comparison rather than blind duplication

## Next MESG priorities

1. non-debug narrative tablets/data records
2. named maiden / character-data messages
3. quest lore interfaces
4. mechanical/debug/menu-only records
