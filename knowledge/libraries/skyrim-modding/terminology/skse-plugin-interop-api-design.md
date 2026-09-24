# Skyrim Modding Terminology — SKSE Plugin Interoperability and Native API Design

Imported: 2026-09-24
Status: sourced deep-ingestion pass 15

## SKSE Messaging

### SKSE Messaging Interface
Native API for runtime messages between SKSE and plugins and between plugins.

### PluginHandle
Opaque SKSE identity assigned to a loaded plugin.

### RegisterListener
Messaging function registering callback for messages from SKSE or named plugin.

### Dispatch
Messaging function sending typed payload to one/all listeners.

### Sender name
Plugin identifier used for listener registration/message origin.

### Message type
Numeric/application-defined identifier describing payload.

### messageData
Opaque pointer to sender-owned payload interpreted according to API contract.

### dataLen
Payload length for validation.

### PostLoad
SKSE message after all plugins have loaded.

### PostPostLoad
Follow-up stage useful for plugins to establish cross-plugin APIs after PostLoad registration/discovery.

### PreLoadGame
Message before save data is loaded.

### PostLoadGame
Message after save loading lifecycle.

### NewGame
Message indicating new-game lifecycle where supported.

### DataLoaded
Message after game forms/data are loaded; common time for form lookups/API initialization.

## Direct plugin APIs

### RequestPluginAPI
Common ecosystem pattern: provider exports C function returning versioned C++ interface pointer.

### Exported function
DLL function exposed by stable symbol/name so other plugins can discover it with GetProcAddress.

### GetModuleHandle
Windows lookup retrieving loaded DLL module.

### GetProcAddress
Windows lookup retrieving exported function address.

### Interface pointer
Pointer to virtual/interface table owned by provider plugin.

### API version
Integer/enum requested by consumer to ensure interface layout compatibility.

### Current API
Latest provider interface version.

### Backward-compatible API
Provider continues returning older interface layout for consumers built against previous version.

### Breaking API change
Function order/signature/lifetime contract changes requiring new API version.

### Capability query
Consumer tests whether optional feature exists before calling it.

### Plugin-ready message
Provider dispatches message indicating its API/data is initialized and safe to consume.

### Request timing
Consumer should not request another plugin's API before provider has loaded/exported/initialized it.

## Interface design

### Pure virtual interface
C++ abstract class used as ABI contract across DLLs.

### C ABI export
Extern "C" function boundary avoiding C++ name mangling for API acquisition.

### ABI stability
Binary compatibility of vtable/function signatures/types/compiler conventions.

### POD payload
Plain-old-data struct safer to exchange across DLLs than STL containers whose ABI/allocator may differ.

### Ownership
Contract defining which plugin allocates/frees returned memory.

### Lifetime
How long interface/pointer/event payload remains valid.

### Borrowed pointer
Consumer may inspect but must not free/retain beyond documented lifetime.

### Copy-out API
Provider fills caller-owned buffer/value, reducing cross-DLL ownership problems.

### Callback registration
Consumer supplies callback invoked by provider.

### Event listener interface
Object implementation registered for provider notifications.

### Listener removal
Unregister API needed before consumer state unload/shutdown where applicable.

### Reentrancy
Provider invokes consumer callback while in internal processing; callback calling provider again can cause recursion/locks if not designed.

### Thread affinity
API call required on game/main/render thread.

### Thread-safe API
Explicitly safe from multiple threads.

### Error code
Structured failure result instead of crashing/assuming preconditions.

## Common integration examples

### TrueHUD API
Versioned native interface allowing other plugins to request HUD functionality/resources.

### Precision API
Versioned native interface for melee collision integration/callbacks.

### OAR API
Condition/UI/native integration APIs.

### IED API
Native integration/event/placement interfaces exposed to other plugins.

### OBody API
Body-preset/morph state integration.

### SkyrimNet plugin action bridge
Native/Papyrus content interfaces exposing approved actions to AI layer.

## Papyrus interoperability

### Native Papyrus registration
SKSE DLL registers functions with Papyrus VM.

### Script stub
PSC/PEX declaration of native function called by scripts.

### ModEvent
Papyrus/SKSE broadcast mechanism using string event name and simple arguments.

### ModCallbackEvent
Native event source delivering Papyrus-compatible mod events.

### Global function library
Hidden Papyrus script exposing static/global native functions.

### Papyrus API version function
Framework function returning version number for script compatibility checks.

## Serialization interoperability

### Serialization unique ID
Provider plugin's registered co-save namespace.

### Shared serialization
Avoid multiple plugins writing each other's records without documented ownership.

### Form resolution
Use SKSE ResolveFormID on persisted forms across load order changes.

### API state rebuild
After load/revert, provider restores internal state before notifying consumers.

## Dependency styles

### Hard DLL dependency
Consumer cannot function/load without provider.

### Soft DLL dependency
Consumer tests whether provider module/API exists and disables optional integration otherwise.

### Runtime feature negotiation
Consumer/provider agree on supported version/capabilities.

### Compile-time dependency
Consumer includes provider API header/source but can still make runtime relationship optional.

### Header-only API package
Provider distributes interface header separately from implementation.

### API package version pin
Consumer build records which header/API revision it compiled against.

## Diagnostic rules

1. Never call another plugin API before documented readiness stage.
2. Version the interface before changing vtable layout/signatures.
3. Avoid STL allocation ownership across DLL boundaries unless compiler/runtime contract is guaranteed.
4. Validate message dataLen/type before casting.
5. Do not retain event payload pointers beyond callback unless API says ownership transfers.
6. Expose optional integrations as soft dependencies where feasible.
7. Re-resolve FormIDs after save load.
8. Document thread affinity and callback reentrancy.
9. A DLL being loaded is not proof its API initialized successfully.
10. Log API version/provider/consumer at startup for compatibility diagnosis.

## Sources

- Official SKSE64 PluginAPI.h messaging docs: https://github.com/ianpatt/skse64/blob/master/skse64/PluginAPI.h
- CommonLibSSE-NG: https://github.com/alandtse/CommonLibSSE-NG
- TrueHUD API: https://github.com/ersh1/TrueHUD
- Precision API: https://github.com/ersh1/Precision
- OAR example API plugin: https://github.com/ersh1/OpenAnimationReplacer-ExamplePlugin
