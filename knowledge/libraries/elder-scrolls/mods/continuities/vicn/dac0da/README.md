# DAc0da continuity

**Continuity ID:** `tes.mod.vicn.dac0da`  
**Parent continuity:** `tes.mod.vicn`  
**Primary source:** user-provided `DAc0da.esm`  
**Source SHA-256:** `455f07f3bba5de5b1b5a84c882be3309a66fd3d503866e05658b99896dfdb00e`  
**Source size:** 12,626,380 bytes  
**Plugin author:** Vicn  
**TES4 header version:** 1.70  
**Masters:** `Skyrim.esm`, `Update.esm`, `Dawnguard.esm`, `Dragonborn.esm`

DAc0da is stored under the shared **Vicn continuity** with **VIGILANT**, **GLENMORIL**, and **UNSLAAD**. Claims extracted here remain attributable to DAc0da unless independently supported elsewhere. Nothing in this layer silently overwrites official Elder Scrolls canon.

## Stable source references

DAc0da records in this source file use load-order byte `04` because the plugin has four masters. Repository provenance strips that load-order-dependent byte and cites the local record offset:

- raw FormID `0400AA0C` -> `DAc0da.esm:00AA0C`
- raw FormID `04004475` -> `DAc0da.esm:004475`

Editor IDs are retained alongside these references when present.

## Direct ESM inventory

The deterministic parser currently resolves **51,137 records**, including:

- 43 QUST records
- 737 DIAL topic records
- 1,027 INFO dialogue records
- 554 NPC_ records
- 90 BOOK records
- 66 MESG records
- 79 SCEN records
- 12,699 CELL records
- 5 WRLD records

The plugin stores English dialogue directly in INFO/NAM1 fields, so dialogue can be ingested without an external string table.

## Main narrative chain

1. `DAc0da.esm:00AA0C` — **The Call of Landfall** (`zDcdMq00`)
2. `DAc0da.esm:004475` — **The Sea of Causality** (`zDcdMq01`)
3. `DAc0da.esm:004931` — **Negative Legacy** (`zDcdMq02`)
4. `DAc0da.esm:004981` — **Patchwork** (`zDcdMq03`)
5. `DAc0da.esm:00B21B` — **Numidium Tertius** (`zDcdMq04`)
6. `DAc0da.esm:00CA1E` — **Censored Fate** (`zDcdMq05`)

## Current ingestion state

### First-pass ESM lore ingestion — COMPLETE

- Structural inventory and all-quest catalog.
- Numbered main quest MQ00–MQ05.
- Numidium interior / Ghost Choir / Mantella / Jill / Prisoner / Many-Paths material.
- **Drowned Nighthawk** / Yngol / Tsuunalinfaxtir.
- **The End of All Wishes** / Beynhaal / Atmoran sacrifice material.
- **Abnur Tharn** plus Abnur epilogue/will.
- Akashiya-Samon main appearances and ghost epilogue.
- **Echoes of Mnemolichite** and linked subquests:
  - Option: Dreugh
  - Group Battle: The Sload City
  - Group Battle: The Revenant
  - The Sea of Radiance
- Vanus Galerion, Yu'qbar, Republic of Hahd, Vigilant Athanasius, mnemolichite.
- Augur of the Obscure / Adjacent Places / Grabbers.
- **Cheese Party** and **Sload Radio**.
- Alternate ending analyses:
  - **Rella Mozzarella**
  - **Pan-Argonia**
- First BOOK inventory/provenance pass over all 90 BOOK records.
- **In Grabbers' Hands** name/nymic mechanics resolved structurally.
- **Epilogue Yngol** resolved as a branch-dependent physical aftermath state.
- **Golden Dragon Flight** and **Agent Event** support/state-machine records resolved.
- DAc0da's Yaghra **Agent** is materially linked to the Daggerfall Agent/Warp-in-the-West cluster through its dedicated Totem-letter loot.
- Six Daggerfall Totem letters verified as reused official game text.
- Major Nahd-fiction provenance resolved: Djaf as mojonation1487 community apocrypha; KINMUNE, Tsaesci Creation Myth, Dominion Prism, Eat the Dreamer, Lament for Pelinal, and Type of Zero as reused Michael Kirkbride material.
- All **79 SCEN records** indexed with owning quests and scene-speaker resolution.
- Scene-driven dossiers added for N'Danda, Hgelhelm the Outcast, Haalj Hgelhelmson, and Sindwen the Wintercaller.
- Full custom worldspace/location index added for **Sea of Causality**, **Dwemereth**, and **Mozarella Spacetime**, plus important named Numidium interiors.
- Character form-family index added for ordinary/boss/ghost/summon/memospore/alternate forms.
- Narrative artifact index expanded for Prisoner/nymic objects, abstract Totems, Yngol/Atmoran artifacts, Tsaesci weapons, Underking/Zurin gear, and related quest objects.

### Strong cross-Vicn links indexed

- **Rolls-On-Roads ↔ Romion** -> GLENMORIL.
- **Radiance / Letter to a Friend ↔ Altano** -> VIGILANT.
- **Adjacent Places / Grabbers ↔ Lyg** -> UNSLAAD.
- **Mnemo-Li / memory / many paths** -> GLENMORIL and UNSLAAD.
- Atmora/Saarthal/Night-of-Tears comparison targets across the Vicn corpus.

### Written-lore status

The 90 BOOK records currently classify as:

- 66 spell/summon/item books;
- 13 letters/notes;
- 11 Nahd-fiction / apocryphal texts.

High-value DAc0da letters and temporal tomes are indexed. Reused Daggerfall and developer/apocryphal texts are being provenance-separated rather than silently attributed to Vicn.

## Completion state

For source SHA-256 `455f07f3bba5de5b1b5a84c882be3309a66fd3d503866e05658b99896dfdb00e`:

> **DAc0da first-pass ESM lore ingestion is complete.**

Completed structural layers now also include:

- creature/encounter families;
- custom race/morphology index;
- faction-record classification;
- Generic Dialogue pass;
- Citizen Dialogue pass;
- named-NPC gap pass;
- deterministic INFO ownership audit with **0 orphan INFO records**;
- first comprehensive gap audit;
- first-pass completeness report.

See:

- `analysis/gap-audit-01.md`
- `analysis/completeness-report-01.md`
- `analysis/info-ownership-audit.md`

## Next phase

Do **not** restart broad DAc0da ingestion unless the source hash/version changes.

Continue with **second-pass cross-Vicn synthesis and topic promotion**:

1. reconcile direct/rare-vocabulary bridges against VIGILANT, GLENMORIL, and UNSLAAD;
2. preserve source-level provenance and distinguish genuine shared continuity from reused external texts;
3. promote high-confidence entities/relationships into reusable Lorekeeper topic/claim structures;
4. perform targeted deep dives only where a specific unresolved question remains.

Residual DAc0da-only gaps are now technical/refinement issues: readable Papyrus bodies for a few runtime mechanics, exhaustive navigation graphs, and optional low-prose item expansion. The long Ghost Choir 9 transcript's source provenance is resolved.
