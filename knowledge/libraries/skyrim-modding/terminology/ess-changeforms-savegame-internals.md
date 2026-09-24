# Skyrim Modding Terminology — ESS, ChangeForms, Papyrus Save Data, and Co-Saves

Imported: 2026-09-24
Status: sourced deep-ingestion pass 25

This module describes reverse-engineered save structures as represented by FallrimTools/ReSaver and SKSE. It is not an official Bethesda save-format specification.

## Save containers

### ESS
Skyrim savegame file containing header, plugin table, global data, ChangeForms, Papyrus state and other serialized game state.

### SKSE co-save
Companion file storing SKSE/plugin serialization records associated with one ESS.

### Header
Save metadata including game/version/player/location/time/screenshot/compression-related fields.

### Save compression
Later Skyrim save formats can compress body data; parser must decode according to header compression type.

### PluginInfo
Save section listing loaded full/light plugins used to interpret saved RefIDs/FormIDs.

### FileLocationTable
Save structure containing offsets/counts for major GlobalData and ChangeForm sections.

### GlobalData table
Typed save data blocks for engine subsystems.

### FormID array
Saved form ID table used by save references/structures.

### Visited worldspace array
Saved list of worldspaces visited.

## RefID

### RefID
Compact save-game reference identifier that can point to form from plugin table, created form or save-local identity.

### RefID resolution
Parser maps compact RefID through plugin/load tables to actual FormID/source.

### Plugin index drift
Load order can change between save creation/load; engine remaps plugin-backed identities through save plugin table/current load.

### Missing plugin
Saved RefIDs targeting removed plugin cannot resolve cleanly.

### Created form
Runtime-created form/reference identity stored in save rather than originating directly from static plugin.

## ChangeForm

### ChangeForm
Save record storing differences/state for a game form/reference relative to plugin defaults.

### Change flags
Bitfield specifying which categories of data are present.

### REFR ChangeForm
Saved ObjectReference changes.

### ACHR ChangeForm
Saved Actor reference changes.

### NPC_ ChangeForm
Saved actor-base-related mutable state where applicable.

### QUST ChangeForm
Quest runtime state.

### CELL ChangeForm
Cell runtime/reset/ownership/etc. state.

### FLST ChangeForm
Runtime FormList changes.

### GLOB saved state
Global values are also represented through dedicated global/change state.

### HAVOK_MOVE
Reference ChangeForm flag/data storing Havok-driven transform state.

### INVENTORY
Saved container/reference inventory changes.

### EXTRA_OWNERSHIP
Saved ownership-related ExtraData.

### SCALE
Saved reference scale.

### ANGLES / POSITION
Saved moved transform state.

### ENABLE_STATE
Saved enabled/disabled state.

### Base vs ChangeForm
Plugin supplies base/static data; save overlays mutable changed fields.

### Baked value
Community term for plugin-derived field copied into save ChangeForm and therefore no longer following updated plugin value automatically.

### Unbake
Remove/ignore selected ChangeForm field so current plugin data becomes authoritative again.

## Papyrus section

### Papyrus
Save section containing VM string table, script definitions/instances, references, arrays, active scripts/stacks and related state.

### Script instance
Serialized object of a Papyrus class with variables/properties/state.

### Script definition
Saved metadata/reference to script class.

### Struct/array data
Serialized collections referenced by script variables where supported.

### Active script
Execution stack suspended/running when save was made.

### Suspended stack
Papyrus stack waiting on latent operation/event state.

### Function message
Queued/call-related VM data represented in save internals.

### Unattached instance
Script instance whose owning form/reference can no longer be resolved appropriately.

### Undefined element
Papyrus data whose script/type definition is absent or invalid.

### Missing parent script
PEX dependency removed, preventing class binding/loading.

### Papyrus string table
Deduplicated saved strings referenced by VM data.

### Script state
Current State name stored for script instance.

### Variable data
Saved properties/member values.

## Quest save state

### Quest stage state
Stages/objectives/running/stopped status persisted.

### Alias fill
Reference/location bound to quest alias saved.

### Alias-created reference
Reference created/owned by quest and persisted.

### Quest objective
Displayed/completed objective state.

### Stage fragment side effect
Once fragment changed world/quest state, editing fragment source doesn't undo prior saved consequences.

## Inventory/ExtraData

### Inventory delta
Difference from base container/NPC inventory.

### ExtraDataList
Per-instance data such as enchantment, health/temper, ownership, count, poison.

