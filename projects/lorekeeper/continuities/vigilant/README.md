# VIGILANT continuity

**Continuity ID:** `tes.mod.vigilant`  
**Source:** user-provided `Vigilant.esm`  
**Source SHA-256:** `7d3ca2d72297fbc5afda8f1b8bb217fa1fd6d9d7414360acdf1a922d848949ba`  
**Boundary:** mod continuity; do not treat VIGILANT additions as base Elder Scrolls canon unless separately supported by base-canon evidence.

Canonical library path: `knowledge/libraries/elder-scrolls/mods/continuities/vigilant/`.

## Initial extraction

The first structural pass parsed 120 quests, 1,012 dialogue topics, 1,225 INFO records with 1,698 response entries, 179 BOOK records, 1,233 NPC records, 49 factions, 13 worldspaces, 5,511 cells, and 78 scenes.

The raw local extraction also preserves decoded book text and machine-readable quest/dialogue/entity inventories. Repository normalization is proceeding from the highest narrative-value material first.

## First story layers identified

- numbered Vigilant/Altano chain (`zzzAoMMq00`–`zzzAoMMq10`)
- Blood Matron chain (`zzzBMMq01`–`03`)
- Bruiant Mansion / Child of Oblivion material (`zzzCO*`)
- Coldharbour main, memory, side-quest, boss, and historical/mythic material (`zzzCH*`)
- two Spinner's Needle routes whose quest objectives explicitly state they can skip to Act 4

## Next pass

Resolve INFO speakers and scene actors, then generate high-relevance character dossiers and a source-backed quest/narrative graph. Do not infer a speaker solely from line wording when conditions/aliases leave multiple candidates.
