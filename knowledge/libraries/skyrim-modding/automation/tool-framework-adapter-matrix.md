# Skyrim Mod Factory — Tool and Framework Adapter Matrix

Snapshot: 2026-09-24
Status: active capability registry

This matrix answers: **what should Agent OS use, what can it automate, and what must it verify?**

## Core authoring and data tools

| Tool/framework | Best use | Automation surface | Mandatory checks | Human/supervised boundary |
|---|---|---|---|---|
| xEdit / SSEEdit / xDump | authoritative plugin inspection, conflict analysis, cleaning, schema/export | command-line tool modes, xDump definition export, scripts | unresolved FormIDs, masters, flags, record schema, ESL range, cleaning warnings | interpret intentional conflict semantics |
| Mutagen | deterministic programmatic plugin read/write | .NET API | schema/type safety, masters, FormKeys, output reload | game semantics not encoded by type system |
| Synthesis | load-order-derived code patchers | patcher pipeline/CLI/GUI ecosystem | patcher version, settings, source load order, output validation | choose patch intent when multiple mods disagree |
| Creation Kit | editor-owned quests/scenes/dialogue/world/navmesh/FaceGen workflows | partially scriptable/launchable, mostly editor-centric | xEdit post-validation, generated assets, warnings | navmesh, scene, spatial and visual authoring |
| CK Platform Extended | CK stability/fixes/reverse-engineered improvements | CK launch/build integration | exact CK/CKPE compatibility | editor behavior still needs CK testing |
| Wrye Bash | Bashed Patch and tag-driven merging | batchable tool workflow | tags, generated patch contents, current load order | verify merge semantics for unusual mods |
| LOOT/libloot | ordering metadata, warnings, dirty metadata | library/metadata syntax/CLI ecosystem | cycles, requirements, exact CRC metadata | LOOT order does not prove compatibility |
| MO2 | isolated profiles, VFS, executable launching | command-line instance/profile/run support | profile identity, overwrite outputs, VFS winner | gameplay remains external |
| Wabbajack | reproduce full modlist environment | automated modlist installation/build ecosystem | source availability, hashes, licensing | authoring individual mod logic |

## Runtime patch/distribution frameworks

| Framework | Use when | Auto-generation opportunity | Main validation |
|---|---|---|---|
| SPID | distribute supported spells/perks/items/outfits/factions/keywords to actors | generate DISTR configs from semantic filters | parse config, resolve forms, detect overlapping rules, verify recipients |
| KID | add/remove keywords on supported items | generate keyword rules from type/value/name/form filters | form existence, duplicate/contradictory keyword rules |
| BOS | replace base objects at runtime | generate swap rules from FormKeys/filters | swapped types compatible, recursion/overlap, source form availability |
| FLM | mutate FormLists at runtime | generate list add/remove configs | list/form resolution, duplicate entries, ordering assumptions |
| SkyPatcher | runtime record/distribution patching for supported domains | generate configs from manifest transformations | grammar/version, target record types, patch ordering |
| OAR | conditional animation replacement | generate condition trees/submods/priorities | condition parse, priority conflicts, animation path, runtime match |
| MCM Helper | settings persistence/UI integration | generate settings schema/config scaffolding | defaults, save/global persistence, migration |

Rule: runtime patchers reduce static plugin conflicts but introduce **runtime provenance**. The build report must record every framework capable of changing final state.

## Native plugin stack

### SKSE
Runtime extender and plugin host.

Automate:
- runtime detection;
- version matrix;
- plugin metadata checks;
- dependency scanning.

### CommonLibSSE-NG
Preferred strongly typed reverse-engineered C++ layer for multi-runtime SKSE plugin work.

Automate:
- project generation;
- CMake presets;
- compile matrix;
- symbol/reference checks;
- unit tests;
- Address Library/runtime guard tests.

Important current concern:
CommonLibSSE-NG's current licensing should be checked at project creation because static-link licensing can constrain the downstream plugin license.

