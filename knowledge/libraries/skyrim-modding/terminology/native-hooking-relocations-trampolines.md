# Skyrim Modding Terminology — Native Hooking, Relocations, Trampolines, and ABI Compatibility

Imported: 2026-09-24
Status: sourced deep-ingestion pass 25

## Native address problem

### Runtime address
Virtual memory address of game function/data in current Skyrim executable process.

### Address drift
Compiler/linker/game updates move functions/data, invalidating hard-coded addresses.

### RVA
Relative Virtual Address from module image base.

### Module base
Address where SkyrimSE.exe or DLL is loaded.

### ASLR
Address Space Layout Randomization changes module load bases between processes, so absolute addresses cannot be persisted.

### Signature scan
Pattern-search machine code bytes to locate function/data when symbol/address ID unavailable.

### Pattern
Byte sequence plus wildcards used for scanning.

### False-positive signature
Pattern matches wrong code location.

### Version-specific offset
Hard-coded offset valid only for one executable build.

## Address Library / relocations

### Address Library
Versioned database mapping stable community IDs to runtime-specific executable addresses.

### Address ID
Stable numeric identifier assigned to reverse-engineered function/data location.

### REL::Relocation
CommonLib abstraction resolving address ID/offset/variant into usable runtime pointer/address.

### RelocationID
Pair/set of IDs for runtime families supported by CommonLib.

### VariantID
CommonLibSSE-NG identity carrying SE/AE/VR-related address IDs/offsets.

### VariantOffset
Runtime-specific direct offset abstraction.

### REL::ID
Address-library ID wrapper.

### REL::Offset
Module-relative direct offset.

### REL::safe_write
CommonLib helper modifying executable memory after applying appropriate page protection.

### Relocation database mismatch
Installed Address Library lacks IDs for current executable or plugin compiled with wrong expectations.

### Hardcoded-address plugin
DLL uses direct offsets/signatures instead of relocation abstraction and is especially runtime-fragile.

## Hooks

### Hook
Redirect/intercept game execution to plugin code.

### Detour
Patch function entry/call site so custom function executes.

### Inline hook
Overwrite instructions at target site with jump/call.

### Call-site hook
Replace one CALL target while leaving target function itself intact.

### Branch hook
Replace control-flow branch with plugin code.

### VTable hook
Replace one virtual-function pointer in class vtable.

### IAT hook
Replace imported function pointer in module's import table.

### Event hook
Prefer engine/SKSE event sink instead of machine-code patch where available.

### Pre-hook
Plugin code runs before original logic.

### Post-hook
Original runs, plugin modifies/observes afterward.

### Around hook
Plugin controls whether/when original runs.

### Original function
Address/callable returned/stored by hook so custom code can forward.

### Chain hook
Multiple plugins hook same site and forward through each other.

### Hook conflict
Two plugins overwrite same site without preserving prior detour.

### Hook order
Whichever DLL patches later may see first plugin's modified bytes instead of vanilla bytes.

## Trampolines

### Trampoline
Executable memory block near hook site containing jump stubs and/or displaced instructions.

### SKSE::Trampoline
CommonLib/SKSE helper allocating executable memory and writing branch/call hooks.

### Branch island
Nearby executable stub allowing a short relative branch to reach a far 64-bit target.

### 5-byte branch
x64 near JMP/CALL using rel32 displacement.

### 6-byte branch
Indirect RIP-relative branch/call through pointer slot.

### write_branch
CommonLib trampoline helper replacing branch with target and returning prior/original destination as applicable.

### write_call
Helper replacing call instruction.

### Allocate trampoline
Plugin reserves sufficient executable memory before installing hooks.

### Trampoline exhausted
Plugin attempts more stubs than allocated capacity.

### Displaced instruction
Original bytes overwritten by hook and copied/executed in trampoline when necessary.

### Instruction boundary
Hook must overwrite complete machine instructions; splitting instruction corrupts execution.

## VTables and RTTI

### VTable
Array of virtual-function pointers for C++ polymorphic class.

### VFunc index
Position of one virtual function in vtable.

