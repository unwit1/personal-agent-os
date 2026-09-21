# BOOK manifest — GLENMORIL

**Source:** user-supplied `Glenmoril.esm`  
**SHA-256:** `5669018c81acf13147ff489f486963ecc3c57515a73ed9afd210c7ede85e1cc8`  
**BOOK records:** 264

## High-priority GLENMORIL-specific groups

- `zzzRevYelemNote*` — Yelem's Note corpus
- `zzzGHmq06Letter` — Letter from Lalanoah
- `zzzGHMq01Blackmail` — Threatening Letter from Ja'zel
- `zzzGHBookDebug` — Black Book: Debug; internal quest-order evidence
- `zzzLamBookGardener` — Black Book: The Gardener
- `zzzLamM04NoteHangedMan` — Ancient Note
- summon/spell/ash/heart BOOK records tied to named GLENMORIL entities

## Reused/reference texts observed

The plugin also includes titles known from broader Elder Scrolls material, including **The Glenmoril Wyrd**, **Aspects of Lord Hircine**, **Songs of the Return, Volume 5**, **To Dream Beyond Dreams**, **Varieties of Faith...**, and **The Ooze: A Fable**.

These records remain in the inventory but should resolve to/reference the appropriate official-source text node rather than creating a false Vicn-authorship claim.

## Next normalization

Generate one source record per GLENMORIL-specific BOOK with stable source-local IDs such as `Glenmoril.esm:<local-formid>`, retaining the raw load-order Form ID as observed metadata.