### Address Library / VR Address Library
Treat as runtime relocation data dependency, not a substitute for plugin runtime compatibility.

Validate:
- installed family;
- game runtime;
- relocation IDs used;
- plugin's supported runtime declarations.

### powerofthree's Papyrus Extender
Search this provider **before creating a new native DLL** when Papyrus needs operations/events not offered by vanilla/SKSE.

Current inspected upstream source snapshot contains 379 global function declarations, 37 event names and four extra Form-derived script object classes; the repository stores the exact source-derived catalog.

Automate:
- PSC provider ingestion;
- dependency declaration;
- compile-root generation;
- exact function/event lookup;
- base-form vs reference vs instance vs loaded-3D mutation classification;
- compile-provider/runtime-provider cross-check;
- native-binding smoke tests.

## Papyrus toolchain

### Pyro
Use as the repeatable project-level build orchestrator when a mod has multiple Papyrus sources, incremental rebuild needs, or packaged BSA/ZIP outputs.

Automate:
- incremental/parallel compile;
- pinned PapyrusCompiler path;
- build/output/package paths;
- archive/distribution production;
- input/output denominator checks.

Validate Pyro's output independently with the compiler/provider map, PEX inspection/decompilation, and archive extract/hash checks.

### Official PapyrusCompiler
Reference compiler for shipped language/runtime expectations.

### Caprica
Open-source compiler with Skyrim support and command-line options including imports, output, optimization, release mode, recursion and parallel compilation.

Best use:
- fast deterministic CI compilation;
- cross-check against official compiler for release-sensitive scripts.

### papyrus-utility
Promising CLI with compile/format/declaration/PEX inspection capabilities, but its own documentation states Skyrim support is not yet certified against a committed real source corpus.

Policy:
use experimentally until the project's compatibility evidence is strong enough for release gating.

### Champollion/decompilers
Useful for research/recovery/inspection. Never treat decompiled source as authoritative original source.

## Mesh / NIF / morph / animation assets

### NifSkope
Best visual/manual NIF inspector.

Automation:
limited direct batch authoring; use as reference and spot-checker.

### Nifly / PyNifly
High-value automation backend. Current PyNifly documentation exposes Python-accessible NIF manipulation and supports Skyrim NIF, TRI, skinning, partitions, shaders, collision, and HKX workflows.

Automate:
- inspect block tree;
- validate shader slots;
- detect missing bones/unweighted vertices;
- write transforms;
- batch path changes;
- generate/validate TRI;
- import/export controlled assets;
- test round trips.

### Blender
Use for real geometry/UV/weight/animation authoring. Prefer scripted Blender/PyNifly pipelines where deterministic.

### BodySlide / Outfit Studio
Use for outfit conversion, slider projects, weights, morph generation.

Automate:
- project discovery;
- batch build;
- output-path verification;
- mesh hash/change checks.

Supervise:
- clipping/weight quality.

### Cathedral Assets Optimizer
Use for asset conversion/optimization workflows when appropriate.

Policy:
always work on copies/staging outputs and verify before replacing source assets.

## Animation/behavior

### OAR
Choose for conditional replacement without graph authoring.

### Pandora Behaviour Engine+
Current upstream describes a modular behavior/character/skeleton patcher that parses patch changes, validates behavior nodes, and emits game-ready HKX.

Automate:
- patch-file generation;
- patch-order definition;
- generator launch;
- log parsing;
- output ownership check;
- graph validation.

### AMR / Precision / SCAR / MCO / Payload Interpreter
Treat as specialized capability providers. Adapter must declare:
- whether it adds runtime state, animation annotations, behavior dependencies, collision semantics, or event payloads;
- exact config/provider version;
- interaction with OAR/Pandora.

## Rendering / materials / LOD

### Community Shaders
Use as an optional rendering dependency only when feature genuinely requires its pipeline.

