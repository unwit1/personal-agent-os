# Skyrim Modding Knowledge — Advanced Papyrus Persistence, Concurrency, and Save-State Diagnostics

Imported: 2026-09-24
Status: sourced encyclopedia pass 4

This module extends the Papyrus glossary with lifecycle, concurrency and persistence concepts needed to diagnose long-running saves safely.

## VM execution model

### Papyrus VM
Event-driven virtual machine that schedules script stacks independently of the native game call stack.

### Stack
Papyrus call chain associated with an event/function execution.

### Active stack
Stack currently eligible/running in the VM.

### Suspended stack
Stack paused on a latent/native operation and stored so execution can resume later.

### Frozen stack
Diagnostic/community term for a stack that is not making expected progress. Determine actual waiting state before attempting repair.

### Latent call
Papyrus/native call allowed to suspend a stack and resume later.

### Non-latent call
Call expected to complete without yielding the stack through Papyrus latency semantics.

### VM queue
Pending work/events/stacks waiting for Papyrus execution time.

### Event queue
Pending script-event deliveries awaiting processing.

### Script latency
Delay between event occurrence and script execution caused by scheduling/workload.

### Stack dump
Diagnostic output when VM conditions cause stacks to be reported. Repeated dumps indicate pressure/state problems but do not identify one culprit automatically.

### Infinite loop
Script path that never yields/terminates and can consume VM resources catastrophically.

### Busy polling
Repeated frequent updates checking state that could have been event-driven or less frequent.

### OnUpdate storm
Large number of registered scripts delivering update events at high frequency.

### Single-update pattern
Schedule one future update then explicitly schedule the next, giving script logic more control than a permanent repeating registration.

## Event registration

### RegisterForUpdate
Registers repeating timed events.

### RegisterForSingleUpdate
Registers one timed event.

### RegisterForModEvent
SKSE Papyrus registration for named mod events.

### RegisterForMenu
SKSE registration for menu open/close events.

### RegisterForKey
SKSE input registration.

### Registration persistence
Whether a registration survives save/load and how it is restored depends on the registration API/framework and serialized VM/native data.

### Unregister
Remove a prior event/update subscription.

### Stale registration
Saved registration remains for a script/object that no longer needs it after update/removal.

### Event fan-out
One engine/mod event delivered to many registered instances, potentially causing a burst of VM work.

## Script instances and lifecycle

### Script definition
Compiled class/type metadata loaded from PEX.

### Script instance
Runtime object containing variables/properties/state for one attached script.

### Instance host
Form/reference/alias/effect/etc. to which the script instance belongs.

### Base-form script
Script attached to a base object record.

### Reference script
Script instance associated with a placed/runtime reference.

### Quest script
Script attached to a quest instance.

### Alias script
Script instance attached to a quest alias and lifecycle-bound to that alias's filling/clearing behavior.

### ActiveMagicEffect script
Instance created for one applied magic effect and normally ending with that effect's lifecycle.

### Fragment script
CK-generated script class/instance implementing quest/dialogue/scene/package fragments.

### Generated fragment
Compiler/CK-produced function tied to editor data rather than manually called like ordinary API code.

### Property state
Values of script properties for an attached instance. Existing save-side values can remain after source defaults change.

### Variable state
Runtime script variables serialized into the save.

### Papyrus state
Current declared state-machine state of a script instance.

### Instance version
Mod-defined schema/version variable used by update logic to decide which migration steps are needed.

## Save serialization

### Papyrus save section
ESS global data section containing script definitions, instances, references, arrays, active scripts/stacks and other VM state as parsed by FallrimTools.

### ScriptInstance table
Save collection mapping serialized Papyrus script instances.

### Script reference
Serialized Papyrus object/reference pointing at another VM/game object.

### Papyrus array
Serialized array object potentially shared/referenced from script variables.

### ActiveScript
FallrimTools terminology/model for serialized active Papyrus stacks/execution state.

### SuspendedStack
FallrimTools model for suspended Papyrus execution.

### FunctionMessage
Serialized queued/call-message data associated with VM work.

### String table
Papyrus save structure storing script strings/names efficiently.

### Undefined element
Saved Papyrus object whose type/script/form cannot be resolved against the current environment.

### Unattached instance
FallrimTools/ReSaver category for a script instance that lacks a valid expected attachment.

### Nonexistent-created-form instance
Script instance points to a runtime-created RefID for which no corresponding created ChangeForm exists. FallrimTools exposes a targeted cleanup for this condition.

### Papyrus error state
ReSaver parser marks Papyrus section broken/error when serialized structure cannot be parsed consistently.

### Truncated save
File ends/misses required data before expected structures are complete.

## ChangeForms and script interaction