### VTable layout drift
Game update/compiler change adds/reorders methods or class layout, invalidating old index assumptions.

### RTTI
Run-Time Type Information structures used for dynamic class identification/casts.

### CommonLib RE class
Reverse-engineered C++ representation of game object.

### Layout assertion
Compile-time/static assert checking expected class size/member offsets.

### Offset
Byte position of field inside class.

### ABI
Binary contract of calling convention, class layout, vtables and data types.

## Calling conventions

### x64 calling convention
Windows x64 ABI passes initial args in registers and requires stack/shadow-space rules.

### This pointer
C++ instance pointer passed as first logical argument.

### Function prototype mismatch
Hook typedef signature differs from actual machine function, causing register/stack corruption.

### Return type mismatch
Wrong assumed return convention/value.

### Struct layout mismatch
Plugin reads wrong field offsets.

## Runtime families

### SE 1.5.97
Legacy commonly supported SSE executable.

### AE 1.6.x
Later executable generations with substantial address/layout changes.

### 1.7.x runtime
Current 2026 executable generation requiring newly mapped addresses/build support.

### GOG runtime
Distribution-specific executable with distinct version/address mapping.

### VR runtime
Separate executable/ABI with additional layout differences.

### NG plugin
CommonLibSSE-NG-based plugin potentially compiled for multiple runtime families.

### Runtime gating
Plugin explicitly detects supported executable and refuses to load on unknown versions.

### Version-independent claim
Means plugin uses relocations/compatible abstractions for declared family; not proof of future unknown-runtime support.

## Patching safety

### Expected bytes
Plugin validates original instruction bytes before overwriting.

### Byte mismatch
Target no longer matches expected build or another plugin already hooked it.

### Fail closed
Plugin logs/refuses feature rather than patching unknown bytes.

### NOP
No-operation instruction used to disable/replace code.

### Patch length
Number of bytes overwritten.

### Memory protection
Executable pages normally read/execute; patch helper temporarily enables writing.

### Instruction cache
CPU may require synchronization after code patch depending on API/helper implementation.

## Threading

### Main thread hook
Hook executes in game main thread; heavy work directly causes frame hitches.

### Render thread hook
Runs during graphics submission; blocking causes rendering stalls.

### Worker hook
Executes on background engine thread; calling game APIs may be unsafe.

### Reentrancy
Hook can indirectly trigger itself; guard if not designed for recursion.

### Lock
Synchronization protecting shared state.

### Deadlock
Hook takes locks in conflicting order with engine/other plugin.

## Reverse-engineering workflow

### Disassembler
IDA, Ghidra, Binary Ninja, x64dbg tools inspect machine code.

### PDB
Symbols map functions/types/source locations for plugin; Bethesda executable usually lacks public full symbols.

### Cross-reference / xref
Instruction/data location referencing function/string/global used to identify code.

### String reference
Human-readable engine string helps identify nearby function.

### Decompilation
Tool reconstructs C-like pseudocode from machine instructions.

### Function signature
Recognizable byte/control-flow pattern used for version mapping.

### Address mapping
Locate corresponding function across runtime versions.

## Diagnostic rules

1. A DLL loading does not prove every hook installed; inspect plugin log.
2. Address Library support and class-layout support are separate concerns.
3. Hook conflicts can exist with zero ESP/xEdit conflicts.
4. Validate expected bytes before patching when feasible.
5. Never call a function through guessed prototype/layout.
6. Runtime update can break vtable indexes/struct offsets even when one relocation still resolves.
7. Use events/APIs instead of hooks where they provide required capability.
8. Preserve exact DLL version, runtime, Address Library and PDB/symbol info for crash analysis.

## Sources

- CommonLibSSE-NG: https://github.com/alandtse/CommonLibSSE-NG
- CommonLibSSE-NG REL documentation: https://ng.commonlib.dev/classREL_1_1Relocation.html
- CommonLibSSE-NG Trampoline source/docs: https://ng.commonlib.dev/classSKSE_1_1Trampoline.html
- SKSE64 upstream: https://github.com/ianpatt/skse64
