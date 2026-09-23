# Wheels of Lull book provenance — pass 01

Continuity: `tes.mod.wheels-of-lull`  
Source ESP SHA-256: `230b102cd1ec13f2d104da8803d32c19227ef519eaca766a00b076c322aa78bb`  
Scope: provenance/origin classification for the 33 persisted BOOK records.

## Rules

- A text embedded in Wheels of Lull remains evidence that the text exists inside the mod continuity.
- Reuse of an official, developer, apocryphal, or community text does **not** promote that source class into another canon class.
- Exact source reuse is linked to a central source record when one already exists; the mod keeps only its local BOOK record plus the relationship.
- No-match results are not proof of original authorship. Unverified records remain continuity-local until a prior source is positively identified.
- Textual similarity is not enough for promotion: title/prose/source provenance must be checked.

## Verified external-source reuse

### `0537158E` — KINMUNE

- Editor ID: `_Lull_Book2`
- Wheels title: **KINMUNE**
- Classification: **verified developer/apocryphal text reuse**
- Central source already present:
  `knowledge/libraries/elder-scrolls/sources/apocryphal-library/books/040008F1-anon-anu-anui-el.txt`
- Central source index identity: `LB_Book_AP_KINMUNE` / `040008F1`
- Relationship: Wheels embeds a KINMUNE-version text; retrieval should route to the central work for source history and keep the Wheels BOOK as continuity-local placement/adoption evidence.
- Version note: KINMUNE exists in multiple published/unofficial revisions. Exact variant-diffing remains a separate follow-up; do not collapse variants until normalized-text comparison identifies the closest source edition.

### `0537158F` — Tatterdemalion

- Editor ID: `_Lull_Book3`
- Wheels title: **Tatterdemalion**
- Internal heading: **Tatterdemalion: The Lunar Province of Secunda**
- Classification: **verified developer/apocryphal text reuse**
- Prior source: Michael Kirkbride, *Tatterdemalion: The Lunar Province of Secunda*.
- Verification basis: exact title and opening prose match a pre-Wheels forum/developer-text publication; Bethesda's later MysticMadman profile also identifies *Tatterdemalion* as an out-of-game Kirkbride work that inspired the mod author.
- Central library state: no dedicated Tatterdemalion source record was located in the current central apocryphal index.
- Action: candidate for central source ingestion; the Wheels BOOK should later point to that stable central work/source ID rather than becoming the canonical copy.

### `05371590` — The Cacophany

- Editor ID: `_Lull_Book4`
- Wheels title: **The Cacophany**
- Internal heading: **The Xal-Gosleigh Letters: On the Cacophony**
- Classification: **verified excerpt/reuse of developer-apocryphal correspondence**
- Prior source: *The Xal-Gosleigh Letters*, the out-of-game Xal/Gosleigh correspondence associated with Michael Kirkbride and Ted Peterson.
- Verification basis: the Wheels prose beginning with the Cacophany's gold masks, armor-mounted instruments, flute helms, and rib-xylophone leader matches the **Day of the Power/Knowledge** Xal letter.
- Central library state: no dedicated Xal-Gosleigh source record was located in the current central apocryphal index.
- Action: candidate for central source ingestion with letter/section-level variant tracking; the Wheels BOOK should link to the central work while preserving its local excerpt boundaries.

## Remaining BOOK records

The other 30 BOOK records remain `pending_provenance_review` in this pass. They stay scoped to `tes.mod.wheels-of-lull` unless and until a prior source is positively identified.

This includes the continuity's letters, manuals, crafting lists, Archeron documents, Chronography volumes, Sybandis texts, Hammar-era treatises, forged orders, and other local documents. Absence of an obvious central match is **not** recorded as proof that the text was first authored for Wheels of Lull.

## Centralization candidates created by this pass

1. `apocryphal.work.tatterdemalion` — candidate stable work ID.
2. `apocryphal.work.xal-gosleigh-letters` — candidate stable work ID, preserving individual-letter structure.
3. KINMUNE requires no new work record if the existing `040008F1` source is retained as the central representative; it does require explicit edition/variant metadata before exact deduplication.

## Next provenance batch

1. Normalize markup away from all 33 Wheels BOOK texts while preserving the raw plugin source.
2. Compare normalized text hashes against central official/apocryphal repositories.
3. Search prior-source provenance for the remaining named treatises, especially *Harquebuses*, *How Two Moon*, *De Rerum Mutabilitatis*, *Chronography*, and the Sybandis texts.
4. Create stable central work/source links for verified matches.
5. Keep uncertain origins unresolved rather than guessing.
