# Skyrim Modding Knowledge — Crash-Log Evidence and Common Native Failure Patterns

Imported: 2026-09-24
Status: diagnostic encyclopedia pass 5

This module does not map offsets to “culprit mods.” It records what common crash-log evidence means and how strongly it supports a hypothesis.

## Exception classes

### EXCEPTION_ACCESS_VIOLATION
CPU attempted invalid read/write/execute memory access. Common immediate causes include null/dangling/bad pointers, out-of-bounds addresses, invalid vtables, corrupted objects, or incompatible binary layouts.

### Read access violation
Faulting instruction tried to read invalid/unmapped/protected address.

### Write access violation
Faulting instruction tried to write invalid/unmapped/protected address.

### Execute access violation
Instruction pointer/call target points to non-executable/invalid memory, often consistent with corrupted function pointer/vtable/stack.

### Stack overflow
Thread exhausted call stack, potentially from recursion or extreme call nesting.

### Illegal instruction
CPU executes invalid/unsupported opcode; can indicate corrupted control flow, bad binary/patching or incompatible instruction assumptions.

### Integer divide by zero
Native calculation attempts integer division by zero.

### Breakpoint exception
Intentional debug/assert trap or injected diagnostic breakpoint depending on code.

### C++ exception
Language/runtime exception may propagate to crash handler if uncaught.

## Pointer patterns

### Null dereference
Object pointer is zero/near-zero and code accesses a field offset.

### Near-null address
Address like small constant offset can imply null base + member offset.

### Invalid object
Pointer is nonzero but object memory/type/lifetime is invalid.

### Dangling pointer
Object was destroyed/freed but stale pointer remains.

### Use-after-free
Code accesses freed object memory; may reproduce nondeterministically.

### Vtable call crash
Indirect virtual-function call uses invalid object/vtable slot.

### Bad cast
Code treats one object type as incompatible type/layout.

### Out-of-bounds
Array/vector/index operation goes beyond valid storage.

## Stack interpretation

### Top frame
Current/faulting function context. Stronger evidence than a DLL merely appearing deeper in stack, but still not proof of root cause.

### Caller frame
Function that invoked the next frame.

### Engine frame
SkyrimSE.exe code; engine crash can still be triggered by bad mod data passed into it.

### Plugin frame
SKSE DLL code appears in execution path.

### Repeated plugin frame
Same native mod consistently appears close to fault across reproduced logs; raises suspicion substantially.

### Innocent intermediary
Library/function appears because it processes corrupted data produced elsewhere.

### PDB-symbolized frame
Function/source name resolved from matching debug symbols, improving interpretation.

### Unsymbolized offset
Module+offset only; requires exact module version/hash and reverse-engineering/map to interpret.

### SHA/module hash
Binary fingerprint that identifies exact DLL even when embedded version metadata is missing/incorrect.

## Skyrim object evidence

### TESForm pointer
Native form object identified in registers/stack.

### FormID in log
Resolved game form ID. Must map through the exact load order from that crash.

### EditorID in log
Human-readable form label if logger could introspect it.

### NiAVObject
Scene-graph object such as node/shape associated with rendered NIF.

### BSFadeNode / NiNode
Scene-node types frequently appearing in mesh/render/animation contexts.

### hkb / animation graph object
Havok behavior/animation object suggests animation graph context but not necessarily a broken animation file.

### Actor
Native actor object; correlate identity/equipment/location/animation state.

### TESObjectREFR
Placed/runtime reference object.

### Base object
Form underlying a reference.

## Failure-family hypotheses

### Mesh-load crash hypothesis
Evidence:
- same NIF/path/object/BSFadeNode/NiAVObject near fault;
- crash on loading/equipping/entering area;
- hiding exact mesh resolves crash.
Confirm by asset isolation and NifSkope/clean profile.

### Animation crash hypothesis
Evidence:
- behavior graph/hkb/animation frames;
- reproducible on animation event/action;
- generator/OAR/HKX/skeleton change correlates.
Separate behavior graph, replacement HKX and skeleton/physics.

### Physics crash hypothesis
Evidence:
- FSMP/Havok physics frames;
- specific physics-equipped asset reproduces;
- XML/schema/skeleton issue.
Do not blame FSMP just because its solver is handling malformed input.

### FaceGen crash hypothesis
Evidence:
- specific NPC/headpart/NiNode;
- crash on NPC load;
- appearance assets/dependencies inconsistent.
Test NPC record and head assets.

### UI crash hypothesis
Evidence:
- Scaleform/GFx/menu/plugin callback frames;
- exact menu opening reproduces;
- SWF/native MCM helper/UI plugin involved.

### Renderer crash hypothesis
Evidence:
- d3d11/dxgi/driver/CommunityShaders/ENB/upscaler context;
- rendering action/resolution/feature toggle controls reproduction.
GPU driver frames alone are weak evidence without isolation.

### Save-state crash hypothesis
Evidence:
- only one established save;
- reproducible immediately on loading same object/quest state;
- new game safe;
- serialized form/plugin missing or migration error logged.

### DLL incompatibility hypothesis
Evidence:
- startup plugin loader rejects version;
- crash at initialization after game update;
- plugin supports different runtime;
- missing relocation/Address Library mapping.

### Record-data crash hypothesis
Evidence:
- engine receives invalid/unresolved form/data;
- xEdit Check for Errors identifies same record;
- removing/fixing record resolves crash.

## Crash Logger capabilities

Current Crash Logger SSE AE VR supports SE/AE/VR, PDB parsing, Skyrim object introspection, optional minidumps and thread dumps. On 2026-09-24 Nexus lists version 1.25.0 and support for Skyrim AE 1.7.99.

### Thread dump
Snapshot of threads without necessarily crashing, useful for hangs/deadlocks.

### Minidump
Binary crash snapshot inspectable with WinDbg/Visual Studio.

### Reverse-engineered Skyrim PDB
Symbol file mapping Skyrim executable addresses to reconstructed symbols for a matching runtime.

## Trainwreck role

Trainwreck 1.4.0 is a broad-version crash logger. It provides useful exception/module/hash evidence, but when deeper object/PDB introspection is needed, Crash Logger can be a stronger first source on supported environments.

## Automated analyzer caution

Crash-log analyzers can recognize known textual patterns but cannot reliably infer root cause from all logs. Treat analyzer output as hypotheses to verify through reproduction and isolation.

## Diagnostic rules

1. Never produce a “culprit ranking” solely from names appearing in a call stack.
2. Exact DLL/runtime/hash matters when mapping offsets.
3. Reproduction plus controlled disable/re-enable is stronger than pattern matching.
4. Match FormIDs against the crash-time load order, not the current changed profile.
5. Distinguish immediate fault (where crash happened) from initiating defect (why object/data became invalid).
6. Multiple crash logs from the same trigger are more informative than many unrelated random logs.
7. Preserve logs before modifying profile.
8. Use PDB/minidump when debugging a native plugin you control.
9. An engine/driver frame is not automatically a Bethesda/NVIDIA/AMD bug.
10. Persist confirmed signatures only with versions and reproduction conditions.

## Sources

- Crash Logger SSE AE VR: https://www.nexusmods.com/skyrimspecialedition/mods/59818
- CrashLoggerSSE source: https://github.com/alandtse/CrashLoggerSSE
- Trainwreck: https://www.nexusmods.com/skyrimspecialedition/mods/106440
- CommonLibSSE-NG: https://github.com/alandtse/CommonLibSSE-NG
