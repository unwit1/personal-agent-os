# Skyrim Modding Terminology — Engine Fixes, Papyrus Extension Frameworks, and Runtime Infrastructure

Imported: 2026-09-24
Status: sourced encyclopedia pass 3

This module covers engine-level patch plugins and scripting/data frameworks that extend Skyrim below or beside ordinary ESP/ESL content.

## Engine patching concepts

### Engine fix
Native-code change correcting or mitigating behavior in Skyrim's executable/runtime rather than editing ordinary game records.

### Runtime patch
Memory/code/data modification applied after the executable starts.

### Binary patch
Modification to machine instructions or engine data layout.

### Hook-based fix
Engine fix implemented by intercepting a function/code path and adding replacement/corrective logic.

### Configuration-gated fix
Native patch enabled/disabled by INI/TOML/configuration setting.

### Preloader
Component loaded earlier than ordinary SKSE plugins to initialize hooks, allocators, or DLL-loading behavior before the standard plugin stage.

### Root DLL
DLL installed beside the game executable rather than under Data/SKSE/Plugins.

### SKSE DLL
Native plugin installed under Data/SKSE/Plugins and loaded through SKSE's plugin system.

### Runtime-specific DLL
Native binary built for only one or a subset of executable versions.

### Address Library dependency
Native plugin depends on runtime-specific relocation mappings supplied by Address Library.

### Patch overlap
Two native mods modify the same or closely related engine function/instruction and may be mutually exclusive or require coordination.

### Engine-fix conflict
Incompatibility at hook/patch level rather than plugin-record level.

### Double patch
Two components attempt to fix/replace the same code path. Correct behavior depends on explicit compatibility; stacking fixes is not automatically safer.

## SSE Engine Fixes

### SSE Engine Fixes
SKSE/native engine-fix suite by aers/Ryan/Nukem lineage addressing numerous Skyrim Special Edition engine bugs and limits.

### Part 1
Common installation terminology for the Data/SKSE-plugin portion of Engine Fixes.

### Part 2 / preloader
Common installation terminology for root-folder/preloader components required by some runtime/version configurations.

### EngineFixes.toml
Modern configuration file controlling Engine Fixes options.

### CleanSKSECosaves
Engine Fixes option historically used to remove orphaned SKSE co-saves lacking corresponding Skyrim saves.

### MaxStdio
Engine Fixes feature increasing the process file-handle/stdio limit to address classes of false save corruption/resource exhaustion issues.

### Memory manager patch
Engine Fixes functionality that changes memory allocation behavior; historical/current requirements vary by runtime/build.

### Form cache
Engine optimization/fix involving caching of form lookups. It can overlap with other engine-fix implementations and must not be blindly duplicated.

### Achievements with mods
Engine patch allowing achievements while modded.

### Chargen precache disable
Patch disabling character-generation precache behavior; overlaps conceptually with RaceMenu's historical Precache Killer.

### False save corruption
Community/Engine Fixes term for saves appearing unreadable/corrupt because the process exhausts file handles/resources rather than because the save bytes themselves are necessarily destroyed.

### Engine Fixes runtime matrix
Supported executable versions differ by Engine Fixes release. Treat the exact DLL build, runtime and Address Library version as one compatibility unit.

## Bug Fixes SSE / Scrambled Bugs class

### Bug Fixes SSE
SKSE plugin by meh321 containing engine-level bug fixes and requiring matching SKSE/Address Library support.

### Scrambled Bugs
Native bug-fix suite with individually configurable patches addressing gameplay/engine issues. It is separate from SSE Engine Fixes and compatibility must be evaluated patch by patch.

### Patch toggle
Config option enabling one fix within a larger bug-fix DLL.

### Patch provenance
For overlapping fix suites, record which component owns a correction rather than enabling every similarly named patch.

## powerofthree's Tweaks

### powerofthree's Tweaks
SKSE plugin containing bug fixes and gameplay/runtime tweaks across SE/AE/VR.

### po3 Tweaks configuration
INI/config-driven switches controlling individual fixes/features.

### Runtime utility DLL
Class of native plugin whose purpose is broad engine/framework functionality rather than one player-facing gameplay feature.

## Papyrus extender frameworks

### Papyrus Extender
Native SKSE plugin exposing additional game-engine functions/events/types to Papyrus beyond vanilla/SKSE base APIs.

### powerofthree's Papyrus Extender
Current widely used extension framework exposing hundreds of functions and dozens of events for Skyrim SE/AE/VR.

### Native Papyrus function
Function implemented in C++ and registered with the Papyrus VM.

### Custom Papyrus event
Native framework event delivered to registered scripts when an engine event/condition occurs.

### Registration
Script requests future custom-event delivery from an extension.

### Unregistration
Script removes event subscription to avoid unwanted callbacks/lifetime issues.

### Persistent event registration
Registration serialized or reconstructed across save/load depending on framework implementation.

### Function versioning
Extension functions/events can be added or behavior-adjusted across framework releases; mod requirements should specify minimum versions where needed.

