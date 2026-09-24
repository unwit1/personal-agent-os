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


## 2026-09-24 deep-ingestion progress

The following frontier areas have now moved substantially beyond foundational coverage:

### Record-schema encyclopedia — PARTIALLY CLOSED
Added field-level schema maps for:
- actors/AI;
- quests/dialogue/scenes;
- worldspace/cell/landscape/navmesh/environment;
- items/magic/crafting/leveled data.

Remaining work is primarily exhaustive subrecord-by-subrecord extraction from current xEdit definitions and automated generation.

### CommonLib/SKSE API graph — PARTIALLY CLOSED
Added:
- subsystem/singleton map;
- actor processing tiers;
- plugin lifecycle/loading;
- inter-plugin API design;
- hooks/relocations/trampolines;
- serialization;
- event source/sink architecture.

Remaining work is symbol-level automated indexing with exact class/member/version provenance.

### Papyrus API encyclopedia — PARTIALLY CLOSED
Added:
- core host-type API map;
- event registration/messaging;
- language semantics/states/properties/fragments;
- performance/persistence;
- po3/PapyrusUtil/JContainers framework coverage.

Remaining work is machine-generated method-by-method signatures/caveats for every vanilla/SKSE/po3 framework script.

### INI/GMST catalog — PARTIALLY CLOSED
Added a core typed catalog plus environment/testing modules. Remaining work is exhaustive extraction with defaults/runtime ownership and reproducible benchmark evidence.

### Exact save-format model — SUBSTANTIALLY DEEPENED
Added dedicated ESS/ChangeForm/Papyrus/co-save internals and save-persistence modules. Remaining work is field-complete binary schema extraction and validated repair-case corpus.

### Behavior/Havok internals — SUBSTANTIALLY DEEPENED
Added Pandora behavior-graph authoring, BDI/OAR/AMR/Payload/SCAR/Precision and Havok collision/rigid-body authoring. Remaining work is graph-node/type-level schema automation.

### NIF/shader encyclopedia — SUBSTANTIALLY DEEPENED
Added block, geometry, shader, texture-slot, skinning and collision catalogs. Remaining work is exhaustive flag/block schema generation from NifTools/nifly.

### Rendering internals — SUBSTANTIALLY DEEPENED
Added Community Shaders deferred/G-buffer/pass architecture, ReShade/display/HDR and material/ParallaxGen layers. Remaining work is per-feature shader/resource graph and performance evidence.

### Creation Kit authoring handbook — BROADLY COVERED
Dedicated modules now cover worldbuilding/navmesh, portals/Room Bounds, weather/climate, crafting, quests/dialogue, Story Manager, encounters, Hearthfire, maps, races, furniture/traps and release packaging. Remaining work is tutorial-level step-by-step recipes and current CK/CKPE UI screenshots/behavior.

### VR — SUBSTANTIALLY DEEPENED
Added HIGGS/PLANCK/VRIK, VR Address Library, input/body/physics and cross-platform architecture. Remaining work is detailed VR UI/input bindings and per-framework compatibility matrices.

### Proton/Linux — FOUNDATION PRESENT
Architecture and MO2/Proton/DXVK path issues are covered. Remaining work is maintained current-version compatibility testing.

### Tool errors — FOUNDATION ADDED
A central tool error catalog now covers xEdit, LOOT, MO2, Vortex, CK, Papyrus Compiler, SKSE, Pandora, BodySlide, DynDOLOD/TexGen, xLODGen, ParallaxGen, Synthesis and CAO. Remaining work is exact message-by-message ingestion tied to versions.

### Compatibility patterns — FOUNDATION ADDED
A cross-mod pattern corpus now covers NPC appearance, cities/navmesh/lighting, landscape, water, leveled lists, magic/perks, animation stacks, runtime patchers, generated output, saves, VR and rendering.

### Tool/version provenance — FOUNDATION ADDED
A canonical version/provenance model now prevents old runtime/tool claims from being flattened into timeless advice.

## Highest-value remaining research

1. Generate record/subrecord schemas directly from current xEdit definitions.
2. Generate Papyrus method/event catalogs from source PSC/index data.
3. Generate CommonLib symbol graphs from headers/Doxygen.
4. Build a versioned exact-error corpus from real tool logs.
5. Build a validated crash-signature corpus from reproducible cases.
6. Maintain current tool/runtime/Creation update compatibility matrices.
7. Recover high-value historical technical knowledge with date/version tagging.
8. Build mod-specific profiles for important user projects and dependencies.
9. Add automated contradiction detection between old/new source snapshots.
10. Add CI jobs that rebuild indexes and flag stale source/version facts.


