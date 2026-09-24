# JContainers v4.3.2 — Lifetime, Serialization, Domains, and Persistence

Imported: 2026-09-24
Status: source-backed persistence model

## Native object model

JContainers implements its own:
- heterogeneous arrays/maps;
- object registry;
- object IDs/handles exposed to Papyrus as integers;
- reference/lifetime accounting;
- garbage collection;
- JSON serialization;
- named domains.

A JContainer object's integer handle is **not a Skyrim FormID**.

## Lifetime

### Temporary ownership
Newly created JContainer objects are temporarily owned by JContainers so immediate chained operations are possible.

### Retain
`JValue.retain` gives the caller durable ownership of an object.

### Release
`JValue.release` removes retained ownership and can allow garbage collection when nothing else references the object.

### releaseAndRetain
Convenience for replacing one retained object with another.

### zeroLifetime
Reduces JContainers' temporary hold so unreferenced objects can be collected sooner.

### Pools
`addToPool` and `cleanPool` group temporary objects for deterministic cleanup.

### Nested ownership
A container holding another JContainer object creates an object graph. Deep copy versus shallow copy determines whether child containers are duplicated or shared.

## SKSE serialization

JContainers v4.3.2 registers:
- Revert callback;
- Save callback;
- Load callback;
- Form-delete callback.

The serialized record type is four-character `JSTR`.

On save:
- JContainers opens the `JSTR` SKSE serialization record;
- writes its domain-master state to the record stream.

On load:
- current state is cleared;
- the JSTR record is found;
- the domain-master state is reconstructed.

On revert:
- domain state is cleared.

## Form identity

JContainers resolves stored Form IDs through SKSE serialization when loading.

It also registers a Form-delete callback so its form observer can react when a referenced Form is deleted.

This is crucial for JFormMap/JFormDB and any container holding Form values.

## Domains

JContainers supports named domains/contexts. The default domain is registered normally; active named domains can expose an amalgamated API under alternate class names.

Stateless functions are not re-registered for non-default domains; stateful functions operate against their domain context.

Treat a domain name as part of persistence/API identity when a mod uses custom domains.

## JDB

JDB is a global retained database root for path-addressed data.

Use namespaced paths such as:
`.yourmod.feature.key`

rather than generic top-level names that may collide with other mods.

## JFormDB

JFormDB associates a Form key with a named storage entry/container, useful for persistent data logically attached to actors/forms without putting variables on scripts.

Because Form identity can be invalidated by missing/deleted plugins/forms, troubleshooting must validate the Form before assuming the JFormDB entry itself is corrupt.

## File JSON

`JValue.readFromFile` / `writeToFile` serialize JContainer structures to external JSON.

That is a different persistence channel from the SKSE JSTR save record.

### Save-local data
JDB/JFormDB/container state retained in JContainers serialized domain state.

### External/cross-save data
Explicit JSON files written through file APIs.

## User directory

Source constants define a per-game user path:
- SE/AE: `My Games/Skyrim Special Edition/JCUser/`
- GOG: `My Games/Skyrim Special Edition GOG/JCUser/`
- VR: `My Games/Skyrim VR/JCUser/`

Do not assume every JContainers JSON API necessarily writes only beneath Data; inspect the exact file/path API.

## Form string encoding

JString supports conversion between Form/FormID and a serialized string identity containing plugin name + low FormID. This provides a load-order-robust representation when used correctly.

## Diagnostic rules

1. A JContainer object handle is not a FormID.
2. Missing object errors can be lifetime/GC problems, not failed JSON parsing.
3. Retain objects that must survive beyond temporary/chained use.
4. Release retained objects when no longer needed.
5. JDB state is save-serialized; explicit JSON exports are filesystem state.
6. Form-valued data must survive plugin/load-order remapping through proper Form resolution.
7. JFormMap/JFormDB issues after removing a plugin can reflect invalid Form keys.
8. Domain name is part of state identity.
9. New-game persistence strongly suggests external JSON/user files or deliberate shared storage, not ordinary JSTR save-local state.
10. When cleaning a save, understand that deleting JSTR serialization state can reset every mod relying on JContainers persistence.
