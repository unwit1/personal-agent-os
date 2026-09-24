# Skyrim Modding Diagnostic Router

Updated: 2026-09-24
Status: active troubleshooting index

This is the retrieval front door for Agent OS. Start with the symptom, identify all plausible layers, then consult the linked terminology/authoring/playbook modules. Do not jump directly from symptom to culprit.

## Startup / before-main-menu crash

Retrieve:
- `terminology/skse-commonlib-native-crash.md`
- `terminology/runtime-platform-config-files.md`
- `terminology/engine-fixes-runtime-frameworks.md`
- `terminology/plugin-format-localization-archives.md`
- `troubleshooting/crash-diagnostics-playbook.md`

Check exact runtime, SKSE, Address Library, native DLL builds, preloaders/root files, missing masters, archive/resource integrity, redistributables, injectors and environment paths.

## Crash while loading an established save

Also retrieve:
- `terminology/worldspace-navmesh-saves-persistence.md`
- `terminology/papyrus-persistence-advanced.md`
- `terminology/papyrus-performance-native-serialization.md`

Compare new-game behavior. Inspect missing plugins, ChangeForms, Papyrus instances/stacks, SKSE co-save serialization and migration.

## Crash in one cell/location

Retrieve:
- worldspace/navmesh modules;
- crash-log patterns;
- NPC appearance/FaceGen;
- NIF/texture/physics;
- LOD/large-reference modules.

Look for a consistently named form, mesh, NPC, node, reference, navmesh or cell-load script.

## Dark face / wrong NPC appearance

Retrieve:
- `terminology/npc-appearance-facegen-racemenu.md`
- `terminology/racemenu-facegen-bodymorph-physics.md`
- `terminology/records-patching-load-order.md`
- archive/asset modules.

Compare winning NPC_ record with FaceGeom, FaceTint, HeadParts, high-poly-head dependencies, RaceMenu overlays/morphs and asset winner.

## Armor/body clipping or wrong body

Retrieve:
- animation/assets/BodySlide;
- RaceMenu/BodyMorph;
- NIF/texture optimization;
- physics.

Check ARMO/ARMA slots, mesh partitions, skeleton, weights, BodySlide output winner, TRI/BodyMorph topology and physics config.

## Animation not playing / wrong animation

Separate:
1. behavior generation: Pandora/Nemesis/FNIS;
2. behavior variable/event injection: BDI;
3. runtime replacement: OAR/DAR;
4. annotation payload: Payload Interpreter;
5. root motion: AMR;
6. combat collision: Precision;
7. raw HKX/asset overwrite.

Retrieve `terminology/modern-runtime-frameworks.md` plus animation/asset modules.

## NPC won't move / path correctly

Retrieve:
- Creation Kit worldbuilding/navmesh;
- worldspace/navmesh persistence;
- Papyrus/AI packages;
- Story Manager/quests if behavior is quest-driven.

Distinguish package eligibility, combat state, navmesh connectivity, door links, collision/navcut, linked refs and save-persisted actor state.

## Quest/dialogue/radiant content not working

Retrieve:
- Papyrus/quests/dialogue/AI;
- Story Manager/quests/dialogue/scenes;
- Story Manager locations/events;
- audio/localization if lines exist but are silent/missing.

Trace event -> node conditions -> quest start -> alias fill -> stage -> scene/topic INFO -> conditions -> voice assets.

## Missing text / $LOOKUP_FAILED / untranslated UI

Retrieve:
- plugin format/localization/archives;
- audio/localization archives;
- UI/SkyUI/MCM.

Check Localized flag, STRINGS/DLSTRINGS/ILSTRINGS filenames/language, string IDs, translation assets and interface translation files.

## Missing voice / silent dialogue

Retrieve:
- audio/localization archives;
- data frameworks/audio;
- quest/dialogue modules.

Check INFO, VoiceType, plugin-name voice path, FUZ/XWM/LIP naming and BSA/loose asset visibility.

## Mesh is invisible / purple / malformed

Retrieve:
- textures/NIF optimization;
- animation/assets/BodySlide/UI;
- plugin archive/loading;
- asset conversion/porting.

Purple generally points toward missing texture/material resources; invisible/malformed geometry may involve mesh format, shader flags, partitions, skinning, nodes, alpha or wrong asset path.

## Physics hair/cloth broken

Retrieve:
- physics HDT-SMP collision;
- RaceMenu/FaceGen/physics;
- NIF/skeleton modules.

Check FSMP version, skeleton nodes, XML path/schema, mesh nodes, bone weights, collision groups and FaceGen node pruning.

## Distant object/tree/grass/terrain wrong

Retrieve:
- LOD/grass/seasons/occlusion;
- LOD/grass/occlusion/world rendering;
- worldspace persistence;
- rendering/shaders.

Identify exact layer: terrain LOD, object LOD, tree LOD, grass LOD, dynamic Near/FarGrid, large reference, full model or occlusion.

## Low FPS / stutter

Retrieve:
- performance engine limits;
- rendering/shaders;
- physics;
- Papyrus performance;
- LOD modules.

Measure frame time and determine CPU, GPU, VRAM, I/O, physics, draw-call, shader-compilation or VM pressure before changing settings.

## Runtime-distribution rule not working

Retrieve:
- runtime-distribution-frameworks;
- skypatcher-runtime-record-patching;
- modern-runtime-frameworks.

Identify framework, exact version/config grammar, input form identity, filters, config processing order and framework log.

## xEdit conflict / patch decision

Retrieve:
- records-patching-load-order;
- xedit-plugin-format-advanced;
- patching-tool-lineage;
- automated-patchers-mutagen-synthesis.

Determine intent per field. Load order is sufficient only when one whole override should win; otherwise forward/combine or use a domain-appropriate runtime/generated patch.

## Mod works loose but not packed

Retrieve:
- plugin-format-localization-archives;
- audio-localization-archives;
- packaging/release workflow.

Validate BSA target format, name/load association, internal Data-relative paths, archive size/settings and loose-vs-archive precedence.

## LE mod port fails in SE/AE

Retrieve:
- asset-conversion-porting;
- textures/NIF optimization;
- plugin-format;
- runtime/native modules.

Inventory plugin, NIF, HKX, DDS, scripts, archives and native DLLs separately. Form-version conversion alone is never proof of a complete port.

## MCM blank / settings do not persist

Retrieve:
- UI/SkyUI/MCM;
- Papyrus persistence;
- data frameworks/Engine Fixes.

Separate menu registration/UI assets from save-side Papyrus state, MCM Helper settings, external JSON/INI and framework dependency versions.

## Generated patch/output stale

Retrieve:
- automated patchers/Mutagen/Synthesis;
- mod manager/Wabbajack pipelines;
- patching-tool lineage;
- LOD/animation/BodySlide modules as applicable.

Trace which input changed and rerun only downstream outputs in the regeneration dependency graph.

## Evidence policy

For every diagnosis:
1. identify symptom and reproduction;
2. classify layers;
3. collect exact versions/state;
4. retrieve relevant knowledge modules;
5. distinguish direct evidence from hypothesis;
6. choose the least destructive discriminating test;
7. record the result;
8. promote only validated findings to canonical knowledge.
