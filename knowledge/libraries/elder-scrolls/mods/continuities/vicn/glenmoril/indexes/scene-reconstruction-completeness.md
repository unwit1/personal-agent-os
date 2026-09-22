# GLENMORIL scene reconstruction completeness

Source: `Glenmoril.esm`  
SHA-256: `5669018c81acf13147ff489f486963ecc3c57515a73ed9afd210c7ede85e1cc8`

## Status

**Complete for deterministic intra-scene choreography and phase chronology.**

- SCEN records reconstructed: **314 / 314**
- JSONL shards: **16**
- standard commit/shard cadence: **20 scenes**
- final shard: **14 scenes**
- parsed actions represented: **2211**
  - dialogue: **1578**
  - package: **461**
  - timer: **172**
- scenes with dialogue: **282**
- scenes with package actions: **139**
- scenes with timer actions: **131**
- zero-action scenes: **1**
- child INFO records linked through scene DIAL actions: **1324**
- response-text entries attached: **1324**

## What each scene record preserves

Each record keeps scene and owning-quest stable IDs, EditorIDs/names, registered and used quest aliases, ordered action indices, actor alias resolution, action flags, start/end phases, package references, timer duration, DIAL references, child INFO source IDs and response text, and a phase-by-phase active-action timeline.

## Chronology boundary

The reconstruction establishes **within-scene** ordering from SCEN phase/action structure. It deliberately does **not** impose a global story order among different SCEN records merely from ESM record order or EditorID names.

Cross-scene chronology remains a separate evidence pass using quest stages, Papyrus/script transitions, package targets, scene-start calls, conditions, and corroborating dialogue/text.

## Next frontier

1. Join QUST stages and stage fragments to scenes.
2. Decode package targets/locations/conditions for movement and interaction semantics.
3. Inspect Papyrus/script properties and scene-start/stop transitions.
4. Promote supported event chronology and relationships into lore pages only after those joins.