Validate:
- core/feature version;
- shader/material assumptions;
- ENB incompatibility state;
- special passes such as first-person/water/reflections.

### ParallaxGen
Use for generated parallax/material asset patching.

Validate source winner and generated NIF/material paths.

### xLODGen / TexGen / DynDOLOD
Generated-output pipeline for terrain/object/tree/grass/distant data.

Rule:
load-order or asset-winner changes invalidate downstream generated output.

Automate:
- launch;
- capture logs;
- fail on configured warning/error classes;
- hash inputs/outputs;
- preserve settings preset.

## Crash and runtime diagnostics

### Crash Logger SSE/VR
Preferred structured crash evidence source where supported.

Automate:
- collect newest crash;
- parse probable object/form/plugin;
- symbolicate where possible;
- link to build version;
- compare regression signatures.

### Papyrus logs
Use only for Papyrus diagnosis; do not treat proximity in log as proof of crash cause.

### framework-specific logs
SPID/KID/BOS/OAR/Pandora/DynDOLOD/etc. should have dedicated parsers rather than one generic regex.

## Installer and packaging

### FOMOD schema ecosystem
Use XML schema + validator for deterministic installer checks.

Automate:
- validate `ModuleConfig.xml`;
- verify every source/destination file;
- verify condition flags/plugin checks;
- simulate common option combinations;
- ensure no option produces missing required dependency.

### archive packaging
Build from a clean staging directory, never directly from development Data.

Check:
- allowed extensions;
- no logs/PDB/source secrets unless intentional;
- correct Data-relative paths;
- duplicate files;
- case conflicts;
- dependency README;
- version metadata.

## Adapter contract

Every adapter must expose:
- adapter id/version;
- executable/library path;
- supported targets;
- invocation;
- inputs;
- outputs;
- exit-code semantics;
- log locations;
- warning/error parser;
- deterministic/non-deterministic classification;
- timeout/stall detection;
- safe retries;
- auto-fixable errors;
- destructive actions;
- version/source provenance.

## Source references

- xEdit docs/source: https://tes5edit.github.io/docs/ and https://github.com/TES5Edit/TES5Edit
- Synthesis: https://github.com/Mutagen-Modding/Synthesis
- CKPE: https://github.com/Perchik71/Creation-Kit-Platform-Extended
- LOOT: https://loot.github.io/docs/
- MO2: https://github.com/ModOrganizer2/modorganizer
- CommonLibSSE-NG: https://github.com/alandtse/CommonLibSSE-NG
- Papyrus Extender: https://github.com/powerof3/PapyrusExtenderSSE
- SPID: https://github.com/powerof3/Spell-Perk-Item-Distributor
- KID: https://github.com/powerof3/Keyword-Item-Distributor
- BOS: https://github.com/powerof3/BaseObjectSwapper
- OAR: https://github.com/ersh1/OpenAnimationReplacer
- Pandora: https://github.com/Monitor221hz/Pandora-Behaviour-Engine-Plus
- PyNifly: https://github.com/BadDogSkyrim/PyNifly
- NifSkope: https://github.com/niftools/nifskope
- Crash Logger: https://github.com/alandtse/CrashLoggerSSE
- Caprica: https://github.com/Orvid/Caprica
- FOMOD docs/validator ecosystem: https://github.com/dh-nunes/fomod-docs

## Experimental isolated runtime automation

### skytest

Third-party Linux/gamescope test harness currently capable of:
- vanilla+one-mod isolated profiles;
- a vanilla A/B control;
- detached visible/headless game sessions;
- replayable step scripts;
- screenshot capture;
- libei input injection;
- structured SkytestProbe state/trace data;
- state gates and save isolation.

Policy:
- **experimental until Agent OS validates it locally**;
- must pass G27 validator/self-tests;
- every assertion is session/freshness scoped;
- do not trust synthetic held-input testing for mechanics whose correctness depends on real hardware held-state behavior;
- initial profile-management mutation requires explicit setup approval.