### Papyrus API dependency
A script mod may compile because source stubs exist but fail at runtime if the native DLL providing those functions is absent.

### Script stub
PSC declaration exposing native functions/classes to the compiler. The stub alone does not implement native behavior.

## PapyrusUtil

### PapyrusUtil
SKSE framework adding utility functions, persistent data structures, JSON/file operations and other scripting capabilities beyond vanilla Papyrus.

### StorageUtil
PapyrusUtil system for storing values associated with forms/keys.

### JsonUtil
PapyrusUtil interface for reading/writing JSON-like data through Papyrus.

### Array utility
PapyrusUtil helpers extending practical collection manipulation beyond vanilla array limitations.

### External persistent data
Mod state written outside the ordinary plugin records and potentially outside vanilla Papyrus variables, depending on framework/API.

### Native data dependency
Save/mod behavior can depend on an SKSE DLL's serialized/external data even if the ESP and PEX files remain installed.

## JContainers

### JContainers
SKSE/Papyrus extension implementing richer serializable data structures and JSON/file access.

### JObject
JContainers generic object handle/base concept for managed container values.

### JMap
Associative key/value container.

### JArray
Dynamic array-like JContainers structure.

### JFormMap
Map keyed by forms.

### JDB
JContainers database/root-access concept for persistent structured data.

### JContainers garbage collector
Framework-managed lifecycle for its own container objects rather than vanilla Papyrus arrays.

### JSON serialization
Converting structured container data to/from JSON text/files.

## FISS / FISSES

### FISS
**Expansion:** FileAccess Interface for Skyrim Scripts.  
Papyrus-facing system for saving/loading configuration data from files, commonly used for MCM preset transfer.

### FISSES
Special Edition continuation/variant of FISS.

### FISSES NG
CommonLibSSE-NG based continuation/build supporting modern runtimes with the original scripts/ESP dependency model.

### MCM export/import
Common use of FISS-like frameworks to save a mod's menu configuration outside the active save and reload it elsewhere.

## Skyrim Platform

### Skyrim Platform
Runtime framework enabling Skyrim mod logic in JavaScript/TypeScript.

### TypeScript plugin
Skyrim Platform mod code authored in TS/JS and executed by the platform rather than compiled as Papyrus.

### Hot reload
Development feature that reloads script/plugin code during testing without a full game restart, within platform constraints.

### Skyrim Platform event
JS/TS event interface corresponding to update/game/input/other platform events.

### Papyrus bridge
Ability for Skyrim Platform code to call Papyrus/third-party SKSE-exposed functionality.

### npm dependency
JavaScript package dependency used by a Skyrim Platform plugin. This introduces a software-dependency layer distinct from ESP/ESL masters.

## Infrastructure troubleshooting rules

1. Record exact runtime, SKSE version, Address Library build, and every native DLL version before diagnosing an SKSE-load failure.
2. Root preloaders and Data/SKSE plugins are different installation layers.
3. A script compiler finding PSC stubs does not prove the native DLL that implements those functions is loaded.
4. Two mods with similarly named “fixes” may patch the same engine code. Verify overlap before enabling both.
5. A Papyrus API can persist state outside ordinary plugin records; uninstall/update analysis must include framework serialization/files.
6. If a DLL fails before DataLoaded, no ESP load-order patch can repair that binary incompatibility.
7. Separate engine-fix logs, SKSE logs, framework logs, Papyrus logs and native crash logs during diagnosis.
8. Treat mod-framework requirements as minimum-version/runtime contracts, not optional conveniences.
9. When a framework supports SE/AE/VR, that does not imply every dependent mod supports every runtime.
10. Do not delete co-saves/external JSON/framework data as a generic fix without backups and evidence.

## Sources

- SSE Engine Fixes: https://www.nexusmods.com/skyrimspecialedition/mods/17230
- SSE Engine Fixes source: https://github.com/aers/EngineFixesSkyrim64
- Bug Fixes SSE: https://www.nexusmods.com/skyrimspecialedition/mods/33261
- Scrambled Bugs: https://www.nexusmods.com/skyrimspecialedition/mods/43532
- powerofthree's Tweaks: https://github.com/powerof3/po3-Tweaks
- powerofthree's Papyrus Extender: https://github.com/powerof3/PapyrusExtenderSSE
- PapyrusUtil source: https://github.com/eeveelo/PapyrusUtil
- JContainers: https://github.com/ryobg/JContainers
- FISSES NG: https://github.com/epinter/fisses-ng
- Skyrim Platform docs: https://github.com/skyrim-multiplayer/skymp/blob/main/skyrim-platform/README.md

## Current-version notes

- On 2026-09-24, Nexus lists current SSE Engine Fixes 7.x files with runtime-specific support; the 1.7.99 beta changes preloader requirements compared with older supported runtimes.
- Bug Fixes SSE was updated in August 2026.
- powerofthree's Papyrus Extender upstream currently describes 374 functions, 37 events and 4 script objects. Treat counts as a dated snapshot, not a timeless API guarantee.
