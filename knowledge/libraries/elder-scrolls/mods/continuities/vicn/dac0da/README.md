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

- Structural inventory and all-quest catalog: complete first pass.
- Numbered main quest reconstruction: **MQ00 through MQ05 complete**.
- Major main-story dossiers/concepts: Rolls-On-Roads, Akashiya-Samon, Yngol, Ghost Choir 9, Prisoner/Many Paths, time breaches/mirror logic/zero-sum, Hist/Jill/Akulakhan Fifth-Era anomaly.
- Side quests processed:
  - **Drowned Nighthawk** (`zDcdSqYngol`)
  - **Abnur Tharn** (`zDcdSqAbnur`)
  - Abnur Tharn epilogue/will
  - Akashiya-Samon epilogue
- Cross-Vicn seed created for DAc0da, including the direct **Rolls-On-Roads ↔ Romion** bridge into GLENMORIL.
- Next high-priority side arc: **Echoes of Mnemolichite** (`zDcdSqWorm`), including Vanus Galerion, Yu'qbar, Mnemolichite, Sload/Necromancer activity, and Mannimarco.
- BOOK-wide provenance, remaining side quests, broad NPC identity resolution, scene-speaker resolution, locations, and full cross-Vicn reconciliation remain pending.

See `analysis/ingestion-checkpoint-01.md` before resuming.
