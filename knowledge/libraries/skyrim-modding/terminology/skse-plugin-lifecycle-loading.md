# Skyrim Modding Terminology — SKSE Plugin Discovery, Lifecycle, Loading, and Initialization

Imported: 2026-09-24
Status: sourced deep-ingestion pass 26

## Discovery

### SKSE plugin
Native DLL loaded by SKSE from `Data/SKSE/Plugins` according to SKSE's plugin discovery rules.

### SKSEPlugin_Version
Exported metadata declaration used by modern plugins to tell SKSE name/version/runtime compatibility.

### SKSEPlugin_Query
Legacy/compatibility export allowing plugin to provide metadata and accept/refuse loading.

### SKSEPlugin_Load
Required load entry point invoked by SKSE for an accepted plugin.

### Plugin declaration
CommonLibSSE-NG structure/macros describing plugin name, author/version, address-library use and supported runtimes.

### add_commonlibsse_plugin
CommonLibSSE-NG CMake helper that can generate/inject required plugin declaration boilerplate.

### Query phase
SKSE checks plugin metadata/compatibility before ordinary initialization.

### Load phase
SKSE calls plugin's load function after validation.

### Refuse to load
Plugin returns false/declares unsupported runtime or dependency and SKSE skips it.

### Disabled plugin
DLL renamed/moved/config-disabled so SKSE does not load it.

## Initialization

### SKSE::Init
CommonLibSSE initialization call wiring interfaces such as messaging, serialization, task/Papyrus APIs.

### Logging initialization
Set up file logger before substantial plugin work so failures are captured.

### Papyrus registration
Plugin registers native functions/classes with Papyrus interface.

### Serialization registration
Plugin sets unique serialization ID and Save/Load/Revert callbacks.

### Messaging registration
Plugin subscribes to SKSE/plugin lifecycle messages.

### Task interface
SKSE queue for executing game-safe work later.

### Scaleform registration
Plugin exposes native functions/data to Scaleform where required.

### Trampoline allocation
Reserve executable memory before writing hooks.

## Lifecycle messages

### PostLoad
SKSE message after plugins have loaded; common stage for cross-plugin discovery.

### PostPostLoad
Later plugin interoperability stage.

### InputLoaded
Game input system ready.

### DataLoaded
Game forms/data have loaded and Form lookups are safe.

### NewGame
New-game lifecycle event/message where supported.

### PreLoadGame
Before ESS load.

### PostLoadGame
After ESS load.

### SaveGame
Save lifecycle callback/message as appropriate.

### DeleteGame
Save deletion lifecycle message where supported.

### Load order ready
Practical point after DataLoaded when plugin records can be resolved reliably.

## Initialization ordering

### Static initialization
C++ global constructors executed during DLL load. Avoid engine-dependent work here.

### DLLMain
Windows loader callback. Heavy threading/locking/game calls here are unsafe.

### Loader lock
Windows internal lock held during DLL load; creating threads/loading DLLs/complex work can deadlock.

### Deferred initialization
Schedule work for PostLoad/DataLoaded/main-thread task rather than Load/DllMain.

### Inter-plugin readiness
Another DLL may exist in module list but its internal API/data may not yet be initialized.

### Ready message
Provider-specific notification that consumers can safely request/use API.

### Late initialization
Setup after all game data/plugins/UI systems are available.

## Dependency types

### SKSE dependency
Requires SKSE runtime loader.

### Address Library dependency
DLL requires relocation database.

### CommonLib dependency
Compile-time library; end user generally doesn't install CommonLib itself unless a mod separately packages runtime resources.

### Native framework dependency
DLL expects another DLL/API such as TrueHUD/OAR/IED.

### Papyrus library dependency
PEX scripts call native functions from PapyrusUtil/JContainers/po3 extender/etc.

### Redistributable dependency
Microsoft Visual C++ Runtime required by compiled DLL.

### Root-loader dependency
Component installed beside executable, e.g. Engine Fixes Part 2/graphics proxy, required before SKSE plugin portion works.

### Soft dependency
Feature enabled only if provider DLL/API present.

### Hard dependency
Plugin cannot operate and should fail clearly if provider absent.

## Runtime compatibility

### Compatible runtime range
Executables explicitly accepted by plugin declaration/implementation.

### Unknown runtime
New executable not mapped/tested.

### Address-library compatible but logic incompatible
Relocations exist but struct layout/hook bytes/API behavior changed.

### NG multi-runtime build
One DLL supports multiple declared runtimes with runtime-specific relocations/branches.

### Runtime-specific binary
Separate DLL per runtime family.

### GOG build
Distribution-specific executable target.

### VR build
Separate Skyrim VR ABI target.

## Load failures

### DLL not found
File absent or VFS deployment not exposing it.

### Missing dependency DLL
Windows loader cannot resolve imported library.

### Unsupported runtime
Plugin rejects executable version.

### Address Library missing/outdated
Relocation resolution fails.

### Entry point missing
DLL isn't built/exported as valid SKSE plugin.

### Crash during load
Static/Load initialization hook or dependency fails before main menu.

### Exception in DataLoaded
Plugin loads but crashes when resolving forms/installing later hooks.

### Silent feature disable
Plugin catches failure and logs that one subsystem was skipped.

### Duplicate DLL
Old and new variants both installed under different names and both attempt hooks.

### Wrong architecture
32-bit DLL in 64-bit Skyrim SE/AE or incompatible binary.

## Logging

### SKSE log
SKSE's own loader log.

### Plugin log
Per-DLL log under Documents/My Games/Skyrim Special Edition/SKSE or configured path.

### Load success line
Explicit version/runtime confirmation.

### Hook install line
Confirms code patch installed, not merely DLL loaded.

### Dependency detection line
Records optional/hard API provider version.

### Fatal initialization error
Plugin should state exact unsupported runtime/dependency rather than crash if possible.

## Safe load design

1. Initialize logging first.
2. Call CommonLib/SKSE interface initialization.
3. Validate runtime/dependencies.
4. Register messaging/serialization/Papyrus.
5. Avoid game-data lookup before DataLoaded.
6. Avoid cross-plugin API assumptions before readiness stage.
7. Install hooks only after validating addresses/expected bytes.
8. Keep DllMain/static initialization minimal.
9. Return failure cleanly for unsupported runtime.
10. Log exact plugin/runtime/API versions.

## Sources

- CommonLibSSE-NG Interfaces.h: https://github.com/CharmedBaryon/CommonLibSSE-NG/blob/main/include/SKSE/Interfaces.h
- CommonLibSSE-NG project documentation: https://github.com/alandtse/CommonLibSSE-NG
- SKSE64 upstream: https://github.com/ianpatt/skse64

## Provenance note

CommonLibSSE-NG exposes macros such as SKSEPluginInfo/SKSEPluginLoad and project helpers that simplify declaration boilerplate, but correct lifecycle timing remains plugin-author responsibility.
