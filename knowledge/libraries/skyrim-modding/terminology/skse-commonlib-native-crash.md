# Skyrim Modding Terminology — SKSE, CommonLibSSE-NG, Native Plugins, and Crash Diagnostics

Imported: 2026-09-24
Status: sourced deep-ingestion pass 2

This reference covers the native-code layer used by modern Skyrim SE/AE/VR mods.

## Runtime and binary terminology

### Runtime
The specific Skyrim executable build running on the user's machine. Native-plugin compatibility depends on the actual runtime/build, not merely the marketing label “SE” or “AE.”

### SE
In modern modding shorthand, often refers to the 1.5.x Skyrim Special Edition runtime family, especially 1.5.97. The term is overloaded and should not be used as a substitute for an exact executable version when debugging DLL compatibility.

### AE
In modern modding shorthand, commonly refers to Skyrim's 1.6+ runtime family. Anniversary Edition content ownership and runtime version are related historically but not identical technical concepts.

### VR
Skyrim VR runtime family. VR differs enough in executable layout and engine structures that native plugins require explicit support.

### GOG runtime
Skyrim Special Edition/Anniversary runtime distributed through GOG. Native compatibility must be checked explicitly because executable/runtime details can differ from Steam builds.

### ABI
**Expansion:** Application Binary Interface.  
The low-level conventions governing class layout, calling conventions, registers, vtables, symbol interaction, and binary compatibility. ABI differences are why code that compiles for one runtime can crash on another.

### Offset
A numeric displacement from a module/function/object base address. Native plugins often use offsets when locating fields, instructions, or functions.

### Address
A concrete memory location in the running process.

### RVA
**Expansion:** Relative Virtual Address.  
Address represented relative to the executable/module base, making it more portable than a process-specific absolute address.

### Pattern scan
Locating machine code/data by searching for a byte signature rather than relying only on one hard-coded address.

### Hook
A code modification that intercepts or redirects execution so a plugin can run custom logic before, after, or instead of original engine behavior.

### Detour
A hook implemented by redirecting execution from an original function/instruction sequence to replacement/custom code.

### Trampoline
Executable memory/code used to bridge from a patched call/jump site to plugin logic and/or back to original code. SKSE/CommonLib expose trampoline support for safer hook construction.

### Call hook
A patch that changes a call instruction so it invokes custom code.

### Vtable
Table of virtual-function pointers used by C++ polymorphic objects. Incorrect vtable layout/slot assumptions can cause runtime-specific crashes.

### RTTI
**Expansion:** Run-Time Type Information.  
Native metadata used to identify class/type relationships. Reverse-engineered Skyrim libraries expose RTTI information for engine classes.

### Struct layout
The exact size and field offsets of a C++ engine structure. Layout can differ across runtime families.

### Reverse engineering
Deriving engine types, functions, layouts, and behavior from executable code/data, runtime observation, and tooling rather than from Bethesda source code.

## SKSE

### SKSE
**Expansion:** Skyrim Script Extender.  
Runtime extension and native-plugin infrastructure used by many advanced Skyrim mods.

### SKSE64
Name commonly used for the 64-bit Skyrim SE/AE SKSE branch/runtime.

### SKSE plugin
A native DLL loaded through SKSE. It can register native Papyrus functions, listen for SKSE lifecycle messages, hook engine code, serialize custom state, or expose APIs to other plugins.

### SKSE plugin directory
Typically `Data/SKSE/Plugins/`, where native SKSE DLLs and many associated INI/log/data files are installed.

### SKSE plugin load
The lifecycle point at which SKSE loads a native plugin and supplies interfaces to the game/plugin environment.

### SKSE messaging interface
Inter-plugin/lifecycle messaging API. Plugins can listen for SKSE lifecycle messages and messages from other loaded plugins.

### PostLoad
SKSE lifecycle message sent after plugins have been loaded.

### PostPostLoad
A later lifecycle message commonly used when a plugin needs other SKSE plugins to already exist before requesting APIs or establishing cross-plugin communication.

