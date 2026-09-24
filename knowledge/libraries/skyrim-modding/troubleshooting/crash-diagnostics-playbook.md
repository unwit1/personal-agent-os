# Skyrim Crash Diagnostics Playbook

Imported: 2026-09-24
Status: sourced troubleshooting knowledge

This playbook is intended for Agent OS troubleshooting. It separates evidence collection, native crash interpretation, reproduction, and escalation. It must not treat a module name in a stack as proof of blame.

## 1. Classify the failure first

### CTD
Process terminates unexpectedly.

### Startup CTD
Crash before main menu. Prioritize runtime mismatch, root-level loaders, native DLLs, Address Library, missing redistributables, broken assets loaded at startup, or environment/injector issues.

### Load-save CTD
Crash while loading an existing save. Compare new-game behavior and inspect save-persisted state, missing plugins, serialized native state, ChangeForms, Papyrus, and assets referenced by that save.

### New-game CTD
Crash when starting a fresh game. More likely to be current installation/runtime/data than old save state.

### Cell/location CTD
Reproducible crash near a specific place. Prioritize world records, references, meshes/textures, navmesh, NPC/FaceGen, scripts triggered by cell load, physics, LOD/full-model transitions.

### Action CTD
Reproducible on equip, cast, open menu, attack, transform, dialogue, etc. Focus on the data/runtime path specific to that action.

### Random CTD
Not yet demonstrated reproducible. Treat candidate causes as low confidence until a trigger/pattern is found.

### Freeze / hang
Process remains alive but stops progressing. A crash logger may not capture this as an exception; use thread dumps/hang diagnostics when available.

### Infinite loading screen / ILS
Loading never finishes. Can arise from deadlocks, resource/state issues, scripts, save problems, filesystem/tooling, or heavy work rather than a single crash exception.

## 2. Collect environment identity

Always record:

- Skyrim executable version/runtime;
- Steam/GOG/VR and relevant distribution;
- SKSE version;
- Address Library version/database;
- crash logger name/version;
- mod manager and deployment model;
- full plugin load order;
- enabled SKSE DLLs and versions;
- ENB/Community Shaders/Reshade/overlays/injectors;
- Windows version and Documents redirection/OneDrive status when relevant;
- GPU/driver for graphics crashes;
- whether issue occurs on new game and existing save;
- exact reproduction steps.

## 3. Preferred crash evidence

### Crash Logger SSE AE VR
Modern PDB-aware native crash logger. Current Nexus version observed during ingestion was 1.25.0, updated 2026-08-23, with support for Skyrim AE 1.7.99 and PDB/object introspection.

### Trainwreck
General-purpose crash logger designed to survive runtime updates. Useful for broad compatibility and quick capture, but logs may contain less game-object introspection than Crash Logger SSE AE VR.

### Minidump
Binary process dump for advanced debugging in WinDbg/Visual Studio. More powerful than a text log but requires symbols/debugging skill.

### Thread dump
Snapshot of active threads useful for hangs/deadlocks.

### PDB
Matching program database allows addresses in a native DLL to resolve to symbols/source locations.

### Module hash
Content hash can identify a DLL even when its embedded version metadata is bad/missing.

## 4. Read a native crash log in layers

### Exception code
Identify access violation, stack overflow, illegal instruction, breakpoint, etc.

### Faulting address / RIP
Instruction pointer where failure occurred.

### Faulting module
DLL/EXE containing the faulting instruction. High-value evidence, not automatic culpability.

### Registers
Inspect pointer-like register values around the fault.

### Probable call stack
Look at call chain and repeated object/module patterns.

### Object introspection
Crash Logger can print TESForm/NiAVObject and other known game-object details. Use FormID, EditorID, model path, actor name, node name as concrete search keys.

### Loaded modules
Check native plugin versions and duplicate/obsolete DLLs.

### Plugins list
Correlate forms/plugins seen in crash context with installed load order.

### Stack repetition
Recursive/repeating frames can suggest recursion/stack overflow, but optimized/unreliable unwind data can mislead.

### Null function pointer
Crash Logger 1.23+ added caller-chain recovery for null function-pointer scenarios; distinguish "call through 0" from generic invalid data reads.

## 5. Common crash-pattern categories

### Native version mismatch
DLL built for another runtime/ABI, wrong relocation IDs, hardcoded offsets, struct layout changes.