### Stack split
Several copies of same base form represented as separate stacks because ExtraData differs.

### ChangeForm inventory corruption
Malformed/unresolvable inventory data can contribute save problems; destructive repair should be targeted.

## ReSaver/FallrimTools concepts

### ReSaver
FallrimTools GUI for inspecting and selectively editing Skyrim/Fallout save internals.

### Analysis
ReSaver loads plugin metadata to name/interpret RefIDs/scripts/forms more meaningfully.

### Remove unattached instances
Repair operation deleting Papyrus instances judged unattached. Should be used only with backup/evidence, not routine "clean every save."

### Remove undefined elements
Repair operation targeting VM elements whose definitions are missing.

### Purge plugins
Aggressive cleanup of data associated with removed plugin; high risk and context-dependent.

### Reset Havok
FallrimTools operation clearing HAVOK_MOVE data from eligible REFR ChangeForms.

### Remove non-existent Form instances
Repair workflow for bad references according to tool analysis.

### Save backup
FallrimTools makes backups when writing; external manual backups are still recommended.

### Truncated save
File ends before expected sections/lengths.

### Plugin overflow
Save/plugin table cannot represent expected plugin state.

### Broken Papyrus
Parser reports inconsistent Papyrus structures.

## Save bloat

### Save size growth
ESS grows as world references, ChangeForms, Papyrus arrays/instances and created forms accumulate.

### Normal growth
Large playthrough naturally records many changed references/quests.

### Pathological growth
Runaway spawned references, unbounded arrays, repeated persistent registrations or orphaned objects cause continuing disproportionate increase.

### Created-reference leak
Scripts PlaceAtMe references and never delete/cleanup them.

### Papyrus-array growth
Script continually appends/rebuilds persistent data without pruning.

### ChangeForm accumulation
World edits/inventory/physics state expand save footprint.

### Bloat myth
Large file alone is not proof of corruption; compare growth pattern and parsed categories.

## Co-save serialization

### SerializationInterface
SKSE API for native plugin custom save records.

### Record type
Plugin-defined tag.

### Record version
Schema version.

### Unique serialization ID
Plugin namespace.

### ResolveFormID
Maps persisted form identity to current load mapping.

### Save callback
Writes state.

### Load callback
Reads/migrates state.

### Revert callback
Clears per-save state for new game/revert.

### Orphaned co-save data
Old plugin serialization remains in co-save after DLL removal; behavior depends on SKSE/plugin handling and is not equivalent to Papyrus instance.

## Upgrade/migration implications

### Plugin default update ignored
Field stored in save remains old despite ESP change.

### Script property update ignored
Existing instance preserves old property value.

### Form removed
Save still contains ChangeForm/alias/script reference to deleted form.

### Renumber/compact
Plugin FormID identity changes can invalidate external/save references unless remapped by engine/tool and operation was safe.

### Mid-save uninstall
Removes definitions while save still owns state; highest risk for scripted/quest/native-serialized mods.

### Mid-save update
Safe only if author designed migration for changed scripts/records/state.

## Diagnostic workflow

1. Preserve original ESS and SKSE co-save.
2. Record exact load order/plugin versions.
3. Reproduce issue without editing save.
4. Compare new game vs affected save.
5. Inspect relevant ChangeForm/Papyrus/plugin data.
6. Identify exact stale/broken state.
7. Prefer mod-provided migration/fix.
8. Use ReSaver surgery only with specific target and rollback.
9. Validate repaired copy through repeated load/save/reload.

## Diagnostic rules

1. A save is an overlay of mutable state, not just a pointer to current ESPs.
2. Plugin changes may not affect fields already represented in ChangeForms.
3. Papyrus instances preserve variables/properties/state across updates.
4. Removing a plugin does not automatically remove its saved consequences.
5. ReSaver is a surgical diagnostic/repair tool, not a routine optimizer.
6. Large save size is not by itself corruption.
7. ESS and SKSE co-save must be treated as a pair for native-plugin state.
8. New-game success + existing-save failure strongly points toward persistence/migration state.

## Sources

- FallrimTools/ReSaver: https://github.com/mdfairch/FallrimTools
- FallrimTools ESS parser: https://github.com/mdfairch/FallrimTools/blob/main/src/main/java/resaver/ess/ESS.java
- SKSE64 serialization APIs: https://github.com/ianpatt/skse64
- CommonLibSSE-NG serialization interfaces: https://github.com/alandtse/CommonLibSSE-NG
