# PapyrusUtil Persistence — StorageUtil vs JsonUtil

Imported: 2026-09-24
Source: PapyrusUtil source commit `ff854180db67d330da34371781bcf9e6443b53c3`
Status: canonical persistence model

## StorageUtil

StorageUtil stores named typed values either:
- globally, by using `None` as the object key;
- on a specific `Form`, by passing the Form as `ObjKey`.

Supported principal data families:
- Int;
- Float;
- String;
- Form;
- typed lists of the same families.

### Save locality

The source describes ordinary StorageUtil values as **"Storage functions - values in save game file."**

The native plugin registers SKSE serialization callbacks:
- Save;
- Load;
- Revert.

Operationally, treat ordinary StorageUtil values as **save-local SKSE serialized state**, not external configuration.

### Form-key lifecycle

Source documentation states that if a stored value is attached to a Form and the object is deleted, that value is removed when saving.

### Key namespace

StorageUtil keys are case-insensitive.

Values are separated by type, so the same string key can simultaneously identify an Int, Float, String and Form entry without those entries replacing one another.

Because storage is shared across mods, the upstream source recommends prefixing keys with a mod-specific namespace.

### Global vs object-scoped

`ObjKey = None` means the value/list is global.

A non-None Form means the data is associated with that Form identity.

## JsonUtil

JsonUtil uses similar typed APIs but replaces `Form ObjKey` with a string file path.

### Default root

Files resolve from:

`Data\SKSE\Plugins\StorageUtilData\`

If no `.json` extension is supplied, it is appended automatically.

A path such as:

`../MyData/config`

can escape the default StorageUtilData subfolder and resolve to a sibling path beneath the SKSE plugin data area, as documented by the source.

### Load/save lifecycle

Source rules:
- manual `Load()` / `Save()` usually are not required;
- when the player saves their game, modified JSON files are automatically written;
- if another save is loaded before modified JSON has been saved, in-memory changes are discarded and the file is reloaded from disk;
- `Unload(FileName, saveChanges)` controls cached file lifecycle.

### Cross-save nature

JSON files are external to one ESS/SKSE co-save and therefore can be shared across savegames/profiles unless the mod deliberately namespaces them.

This makes JsonUtil useful for configuration, but dangerous for values that should be specific to one character/save.

## Deprecated StorageUtil File* API

StorageUtil's historical File* functions are explicitly deprecated and proxy to JsonUtil, using:

`../StorageUtil.json`

for backward compatibility.

Do not treat File* functions as ordinary StorageUtil save-local state.

## JSON path API

JsonUtil also exposes path-oriented APIs using JSON-style paths such as:

`.foo.bar[1]`

The source supports:
- scalar path set/get;
- raw JSON insertion;
- path type tests;
- object member enumeration;
- array element enumeration/search;
- array set/append;
- path/index clearing.

## Troubleshooting matrix

| Symptom | First place to inspect |
|---|---|
| Value differs between saves | JsonUtil/external JSON may be intentionally cross-save |
| Value survives plugin reinstall | External JSON may remain on disk |
| Value survives new game | JsonUtil or other external store, not ordinary StorageUtil |
| Value disappears after loading another save | Unsaved JsonUtil in-memory edits may have been discarded |
| Value only wrong on one Form | Object-scoped StorageUtil key/form identity |
| All saves share wrong setting | Shared external JSON / deprecated File* API |
| Co-save cleaning changes state | Ordinary StorageUtil serialized data |
| Form value becomes None | Form identity/load-order/plugin change or invalid/deleted Form |
| Key collision between mods | Un-namespaced StorageUtil/JsonUtil key |

## Migration rules

1. Decide whether each datum is **save-specific** or **cross-save configuration**.
2. Use StorageUtil for save-local shared state.
3. Use JsonUtil for deliberate external/cross-save data.
4. Namespace keys and filenames.
5. Version JSON schemas explicitly for complex data.
6. Migrate old File* values into dedicated JsonUtil files where practical.
7. Never “fix” a plugin record when the authoritative value is actually persistent StorageUtil/JsonUtil state.