### DataLoaded
Lifecycle stage used by many modern CommonLib plugins when game data is loaded and forms can be safely accessed for many tasks.

### SKSE serialization interface
API used by native plugins to persist custom plugin state into save games and reconstruct it on load.

### SKSE task interface
API for queuing work through game/SKSE-supported task mechanisms instead of performing inappropriate work on arbitrary threads.

### SKSE trampoline interface
Infrastructure for allocating/using trampoline memory for native patches and hooks.

### SKSE Papyrus interface
API allowing native plugins to register new functions/classes callable from Papyrus.

### Plugin API
A deliberately exposed C/C++ interface that one SKSE plugin provides so another plugin can communicate with it.

## Address Library and relocation

### Address Library for SKSE Plugins
A versioned address database created by meh321 that maps stable IDs to runtime-specific executable offsets/addresses so native plugins do not need one hard-coded address set per executable version.

### Address Library ID
Stable identifier representing an engine address/function/data target across supported runtime mappings.

### Version database
The runtime-specific Address Library database containing ID-to-offset mappings.

### Relocation
Resolving a stable identifier or runtime-specific location into the actual in-process address used by the current executable.

### REL namespace
CommonLibSSE-NG namespace containing relocation/address/version support.

### REL::ID
CommonLib-style representation of an Address Library identifier.

### REL::Relocation
CommonLib abstraction wrapping a resolved function/data address so native code can invoke/access engine functionality through runtime-aware relocation.

### Relocation ID
A mapping construct pairing the appropriate IDs for different runtime families.

### Raw offset
Hard-coded memory offset used directly rather than through a versioned mapping. Raw offsets are fragile across executable updates unless the corresponding code layout is verified identical.

### Missing relocation mapping
Address Library/relocation failure where a required ID has no valid mapping for the current runtime. This is a hard compatibility problem, not something to guess around.

## CommonLibSSE-NG

### CommonLibSSE
C++ reverse-engineering/helper library exposing Skyrim engine classes and SKSE integration to native-plugin developers.

### CommonLibSSE-NG
Multi-runtime CommonLib fork/family designed to support SE, AE, and VR from one codebase and, when configured appropriately, one DLL.

### RE namespace
CommonLib namespace containing reverse-engineered Skyrim engine classes/types such as forms, actors, UI, Havok, and many other systems.

### SKSE namespace
CommonLib namespace wrapping SKSE plugin interfaces, plugin lifecycle helpers, serialization, messaging, trampolines, and related facilities.

### REL namespace
CommonLib namespace for runtime/version/address relocation.

### REX namespace
Cross-platform/runtime support namespace present in current CommonLibSSE-NG development.

### Multi-runtime plugin
Native DLL compiled to support more than one Skyrim runtime family, using runtime-aware abstractions where ABI/layout differences exist.

### Runtime feature detection
Code that checks whether a particular runtime-specific feature/layout/function is available before using it.

### Runtime data accessor
CommonLib pattern that hides differing field/layout offsets behind an accessor instead of direct member access.

### Static relocation
A relocation object with lifetime sufficient for repeated calls. CommonLib guidance warns against repeatedly constructing certain relocation singletons where static lifetime is required.

### CommonLib reverse-engineered class
C++ representation of a Skyrim engine class derived from binary analysis. Names/types are technical models of the executable, not Bethesda's published SDK.

## Native plugin debugging

### PDB
**Expansion:** Program Database.  
Debug-symbol file generated by Visual Studio/toolchains. A matching PDB can allow crash loggers/debuggers to resolve native addresses into function/symbol names for a plugin.

### Symbol
Human-readable function/global/type identifier associated with compiled code when debugging information is available.

### Stack trace
Ordered native call stack captured around a fault. It provides execution context but does not automatically identify the true root cause.

### Call stack
Sequence of active native function calls. In crash logs, entries near the top are often relevant but can represent victims/callers rather than the originating bug.

### Register
CPU state value such as RAX, RCX, RDX, RSP, RIP, etc. Crash logs may capture registers to help inspect invalid pointers and faulting instructions.

