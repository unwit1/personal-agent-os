# Playbook — Skyrim Crash and Freeze Triage

Updated: 2026-09-24
Status: operational diagnostic playbook

Use this playbook when Skyrim crashes to desktop (CTD), freezes, hangs, infinite-loads, or exits during startup. The goal is to identify the failing layer with evidence before changing the load order.

## 1. Preserve evidence first

Before changing anything, capture:
- exact Skyrim executable/runtime version;
- SKSE version;
- mod manager/profile;
- current plugin load order and enabled mod/file priority;
- crash logger and version;
- crash log, SKSE log, relevant native-plugin logs;
- what the player was doing and whether the crash is reproducible;
- whether it occurs on new game and/or established save;
- last known working configuration;
- recent changed mods/files/settings.

Do not “clean,” reinstall, sort, or delete generated files before preserving this baseline.

## 2. Classify failure timing

### Before main menu
Prioritize:
- missing/incompatible SKSE DLL;
- wrong runtime build;
- Address Library mismatch;
- root DLL/preloader/proxy conflict;
- invalid master/plugin dependency;
- missing required files;
- renderer injector startup failure.

### Main menu / new game
Prioritize:
- DLL initialization/data-load hooks;
- UI/SWF/Menu initialization;
- startup quests/scripts;
- invalid plugins/forms;
- animation/behavior generated output;
- game-data/runtime framework compatibility.

### Loading one save
Prioritize:
- save-persisted Papyrus/native state;
- removed/changed forms;
- broken quest/alias/reference state;
- SKSE co-save serialization;
- missing plugins used by that save;
- location/reference state at saved position.

### Entering one cell/location
Prioritize:
- bad mesh/texture/NIF/collision;
- worldspace/reference/navmesh edits;
- NPC FaceGen/appearance asset;
- object/animation/physics asset;
- location-specific script/quest event;
- LOD/full-model transition.

### Performing one action
Prioritize the exact call path:
- equipping item → ARMO/ARMA/NIF/skeleton/physics/equip scripts;
- casting spell → SPEL/MGEF/projectile/effect script/native hook;
- opening menu → SWF/SkyUI/MCM/native UI hook;
- dialogue → INFO/voice asset/scene/fragment;
- combat → behavior graph/animation/perk/weapon/AI/native combat hook.

## 3. Crash logger selection

### Crash Logger SSE AE VR
Preferred first evidence source when compatible. It produces exception/register/call-stack/module/form/object data and can use PDB files for symbol resolution.

### Trainwreck
General-purpose crash logger designed for broad runtime compatibility. Useful as fallback/second evidence stream; it may provide less contextual introspection for some crashes.

### Tullius CTD Logger
Additional 2026 diagnostic tool capable of collecting CTD/freeze/infinite-load dumps and incident context. Use as supplementary evidence, especially hangs/ILS.

### Only one primary crash handler
Multiple exception/crash handlers can interfere with each other. Follow each logger's compatibility instructions and do not blindly enable all crash-dump handlers simultaneously.

## 4. Read the log correctly

### Exception code
Class of native failure, e.g. EXCEPTION_ACCESS_VIOLATION.

### Faulting instruction / RIP
The exact machine instruction executing at failure.

### Probable call stack
Execution chain near the exception. It is evidence of involvement, not a guilty-mod ranking.

### Registers
Inspect pointer-like values and decoded objects/forms where logger provides them.

### Modules
DLLs/EXE loaded into process. “Appears in module list” is not proof of crash causation.

### Object/form introspection
Crash Logger may decode TESForm/NiAVObject/editor/form names around register/stack data. Correlate those with the reproducible symptom.

### PDB symbol
Human-readable native function/type mapping. A matching plugin PDB can convert raw DLL offsets into useful symbols.

### Address offset
Module+offset is version-specific evidence. Search exact offset only when runtime and DLL build match.

## 5. Evidence-strength ladder

Strong evidence:
1. Same crash reproduced on demand.
2. Same faulting path/object/module across multiple logs.
3. Disabling/replacing one isolated component removes the crash and re-enabling restores it.
4. Symbolized function or invalid object directly matches the triggering action.
5. Upstream issue/source confirms same defect/version.

Moderate evidence:
- repeated same mesh/form/editor ID;
- one DLL repeatedly appears high in relevant call stack;
- failure starts exactly after a version/runtime update.

Weak evidence:
- mod name merely appears anywhere in log;
- “SkyrimSE.exe” is faulting module;
- Papyrus logged an error before CTD;
- automated analyzer labels one pattern without reproduction.

## 6. Layer-isolation tests

### Native DLL test
Disable only the suspected SKSE DLL (and dependent mods) in a duplicate profile. If startup/action becomes stable, inspect runtime/version/API compatibility before touching ESP order.

### Asset test
Hide/replace exact NIF/HKX/DDS/SWF path while preserving plugin records. If crash disappears, inspect the asset and file winner.

### Plugin-record test
Keep assets but replace/remove the specific record override/patch in a test profile. Validate with xEdit.

### Save-state test
Reproduce on:
- existing save;
- earlier save before symptom;
- new game.
Established-save-only failure strongly increases persistence/migration suspicion.

### Location test
Teleport/COC from a disposable test save to isolate cell/world/NPC loading.

### Animation test
Separate behavior-generator output from OAR replacements and skeleton/physics assets.

### Renderer test
Test without ENB/Community-Shaders optional features only after preserving configs; renderer-only change is meaningful evidence.

## 7. Binary search correctly

Disable half of a *dependency-safe candidate set*, not arbitrary half the entire mod list. Preserve required masters/frameworks. Repeat until the smallest causal set remains.

Bad binary search:
- disables masters but leaves dependents;
- changes plugin order, file order, and configs simultaneously;
- tests a save whose missing mods bake new damage between iterations.

Good binary search:
- duplicate disposable profile/save;
- one layer at a time;
- dependency closure respected;
- exact result recorded each iteration.

## 8. Hangs and infinite loading

Collect:
- thread dump/hang report if tool supports it;
- CPU usage pattern;
- disk activity;
- Papyrus stack/VM state;
- recent cell/quest transition;
- generated LOD/asset loading;
- native plugin logs.

A hang is not necessarily a CTD with “no crash log.” It may be deadlock, infinite loop, blocked I/O, pathological Papyrus/native work, or resource exhaustion.

## 9. Common anti-patterns

Do not:
- blame the first DLL named in a stack;
- sort with LOOT as a universal crash fix;
- clean every plugin;
- delete Papyrus instances wholesale;
- regenerate every tool output simultaneously;
- increase Papyrus budgets/memory settings without evidence;
- remove mods from the only copy of an important save;
- infer causation from one log.

## 10. Closure criteria

A diagnosis is “confirmed” when:
- failure is reproducible or strongly correlated;
- failing layer/component is isolated;
- proposed fix explains observed evidence;
- fix survives repeated test;
- no new structural errors appear;
- for save issues, both current and future state are checked.

Record the confirmed cause, runtime/tool versions, evidence, fix, and regression test in the knowledge base.

## Sources
- Crash Logger SSE AE VR: https://www.nexusmods.com/skyrimspecialedition/mods/59818
- CrashLoggerSSE source: https://github.com/alandtse/CrashLoggerSSE
- Trainwreck: https://www.nexusmods.com/skyrimspecialedition/mods/106440
- Tullius CTD Logger: https://www.nexusmods.com/skyrimspecialedition/mods/172272
- FallrimTools/ReSaver: https://github.com/mdfairch/FallrimTools