### ChangeForm
Serialized changed state for one game form/reference.

### Created ChangeForm
ChangeForm for a runtime-created form/ref.

### Reference ChangeForm
Saved changes to a placed/runtime reference.

### Quest ChangeForm
Saved quest progression/alias/etc. state represented in applicable change data.

### FLST ChangeForm
Saved FormList runtime changes.

### HAVOK move change
Reference ChangeForm flag/data recording Havok/position state; ReSaver includes a targeted Havok-reset operation.

### Null FormList entry
Invalid/unresolved list entry inside a saved FLST ChangeForm; ReSaver provides a targeted cleansing operation.

### ChangeForm removal
Consequential save surgery deleting saved state for a form. It can reset data but can also break dependencies/quests/scripts.

## Co-saves and native serialization

### SKSE co-save
Companion file containing SKSE/plugin serialization data associated with a Skyrim save.

### Serialization record
Plugin-defined data record written through SKSE's serialization interface.

### Serialization unique ID
Native plugin identifier/namespacing used to distinguish its stored records.

### Serialization version
Plugin-defined schema version for saved native data.

### Revert callback
SKSE serialization lifecycle callback allowing a plugin to clear state before loading/new game.

### Save callback
Native plugin callback used to write current custom state.

### Load callback
Native plugin callback reading/migrating serialized state.

### ResolveFormID
SKSE serialization helper remapping stored FormIDs through the current load environment during load.

### Native-state migration
Version-aware conversion of old plugin serialization records to a current schema.

### Orphaned co-save
SKSE companion save remains while corresponding ESS is gone; Engine Fixes can optionally clean this class.

## External framework persistence

### PapyrusUtil storage
Persistent data maintained through PapyrusUtil/native serialization/external utility features.

### JContainers state
Serializable native container graph associated with Papyrus handles and framework persistence.

### MCM Helper settings
Configuration persistence that can be file-based/framework-managed rather than just ordinary script variables.

### FISS/FISSES preset
External configuration export designed for deliberate import/export and not identical to live save state.

### JSON state
External mod data stored in JSON files. Removing a save may not remove this data.

### Per-save external data
External data keyed by save/player identity.

### Global external data
Framework data shared across saves/configurations.

## Update and uninstall behavior

### In-place update
Installing a new mod version over an established save and relying on migration compatibility.

### New-game-only update
Version/change whose author does not support migration from existing saves.

### Script property reset expectation
Incorrect assumption that recompiling/changing default property values automatically resets every existing saved instance.

### Removed property
Script variable/property removed from a newer class while old serialized instance data can still exist.

### Renamed script
New script class name does not magically migrate instances of the old class.

### Orphaning
Removing forms/scripts while serialized references/instances still exist.

### Uninstall mid-save
Removing a stateful mod from an active playthrough. Safety depends on what persistent forms/scripts/native data it created.

### Uninstall procedure
Author-defined steps intended to stop quests/events, remove runtime objects and prepare a save before files are removed.

### Save cleaner
Tool capable of inspecting/removing classes of stale state; not a magic “make any uninstall safe” operation.

## Safe diagnosis rules encoded for Agent OS

1. Always preserve the untouched save and SKSE co-save before ReSaver work.
2. Use parser/tool-defined targeted cleanup classes rather than bulk-removing anything labeled “orphan.”
3. Compare established save against a new-game reproduction before concluding current scripts are defective.
4. Property/default changes do not necessarily replace serialized values on existing instances.
5. Script migration and native serialization migration are separate if a mod uses both Papyrus and an SKSE DLL.
6. External JSON/FISS/framework storage can outlive the ESS/co-save.
7. Repeated stack dumps warrant workload/event/registration analysis before “increase Papyrus budget” tweaks.
8. If a script instance host is missing because its plugin/FormID disappeared, restore/understand the dependency before deleting save objects.
9. Never automate ChangeForm deletion for quests/reference systems without a mod-specific repair contract.
10. Record exact before/after save hashes and ReSaver actions so repair is reversible and auditable.

## Sources

- FallrimTools/ReSaver source ESS model: https://github.com/mdfairch/FallrimTools/blob/main/src/main/java/resaver/ess/ESS.java
- FallrimTools project: https://github.com/mdfairch/FallrimTools
- Creation Kit Wiki Papyrus logging: https://ck.uesp.net/wiki/User:DavidJCobb/Papyrus_logging
- SKSE plugin API/source: https://github.com/ianpatt/skse64
- CommonLibSSE-NG serialization APIs: https://github.com/alandtse/CommonLibSSE-NG
- PapyrusUtil: https://github.com/eeveelo/PapyrusUtil
- JContainers: https://github.com/ryobg/JContainers
