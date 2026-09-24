# Skyrim Modding Compatibility Pattern Corpus

Updated: 2026-09-24
Status: active troubleshooting/patch-design reference

This file captures recurring compatibility structures. Use the pattern to identify which data must be reconciled; do not treat it as a one-click patch recipe.

## NPC appearance + gameplay overhaul

Inputs:
- NPC replacer appearance;
- AI/combat/stat/perk/outfit overhaul;
- FaceGen assets;
- optional HPH/hair/headpart masters.

Preserve:
- gameplay fields from overhaul;
- coherent appearance fields from one chosen visual source;
- matching FaceGeom/FaceTint for final NPC_ appearance.

Common failure:
- dark face due record/asset mismatch.

Preferred tools:
- EasyNPC/manual xEdit/CK FaceGen depending workflow.

## City/interior architecture + lighting

Inputs:
- city/interior overhaul;
- Lux/ELFX/lighting mod;
- navmesh;
- Room Bounds/Portals;
- cell lighting/LGTM/IMGS;
- placed lights/FX.

Preserve:
- architecture placements;
- navmesh/door links;
- room/portal optimization matching new geometry;
- desired lighting template/cell fields;
- lighting mod's placed lights.

Common failure:
- invisible/popping rooms, blocked NPCs, dark/bright interiors.

## Landscape + grass + roads

Inputs:
- landscape-height/texture edits;
- road/bridge mod;
- grass mod;
- landscape-for-grass exclusion patch;
- terrain LOD.

Preserve:
- final LAND height/texture layers;
- navmesh where topology changed;
- no-grass landscape flags/textures;
- correct terrain LOD regeneration.

Common failure:
- grass through roads, seams, floating objects.

## Water + cell overhaul

Inputs:
- city/worldspace/cell edits;
- Water for ENB/RWT/etc.;
- SE flow data;
- WRLD distant-water values.

Preserve:
- unrelated CELL edits from architecture mod;
- water type/flow/height fields from intended water truth source;
- WRLD water/LOD data when overhaul needs it.

Common failure:
- cell-border seams.

## Leveled-list integration

Inputs:
- loot/encounter overhaul;
- item/creature mod additions;
- Delev/Relev or runtime distributor.

Options:
- Bashed Patch for compatible list semantics;
- manual/Synthesis merge;
- SPID/CID/CDF/SkyPatcher when runtime distribution better matches design.

Common failure:
- one overhaul silently erases another mod's list entries.

## Perk/magic-overhaul reconciliation

Inputs:
- perk overhaul;
- spell/magic overhaul;
- item enchantments;
- perk Entry Points;
- MagicEffect archetypes.

Preserve:
- deliberate perk tree/conditions;
- MGEF archetype/flags/cost;
- spell EffectItems;
- perk Entry Point modifiers.

Common failure:
- correct displayed spell but wrong magnitude/cost/duration.

## Skeleton + animation + physics stack

Layers:
1. skeleton winner;
2. behavior generator output;
3. BDI graph injection;
4. OAR selection;
5. AMR root motion;
6. Precision collision;
7. IED/SDS display nodes;
8. CBPC/FSMP physics.

Common failure:
- debugging the wrong layer because all are called "animation mods."

## Body + outfit + runtime morph

Inputs:
- CBBE/3BA/BHUNP/HIMBO family;
- BodySlide generated meshes/TRI;
- RaceMenu/SKEE;
- OBody/BodyGen/AutoBody/SynthEBD.

Preserve:
- topology compatibility;
- matching outfit sliders;
- morph ownership keys;
- correct skeleton.

Common failure:
- naked body correct, outfit wrong/clipping.

## UI injection stack

Layers:
- SkyUI/Scaleform base menu;
- I4 item metadata;
- COCKS crafting categories;
- Description Framework;
- QuickLoot/Favorites/Wheeler;
- native menu frameworks;
- PrismaUI HTML surfaces.

Common failure:
- data exists but one menu doesn't expose needed field or an old SWF lacks current injected metadata.

## Runtime patcher stack

Possible mutators:
- SPID;
- KID;
- BOS;
- FLM;
- SkyPatcher;
- CID/CDF;
- IPM;
- SRD;
- DSD;
- AnimObject Swapper;
- Music Type Distributor.

Rule:
xEdit only establishes static winner. Final runtime value requires config/log provenance from every framework capable of touching that field.

## Native DLL compatibility

Check:
- executable version;
- store (Steam/GOG/VR);
- SKSE/SKSEVR;
- Address Library;
- BEES/header compatibility;
- DLL build;
- CommonLib runtime family;
- dependency APIs;
- VC++ runtime;
- hook conflicts.

Common failure:
- "DLL loaded" interpreted as proof every hook/API initialized.

## Generated-output dependency graph

Typical order:
- finalize static load order;
- BodySlide;
- behavior generation;
- ParallaxGen;
- Synthesis/Bashed/static patches as required;
- TexGen/xLODGen;
- DynDOLOD;
- final manual patch if it must see generated plugins.

Actual order depends on which generator consumes which output.

Rule:
input change invalidates only downstream artifacts in dependency graph.

## Seasons + LOD

Inputs:
- Seasons of Skyrim swaps;
- seasonal textures/models;
- grass cache;
- TexGen/DynDOLOD seasonal variants.

Common failure:
- near objects winter, distant LOD summer.

## AI + navmesh + packages

Trace:
package eligibility -> package priority -> target resolution -> navmesh path -> collision -> process level.

Common failure:
- EvaluatePackage appears ineffective because actual issue is navmesh/collision.

## Quest + Story Manager

Trace:
event -> Story Manager conditions -> quest eligibility -> alias fill -> stage -> scene/dialogue -> script side effects.

Common failure:
- blaming quest script that never ran because alias fill failed.

## Dialogue + voice + localization

Trace:
INFO/topic -> conditions -> VoiceType -> filename/path -> FUZ/XWM/LIP -> BSA/loose resource -> localized strings.

Common failure:
- subtitle works but audio absent, or audio file exists under wrong plugin-name voice folder.

## Save migration

Compare:
- plugin defaults;
- ChangeForms;
- Papyrus instance variables/properties/state;
- StorageUtil/JContainers;
- external JSON/INI;
- SKSE co-save.

Common failure:
- mod update appears "ignored" because old value is baked/saved elsewhere.

## VR interaction

Layers:
- VRIK body/IK;
- HIGGS hands/object physics;
- PLANCK actor physical animation;
- VR input bindings;
- skeleton;
- SKSEVR/native APIs.

Common failure:
- applying flat-screen camera/activation assumptions to tracked hands/HMD.

## Rendering stack

Separate:
- NIF shader/material;
- texture maps;
- ParallaxGen;
- Community Shaders;
- ReShade;
- display/HDR/VRR;
- LOD/water special passes.

Common failure:
- trying to fix a material-data error with post-processing.

## Merge/form identity

Inputs:
- zMerge;
- MergeMapper;
- external configs using FormID~Plugin;
- EditorID lookups;
- plugin-tied config discovery/BSA/strings.

Rule:
"MergeMapper-supported" only solves form identity mapping. It does not make every plugin asset/config convention merge-safe.

## Evidence standard

For every compatibility decision record:
- source mods and exact versions;
- runtime;
- static record winner;
- asset winner;
- runtime mutators;
- save state;
- generated outputs;
- observed failure;
- discriminating test;
- validated resolution.

Promote a pattern-specific solution only when repeated evidence shows the same causal structure.