### Invalid form/object pointer
Native plugin or engine code accesses destroyed, missing, or wrong-type game object.

### Asset crash
Malformed/incompatible NIF, texture, animation, behavior, sound, or shader resource.

### Skeleton/animation crash
Bad node assumptions, incompatible behavior output, malformed HKX, animation hook conflict.

### Physics crash
FSMP/HDT object lifecycle, skeleton/node/config mismatch, collision/constraint issue.

### UI crash
Scaleform/SWF/native menu interaction, incompatible UI frameworks, repeated hooks.

### Save-state crash
Serialized plugin/script data no longer matches current code/forms.

### Reference/world crash
Specific placed reference/base model/navmesh/large-reference/LOD issue.

### Resource exhaustion
Reference-handle limits, memory/VRAM, extreme generated LOD, runaway native allocations, huge save/state.

### Injector conflict
ENB, Community Shaders, Reshade, RTSS, overlays, capture/debug tools all hook rendering/input/process APIs and can conflict.

### Filesystem/environment crash
OneDrive/Documents redirect, permissions, antivirus, missing runtime DLLs, wrong root install, VFS injection.

## 6. Evidence strength rules

Strong:
- exact reproducible trigger;
- faulting instruction in a named native plugin with matching symbols/source;
- same crash signature after repeated reproductions;
- disabling one component eliminates crash while all else is controlled;
- a specific form/asset appears consistently and reproduces when isolated;
- upstream issue/source confirms same condition/version.

Medium:
- plugin/module repeatedly appears near top of stack;
- object/form path appears in several logs;
- crash began immediately after a specific update;
- new-game/existing-save differential.

Weak:
- DLL appears anywhere in module list;
- one forum user blamed the same mod;
- Papyrus log has errors near time of crash;
- LOOT warning exists;
- "last mod installed" correlation without controlled test.

## 7. Controlled isolation

1. Back up profile/save.
2. Reproduce on unchanged baseline.
3. Change one variable or one tightly related component group.
4. Reproduce again.
5. Preserve each crash log with configuration metadata.
6. Prefer binary search for large candidate sets.
7. Do not remove masters from an established save casually.
8. For native plugins, test exact runtime-compatible builds.
9. For location crashes, inspect assets/forms referenced in that cell.
10. For appearance/animation/physics crashes, include skeleton and generated outputs in the candidate set.

## 8. Crash logger coexistence

Only one exception-handler crash logger should generally own native crash capture at a time. Crash Logger SSE AE VR explicitly warns against multiple active crash loggers including NetScriptFramework crash dumps. Trainwreck/Crash Logger should therefore be configured deliberately rather than stacked blindly.

## 9. Hang/freeze diagnostics

Use tools capable of:
- thread dump;
- minidump/manual snapshot;
- Windows Wait Chain Traversal;
- black-box event history;
- native logging around loading stages.

Tullius CTD Logger (2026) is an example of a newer diagnostic tool that captures dumps for CTD/freeze/ILS and combines supporting incident data; treat it as complementary evidence rather than a replacement for controlled reproduction.

## 10. Agent OS output format

For every crash investigation, produce:

- **Observed failure**
- **Reproduction confidence**
- **Runtime environment**
- **Primary evidence**
- **Top hypotheses (unordered unless evidence supports priority)**
- **Evidence for/against each**
- **Safe next isolation step**
- **Do-not-do warnings**
- **Result after test**
- **Promoted finding only after validation**

Never claim "X caused the crash" solely because X appears in a crash stack.

## Sources

- Crash Logger SSE AE VR: https://www.nexusmods.com/skyrimspecialedition/mods/59818
- CrashLoggerSSE source: https://github.com/alandtse/CrashLoggerSSE
- Trainwreck: https://www.nexusmods.com/skyrimspecialedition/mods/106440
- Tullius CTD Logger: https://www.nexusmods.com/skyrimspecialedition/mods/172272
- FallrimTools/ReSaver: https://github.com/mdfairch/FallrimTools
- SSE Engine Fixes source: https://github.com/aers/EngineFixesSkyrim64

## Dated current notes

- Crash Logger SSE AE VR Nexus version observed 2026-09-24: 1.25.0, updated 2026-08-23.
- CrashLoggerSSE upstream release history in 2026 added improved null-function-pointer caller recovery, PDB-path reporting and stack-overflow handling.
- Trainwreck Nexus version observed: 1.4.0 (2024); its design goal is broad runtime compatibility.
