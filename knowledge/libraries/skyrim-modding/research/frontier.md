# Skyrim Modding Research Frontier

Updated: 2026-09-24
Status: active research backlog

## Why this file exists

Skyrim modding knowledge cannot be permanently “exhausted.” The game is reverse engineered continuously, native runtimes and Creation Kit builds change, tools release new versions, new frameworks appear, and millions of individual mods create local compatibility facts.

The repository therefore defines **broad foundational coverage** separately from **open research frontiers**. Agent OS should keep ingesting evidence when a project/question touches an uncovered or version-sensitive area.

## Current broad coverage

The library now has dedicated material for:

- plugin/xEdit binary and conflict semantics;
- FormIDs, ESM/ESL behavior, ONAM, localization and archives;
- Creation Kit record types and worldbuilding;
- Papyrus language, APIs/events, performance and persistence;
- quests, aliases, dialogue, scenes and Story Manager;
- actors, combat, perks, magic, crafting and leveled systems;
- SKSE, Address Library, CommonLibSSE-NG and native plugin development;
- native crash diagnostics and save diagnostics;
- runtime distributors/patchers including SPID, KID, BOS, FLM and SkyPatcher;
- animation/behavior frameworks including OAR, BDI, Payload Interpreter, AMR, Precision and Pandora/Nemesis/FNIS lineage;
- meshes/NIFs, textures, BodySlide, RaceMenu/BodyMorph/BodyGen and FaceGen;
- HDT-SMP/FSMP physics;
- UI, SkyUI, MCM and Scaleform;
- audio/voice/localization;
- rendering, ENB concepts and Community Shaders;
- LOD, grass, seasons, occlusion and large references;
- MO2, Vortex, Wabbajack and generated-output workflows;
- Mutagen, Synthesis, Wrye Bash, Mator Smash and xEdit scripting;
- LE↔SE asset conversion/porting;
- runtime/config/INI/console/testing environments;
- Skyrim VR and Linux/Proton/Steam Deck considerations.

## Highest-value open frontiers

### 1. Exhaustive record-schema encyclopedia
Ingest every Skyrim record signature and important subrecord/field from current xEdit definitions, including field semantics, conflict behavior and safe patch strategy. This should be generated from xEdit schemas where licensing permits rather than manually transcribed.

### 2. CommonLib/SKSE API graph
Index major RE classes, event sources, singleton systems, SKSE interfaces, relocation patterns and cross-runtime availability from current CommonLibSSE-NG source. Store symbol-level references, not copied source bodies.

### 3. Papyrus API encyclopedia
The current event/type catalog is broad but not method-by-method exhaustive. Add every vanilla/SKSE/po3 function with signature, host type, latent/global/native status, caveats and version provenance.

### 4. INI/GMST catalog
Build a typed catalog of meaningful Skyrim.ini/SkyrimPrefs/Game Setting values with default, subsystem, runtime scope, known risks and provenance. Explicitly reject superstition/performance-tweak folklore without reproducible evidence.

### 5. Exact save-format model
Deepen ESS, ChangeForms, Papyrus structures and SKSE co-save data from FallrimTools/SKSE source. Keep destructive repair procedures gated behind backups and identified corruption.

### 6. Behavior/Havok internals
Map behavior graph nodes, variables, animation event routing, project structures and modern Pandora patch semantics beyond end-user terminology.

### 7. NIF schema and shader-material encyclopedia
Index significant Skyrim NIF block types, shader flags, texture slots, collision blocks and skin/partition rules from NifTools/nifly/source evidence.

### 8. Rendering engine internals
Expand Community Shaders and reverse-engineered renderer pipeline knowledge with source-level feature interactions, buffer formats, shader stages and compatibility constraints.

### 9. Creation Kit complete authoring handbook
Systematically ingest current CK/CKPE workflows for every major editor surface: actors, dialogue, scenes, packages, quests, landscape, navmesh, worldspaces, audio, magic, perks, crafting, regions, weather, imagespaces and optimization.

### 10. VR-specific engine differences
Current VR coverage is architectural. Add VR-specific input/UI/camera/player-body, interaction frameworks, physics differences and native RE layout/function coverage as validated sources are found.

### 11. Proton/Linux compatibility matrix
Maintain dated compatibility evidence for Proton versions, MO2 installers, SKSE/native plugins, ENB/Community Shaders, DynDOLOD/BodySlide/Pandora tooling and filesystem setups.

### 12. Historical knowledge recovery
Search archived Bethesda forums, AFKTrack, Nexus comments/docs, GitHub issues and high-quality old technical posts for discoveries lost from modern documentation. Promote only corroborated findings.

### 13. Tool error encyclopedia
Index exact warnings/errors and validated responses from xEdit, DynDOLOD/TexGen, LOOT, MO2, Vortex, Pandora, BodySlide, CK, Papyrus compiler, SKSE/CommonLib, CAO and patchers.

### 14. Crash signature corpus
Store anonymized/reproducible crash signatures tied to validated causes, fixes, runtime versions and regression tests. Avoid “module name = culprit” heuristics.

### 15. Compatibility-pattern corpus
Extract recurring design patterns:
- NPC appearance patch;
- city/navmesh patch;
- landscape/LOD patch;
- leveled-list integration;
- distribution-framework conversion;
- perk/magic overhaul reconciliation;
- skeleton/animation/physics stack;
- UI framework integration;
- weather/lighting/rendering stack;
- runtime DLL compatibility.

### 16. Mod-specific knowledge
For important mods in the user's projects, maintain versioned profiles covering records, scripts, assets, dependencies, frameworks, configuration, conflicts, patches, source links and validated observations.

### 17. Tool/version history
Keep current and historical behavior separate so an old forum answer does not silently override modern tool behavior.

### 18. Creation/official-update change tracking
Track Bethesda runtime, Creation Kit and official Creation/ResourcePack changes that alter engine behavior, record schemas, native addresses or tooling.

## Evidence promotion policy

Evidence progresses:
1. Lead / community claim
2. Corroborated observation
3. Reproducible test or upstream/source evidence
4. Validated knowledge
5. Version-scoped canonical rule

Contradictions should remain visible until resolved. Newer evidence does not automatically invalidate older evidence if it applies to a different runtime/tool version.

## Exhaustiveness definition

For this project, “exhausted” should mean:
- all major domains have at least foundational coverage;
- authoritative/current source families have been registered;
- remaining gaps are explicitly indexed;
- newly encountered terms can be classified into an existing domain;
- questions can trigger just-in-time deeper ingestion from the relevant source;
- no claim is made that the evolving Skyrim modding ecosystem is permanently complete.

That threshold has now been reached for the broad foundation. Further ingestion should become **targeted and evidence-driven**, while periodic crawls can continue to expand source-specific detail.
