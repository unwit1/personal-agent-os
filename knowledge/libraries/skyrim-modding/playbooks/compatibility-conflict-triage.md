# Playbook — Skyrim Compatibility and Conflict Triage

Updated: 2026-09-24
Status: operational diagnostic playbook

Use this when two or more mods appear incompatible, one feature disappears, assets look wrong, or “load order” is suspected.

## 1. Identify the conflict layer

Check independently:
- plugin-record overrides;
- loose/archive asset paths;
- Papyrus PEX/source expectations;
- SKSE DLL/runtime hooks;
- INI/JSON/config files;
- runtime distributors (SPID/KID/BOS/FLM/SkyPatcher);
- behavior generator output;
- OAR runtime animation priority;
- BodySlide/generated mesh output;
- FaceGen;
- navmesh/worldspace/LAND;
- save-persisted state;
- LOD/generated outputs.

More than one layer may conflict simultaneously.

## 2. Plugin-record workflow

1. Load relevant plugins plus dependencies in xEdit.
2. Locate affected record/form.
3. Read entire override chain left-to-right.
4. Identify which fields each mod intentionally changes.
5. Determine desired final semantic combination.
6. Create/select a patch only for fields requiring reconciliation.
7. Add required masters; do not create unrelated dependencies.
8. Check for errors/unresolved FormIDs.
9. Test in game.

“Load X after Y” is sufficient only when losing all of Y's competing changes is actually desired.

## 3. Asset conflict workflow

1. Determine exact runtime path.
2. Identify all providers.
3. Determine file winner in MO2/Vortex/effective Data.
4. Compare assets if necessary.
5. Decide which whole file should win or create an asset-level patch/merge.
6. Check archive vs loose precedence.
7. Re-test without changing plugin order unless records also conflict.

## 4. Script conflict workflow

If same PEX path is supplied by multiple mods:
- identify which mod/version owns the expected API;
- compare source/version when available;
- ensure plugin records were authored against compatible script version;
- do not merge compiled PEX files.

## 5. Native DLL conflict workflow

For DLLs:
- exact runtime compatibility;
- same-path winner;
- overlapping hooks/engine fixes;
- shared Address Library/SKSE dependencies;
- logs and upstream compatibility notes.
Plugin load order cannot choose between two same-path DLLs.

## 6. Runtime distributor workflow

### SPID
Use for supported NPC distribution.

### KID
Use for runtime keyword classification.

### BOS
Use for placed-reference/base-object swaps.

### FLM
Use for FormList mutation.

### SkyPatcher
Use for broader supported runtime record mutation.

For any runtime framework:
- validate exact syntax/version;
- inspect its log;
- identify multiple configs touching same target/property;
- preserve processing order;
- remember xEdit will not show the final runtime mutation.

## 7. Worldspace/navmesh conflicts

Inspect:
- placed REFRs;
- persistent refs;
- door links;
- enable parents;
- NAVM;
- NAVCUT;
- LAND;
- Location/LocRefTypes;
- encounter zones/markers;
- Room Bounds/portals where interior.
Worldspace compatibility cannot be reduced to copying the last CELL record.

## 8. NPC appearance conflicts

Desired final state needs:
- winning NPC_ gameplay fields;
- intended head parts/morph/tints/weight;
- matching FaceGeom;
- matching FaceTint.
If patch changes final appearance data, regenerate/provide matching FaceGen.

## 9. Generated output conflicts

Generated output should be a named, versioned mod layer. Regenerate when relevant inputs change:
- Synthesis patch;
- BodySlide output;
- Pandora/Nemesis;
- TexGen;
- DynDOLOD;
- xLODGen terrain;
- grass cache;
- occlusion;
- merged plugin.

Never assume “generated” means it automatically wins correct priority.

## 10. Conflict classification

### Intentional winner
One mod is intentionally meant to replace another's behavior.

### Mergeable
Both mods change independent fields that can coexist in one patch.

### Semantic incompatibility
Features fundamentally require contradictory behavior; user must choose or code a higher-level integration.

### Runtime-order conflict
Both configs/hooks operate on same data and ordering/lifecycle determines result.

### Asset-exclusive conflict
Only one whole binary asset can occupy the path; custom merge/edit may be required.

### Save-state conflict
Current files are compatible, but existing save contains state from an older/conflicting arrangement.

## 11. Patch-quality checks

A compatibility patch should:
- state which versions it targets;
- have only required masters;
- resolve intended fields, not blindly forward every winner;
- avoid accidental ITMs/wild edits;
- preserve FormIDs;
- include required assets/scripts;
- document runtime framework config dependencies;
- be tested new game and existing save where relevant.

## 12. Knowledge capture

When resolving a conflict, persist:
- involved mod versions;
- exact conflicting records/files/configs;
- intended semantics;
- chosen resolution;
- patch/config artifact;
- test procedure and outcome;
- whether resolution is version-sensitive;
- source/evidence.

This turns one troubleshooting session into reusable knowledge.

## Sources
- Tome of xEdit: https://tes5edit.github.io/docs/
- LOOT load-order documentation: https://loot.github.io/docs/help/introduction-to-load-orders/
- Mod Organizer 2/USVFS: https://github.com/ModOrganizer2/usvfs
- Vortex: https://github.com/Nexus-Mods/Vortex
- SPID/KID/BOS: https://github.com/powerof3
- FLM: https://github.com/MaskedRPGFan/FormList-Manipulator
- SkyPatcher: https://github.com/Zzyxz/SkyPatcher
