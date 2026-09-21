# VIGILANT continuity

**Continuity ID:** `tes.mod.vigilant`  
**Primary source:** user-provided `Vigilant.esm`  
**SHA-256:** `7d3ca2d72297fbc5afda8f1b8bb217fa1fd6d9d7414360acdf1a922d848949ba`  
**Plugin author:** `Vicn`  
**Header version:** `182`  
**Masters:** `Skyrim.esm`, `Update.esm`

VIGILANT is stored as an explicit mod-continuity overlay. Its additions may reference official Elder Scrolls lore, but they must not silently overwrite base canon.

## First-pass ingestion complete

- 120 QUST records parsed and structurally inventoried.
- 1012 DIAL topics and 1225 INFO records parsed, preserving 1698 response entries in the local raw extraction.
- 179 BOOK records parsed with decoded DESC text.
- 1233 NPC records inventoried.
- Faction, cell, worldspace, and named-item records inventoried.
- `analysis/story-skeleton.md` records only first-pass structure directly supported by the ESM.

## Next pass

Resolve dialogue speakers/aliases and SCEN ordering first, then build high-relevance character pages and a quest/narrative graph. Coldharbour memories and historical figures should remain source-scoped until their VIGILANT testimony is compared against base-canon evidence.

## Supplementary source layer

Lorekeeper may ingest translator/contributor background commentary when it materially resolves source gaps, but it remains provenance-separated from direct plugin evidence.

Current supplementary source:
- `sources/supplementary/a123999-vigilant-backgrounds.md`

Rules:
- direct ESM dialogue/structure remains primary implementation evidence;
- supplementary commentary may resolve intended identity or background;
- conflicts are retained rather than overwritten;
- commentary-derived claims must remain labeled as such.