## 2026-09-24 Mod Factory automation progress

The repository has now moved beyond reference-only knowledge into an implementation system.

### Implemented architecture

Added:
- natural-language idea -> typed mod-project manifest -> build graph -> validation -> runtime test -> release pipeline;
- implementation-selection rules that prefer the least invasive correct layer;
- 24 reusable mod archetype playbooks;
- a question-preemption catalog so Agent OS resolves ordinary low-level architecture/tooling questions before asking the user;
- explicit human/CK/game boundaries for visual, navmesh, scene, animation-feel, physics and performance validation.

### Machine-readable contracts

Added schemas for:
- `skyrim-mod-project-v1`;
- `skyrim-tool-adapter-v1`;
- `skyrim-mod-build-report-v1`;
- `skyrim-analyzer-rule-v1`.

### Executable scaffolding

Added:
- project bootstrapper;
- project manifest validator;
- deterministic first-pass build planner;
- core tool-adapter registry;
- xEdit schema/master capture tooling;
- Papyrus/CommonLib/xEdit knowledge extractors.

### Validation and debugging

Added:
- gates G00-G23 covering project manifest, source lock, plugin schema, masters/FormIDs, ESL, conflict intent, framework configs, Papyrus, native plugins, assets, NIF/textures, animation/behavior, world/navmesh, quests, generated outputs, compatibility, crash/logs, performance, saves, packaging and reproducibility;
- differential schema strategy using xEdit + Mutagen + CK/runtime rather than trusting one parser;
- F01-F28 reusable test fixtures;
- evidence-first autonomous repair loop;
- machine-readable analyzer-rule model and initial rules for unresolved FormIDs, deleted navmesh, FaceGen mismatch, armor/partition mismatch, missing assets, stale generated output, runtime DLL mismatch, CTDA semantic loss and OAR overlap.

### Tool/framework automation

Current adapter/research coverage includes:
- xEdit/xDump;
- Mutagen/Synthesis;
- Spriggit;
- Creation Kit/CKPE;
- MO2;
- LOOT;
- Wrye Bash;
- SPID/KID/BOS/FLM/SkyPatcher;
- SKSE/CommonLib/Address Library;
- Papyrus compilers;
- OAR/Pandora and adjacent animation frameworks;
- PyNifly/NifSkope/BodySlide;
- DynDOLOD/TexGen/xLODGen;
- crash logging;
- FOMOD/package validation.

### Remaining implementation frontier

Highest-value next engineering work:

1. Implement the generic adapter runner that executes adapter-registry commands, captures stdout/stderr, hashes inputs/outputs and writes build-step records.
2. Add a typed runtime-patch intent intermediate representation and versioned renderers for SPID, KID, BOS, FLM, SkyPatcher and OAR.
3. Implement normalized semantic plugin export/diff so xEdit and Mutagen interpretations can be compared automatically.
4. Implement an xEdit Check-for-Errors automation wrapper and parser for the local Windows test runner.
5. Build the local/self-hosted Windows runtime harness that can launch dedicated MO2 fixtures, collect logs/crashes and run scripted smoke scenarios without redistributing proprietary game data.
6. Ingest and map validated Mutagen.Bethesda.Analyzers/Antigen Skyrim rules into the analyzer registry.
7. Implement crash-log parsing and signature clustering linked to exact build IDs.
8. Implement FaceGen/NPC appearance fingerprints and validators.
9. Implement PyNifly-backed NIF/TRI/partition/skeleton invariants and BodySlide output checks.
10. Implement FOMOD option-matrix simulation in addition to XML schema validation.
11. Implement dependency/license/redistribution auditing before project architecture is locked.
12. Add source/framework update watchers that create candidate compatibility changes and regression jobs rather than silently updating dependencies.
13. Build a bug-to-regression pipeline that can generate an analyzer rule/fixture candidate from a validated issue.
14. Generate per-mod CI templates from the project manifest.
15. Expand exact framework APIs/config grammars so semantic intent can be rendered without hand-written strings.

The long-term target is that a user can describe a mod idea and Agent OS can choose the architecture, generate the project, validate schemas independently, build assets/configs, launch a controlled test profile, interpret failures, repair deterministic defects and surface only genuinely creative or in-game decisions.
