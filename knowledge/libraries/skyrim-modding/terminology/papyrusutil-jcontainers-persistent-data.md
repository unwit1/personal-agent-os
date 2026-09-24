# Skyrim Modding Terminology — PapyrusUtil, JContainers, Persistent Data, and External JSON

Imported: 2026-09-24
Status: sourced deep-ingestion pass 26

## PapyrusUtil

### PapyrusUtil
SKSE plugin/library extending Skyrim Papyrus with utility functions, persistent key-value storage, JSON I/O, object utilities and events.

### StorageUtil
PapyrusUtil API storing typed values by key, either globally or attached to a Form key.

### Global StorageUtil value
Value whose object key is None, shared process/save-wide within PapyrusUtil's storage namespace.

### Form-keyed StorageUtil value
Value attached to a specific Form identity.

### Storage key
String name identifying one stored value/list.

### Key namespace
Author prefix convention preventing unrelated mods from colliding on the same global/form key name.

### Typed storage
Int, Float, String and Form values are stored in separate typed namespaces, so identical key text can exist independently by type.

### StorageUtil list
Dynamic typed list managed by PapyrusUtil, unlike fixed native Papyrus arrays.

### IntList / FloatList / StringList / FormList
StorageUtil's dynamic list families.

### Storage persistence
StorageUtil data is serialized so values remain until explicitly unset/cleared, subject to the underlying keyed Form's lifetime where applicable.

### Deleted-form cleanup
PapyrusUtil documentation notes Form-keyed values are removed when the keyed object is deleted and the game is saved.

### Unset
Remove one stored value.

### Clear
Remove values/list contents deliberately when state is no longer needed.

### File* StorageUtil functions
Older file-backed StorageUtil API retained for compatibility.

### Deprecated file storage
PapyrusUtil source explicitly deprecates StorageUtil File* functions in favor of JsonUtil.

## JsonUtil

### JsonUtil
PapyrusUtil API storing typed values/lists in external JSON files.

### StorageUtilData
Default PapyrusUtil JSON data directory under `Data/SKSE/Plugins/StorageUtilData/`.

### JSON filename
String path used as JsonUtil backing store; extension can be appended automatically.

### Subdirectory path
JsonUtil filename can point outside default subdirectory using relative path conventions supported by API.

### Load
Explicitly load JSON document into PapyrusUtil cache.

### Save
Write modified cached JSON state to disk.

### Unload
Drop cached JSON state, optionally saving changes.

### Pending save
JsonUtil state where in-memory document differs from disk.

### Automatic save
PapyrusUtil source documents automatic writing of modified JsonUtil files when player saves the game.

### Cross-save setting
External JSON is not inherently tied to one ESS, so it can persist across multiple saves/characters.

### Save-local vs external state
StorageUtil is appropriate for save-associated runtime state; JsonUtil is often appropriate for settings/config intended to survive new games.

### JSON parser error
Malformed external file prevents clean load and should be diagnosed from framework log/API status rather than treated as Papyrus-array corruption.

## ObjectUtil / MiscUtil / ActorUtil

### ObjectUtil
PapyrusUtil helper family for object/form operations.

### MiscUtil
Utility functions including filesystem/string/world helpers.

### ActorUtil
Actor-oriented helpers, including package/combat/actor utility operations depending on version.

### Custom event utility
PapyrusUtil includes additional event and utility helpers beyond vanilla Papyrus.

## JContainers

### JContainers
SKSE plugin extending Papyrus with JSON-like dynamic arrays, maps/dictionaries, file serialization, Lua support and a C++ API.

### JValue
Generic JContainers handle/value abstraction.

### JObject
JContainers object/map abstraction.

### JMap
Associative string-keyed container.

### JArray
Dynamic ordered array.

### JFormMap
Map keyed by Forms.

### Handle
Integer-like JContainers reference identifying a container/object managed by JContainers' own memory system.

### Retain
Keep a JContainers object alive beyond temporary/reference lifetime.

### Release
Drop retained ownership/reference.

### JContainers garbage collector
Framework-managed lifecycle reclaiming unreachable/unretained data.

### Object graph
JContainers structures can contain nested arrays/maps/values unlike vanilla Papyrus arrays.

### Heterogeneous data
Container can represent richer mixed/nested data through JValue/JObject semantics.

### JSON import
Create JContainers object from JSON text/file.

### JSON export
Serialize JContainers object to JSON.

### File-backed object
JContainers state saved to disk separately from ESS.

### Embedded Lua
JContainers provides Lua integration for advanced scripted data manipulation.

### C++ API
Native SKSE plugins can interoperate with JContainers.

## Persistence models

### Save-local script variable
Stored directly in Papyrus instance inside ESS.

### Save-local StorageUtil
Persistent shared data serialized by PapyrusUtil with the save.

### External JsonUtil file
Disk JSON shared independently of one save unless author creates save-specific filenames.

### JContainers save data
Container/object state serialized through JContainers' mechanisms and/or exported externally depending on API.

### MCM preset file
External config created for settings portability.

### Canonical settings store
One selected location should own configuration truth; mirroring the same setting into several systems creates drift.

### Migration
Versioned code transforming old key/schema/container format to current format.

### Schema version
Stored version number inside external or save-local data.

### Idempotent migration
Safe to re-run without duplicating entries or progressively corrupting data.

## Inter-mod interoperability

### Shared key contract
Two mods intentionally read/write same StorageUtil/JContainers path according to documented API.

### Unintentional key collision
Generic key such as `enabled` used globally by unrelated mods.

### Soft integration
Consumer checks whether a known key/object exists before using it.

### Storage API as IPC
Persistent data store used as loose inter-mod communication channel.

### Event + storage pattern
Producer writes current state to storage then broadcasts ModEvent; consumers read canonical data.

## Failure modes

### Stale external config
JSON survives uninstall/reinstall/new game and reintroduces old values.

### Corrupt JSON
Manual edit/truncated write causes parser failure.

### Save/config mismatch
ESS expects one state while external JSON contains another character/profile's settings.

### Handle leak
JContainers objects retained but never released/cleaned.

### Unbounded storage growth
Mod continually writes unique keys/list entries and never prunes.

### Form-key orphan
Stored identity points to removed plugin/form.

### Cross-profile bleed
Multiple MO2 profiles share the same external Data/SKSE/Plugins JSON path and unintentionally share settings.

### Overwrite race
Two systems write the same external JSON without coordinated ownership.

## Design rules

1. Prefix global keys with mod/project identifier.
2. Choose explicitly between save-local and cross-save storage.
3. Version persistent schemas.
4. Never assume external JSON resets with a new game.
5. Keep generated/cache data separate from user-authored settings.
6. Prune abandoned handles/keys/lists.
7. Back up user-editable config before migration.
8. Do not store raw runtime pointers or unstable load-order FormIDs as naked integers when a resolvable form identity can be used.
9. Treat JContainers/PapyrusUtil DLL version as runtime dependency distinct from PSC compile stubs.

## Sources

- PapyrusUtil StorageUtil source: https://github.com/eeveelo/PapyrusUtil/blob/master/Scripts/Source/StorageUtil.psc
- PapyrusUtil JsonUtil source/API
- JContainers upstream: https://github.com/SilverIce/JContainers