### RIP
x86-64 instruction pointer register. The reported faulting RIP identifies the instruction being executed when the exception occurred.

### Access violation
Windows/native exception caused by invalid memory read/write/execute access.

### EXCEPTION_ACCESS_VIOLATION
Common crash exception when code dereferences an invalid pointer or accesses protected/unmapped memory.

### Null pointer
Pointer with no valid target. Dereferencing a null pointer can produce an access violation.

### Dangling pointer
Pointer that once referenced valid memory but outlived/followed destruction of its target.

### Use-after-free
Bug where code accesses an object after the object's memory/lifetime has ended.

### Invalid vtable
Corrupt/wrong virtual-function table pointer or runtime-mismatched layout causing calls through invalid slots.

### Module
Loaded executable or DLL represented in process memory. Crash logs often identify the module containing the faulting instruction.

### Native crash log
Crash report produced by a native crash logger/handler with exception details, registers, stack, modules, and potentially object/form context.

### CrashLoggerSSE
SKSE/SKSEVR crash-logging plugin that produces native crash logs and can use symbol information to improve diagnostics.

### Papyrus log vs native crash log
Papyrus logs describe the script/save VM. Native crash logs describe process-level exceptions. Neither should be used as a substitute for the other.

### Suspect module
A DLL/EXE appearing in a crash stack or fault location. Presence indicates involvement, not automatically blame.

### Faulting instruction
Machine instruction at the exception address. Understanding its operands can reveal whether the immediate failure was an invalid object pointer, bad index, bad function pointer, etc.

### Reproducible crash
Crash that can be triggered through a repeatable sequence. Reproducibility dramatically improves root-cause confidence compared with interpreting one isolated crash log.

## Native-plugin compatibility rules encoded for Agent OS

1. Always collect the exact Skyrim executable runtime when diagnosing DLL compatibility.
2. Distinguish “game version,” “SKSE version,” Address Library data, and the plugin's supported runtimes.
3. Treat SE/AE labels as shorthand only; use exact runtime numbers for technical compatibility.
4. Never assume an Address Library ID, struct offset, hook site, or vtable slot is identical across SE/AE/VR without verification.
5. A native crash stack shows execution context, not automatic culpability. Correlate faulting instruction, registers, involved objects, module versions, and reproduction.
6. A PDB/symbolized stack improves readability but does not eliminate the need for reasoning about object lifetime and ABI.
7. Papyrus errors and native crashes are separate evidence streams.
8. A missing relocation mapping is a compatibility blocker; do not invent offsets.
9. Runtime updates can break native plugins even if their ESP/ESL data is unchanged.
10. Prefer CommonLib/runtime abstractions over raw hard-coded offsets when equivalent supported mechanisms exist.

## Sources

- Official SKSE: https://skse.silverlock.org/
- Original SKSE64 Plugin API header: https://github.com/ianpatt/skse64/blob/master/skse64/PluginAPI.h
- CommonLibSSE-NG current fork README: https://github.com/alandtse/CommonLibSSE-NG/blob/ng/README.md
- CommonLibSSE-NG architecture/contributor guidance: https://github.com/alandtse/CommonLibSSE-NG/blob/ng/CLAUDE.md
- CommonLibSSE-NG SKSE API implementation: https://github.com/CharmedBaryon/CommonLibSSE-NG/blob/main/src/SKSE/API.cpp
- Address Library for SKSE Plugins: https://www.nexusmods.com/skyrimspecialedition/mods/32444
- Address Library description mirror: https://mod.pub/skyrim-se/212-address-library-for-skse-plugins
- VR Address Library: https://github.com/alandtse/skyrim_vr_address_library
- CrashLoggerSSE: https://github.com/alandtse/CrashLoggerSSE

## Current-version note

CommonLibSSE-NG is actively changing. The repository observed on 2026-09-24 contains releases/changes from September 2026, so specific build-system, license, runtime-support, and implementation details must be re-checked when used for future implementation work.
