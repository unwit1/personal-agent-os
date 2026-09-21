# GLENMORIL BOOK / MESG completeness inventory

Source: raw `Glenmoril.esm`.

## BOOK records

Total BOOK records: **264**
All 264 contain non-empty `DESC` text.

Raw BOOK text size:
**161,476 characters**

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
Imported exact source text:
- `007A46` — The Yelem School
- `007A47` — A City Sunken in the Desert
- `007A48` — The Three Owls
- `007A49` — Laza and the Owls
- `007A4C` — Rolly-Polly, Ja'bal the Cat
- `007A4D` — Ja'bal and the Chickens
- `007A4E` — Ja'bal and the Chicks
- `007A4F` — Ja'bal and the Eggs
- `27C7A3` — The Book of Atatami
- `5583A6` — Words of Jhunal
- `016223` — The Blue Star

### Original-book batch 02 — 9 records
Imported exact source text:
- `12D779` — Romion's Last Note
- `0D562D` — Book of Radiance, Vol. 1
- `0D562E` — Book of Radiance, Vol. 2
- `0D562F` — Book of Radiance, Vol. 3
- `0D5630` — Book of Radiance, Vol. 4
- `007A4B` — Laza
- `007A4A` — The People of Grasslands
- `016274` — To Slumber
- `11E049` — Black Book: The Gardener

**New exact BOOK texts imported in this audit: 20.**

Previously normalized families such as the Yelem Notes, Black Book: Debug, Threatening Letter from Ja'zel and Letter from Lalanoah remain separate existing source material and should not be double-counted merely because they also occur in the 264-record raw inventory.

## Reused official material

The `zzzRevBookESO*` family is retained in the raw inventory but should use provenance class **reused-official** unless a record comparison shows modified text.

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

It needs a dedicated provenance/function inventory before lore promotion.

## Next BOOK priorities

1. Professor Y / Secret Tale family — 13
2. remaining original/revision books and letters
3. mechanical spell/heart/ash descriptions
4. reused-official verification by text comparison rather than blind duplication

## Next MESG priorities

1. non-debug narrative tablets/data records
2. named maiden / character-data messages
3. quest lore interfaces
4. mechanical/debug/menu-only records
