# Skyrim Modding Terminology — Papyrus Performance and Native Serialization

Imported: 2026-09-24
Status: sourced deep-ingestion pass 5

## Papyrus scheduling

### Event-driven script
Script that primarily reacts to engine events rather than continuously polling game state.

### Polling script
Script repeatedly checking state through update events/waits. Appropriate in some cases but expensive/fragile when duplicated across many instances.

### OnUpdate loop
Recurring sequence using RegisterForUpdate or re-registering single updates.

### Single-update loop
Pattern using RegisterForSingleUpdate at the end of each update event to avoid some overlapping recurring-registration behavior and to control cadence.

### Update interval
Requested delay between update events. Actual execution is scheduler-dependent and should not be treated as real-time precision.

### Latent function
Papyrus function that suspends the current stack while waiting on engine/time behavior.

### Stack
Execution chain of Papyrus calls/events for one running/suspended task.

### Suspended stack
Stack paused by latent work or other scheduler state.

### Queue pressure
Accumulation of more Papyrus events/stacks than can be serviced promptly.

### Event storm
Large burst of events delivered to many script instances, potentially increasing latency/backlog.

### Script latency
Delay between an event becoming eligible and its Papyrus code actually executing.

### VM budget
Per-frame/time-budget constraints controlling how much Papyrus processing occurs. Raising budgets can steal frametime from the game and is not a substitute for efficient script design.

### fUpdateBudgetMS
Papyrus runtime setting controlling one portion of update processing budget.

### fExtraTaskletBudgetMS
Papyrus runtime setting related to additional tasklet processing time.

### Tasklet
Unit of Papyrus VM work scheduled through its execution system.

### Stack dump
VM diagnostic reporting stacks that have accumulated/failed/been dumped under error conditions. Stack dumps indicate pressure or bad state but require context.

### Infinite loop
Papyrus code that never yields/terminates its current logic. Can monopolize script processing or trigger safeguards.

### Busy wait
Loop repeatedly checking time/state without a latent wait/event. Avoid.

### OnHit spam
High-frequency event pattern when scripts subscribe/attach broadly to combat hit events. Filter/centralize when possible.

### OnItemAdded spam
Potentially high-volume inventory event pattern when attached to actors/containers with many transactions.

### RegisterForUpdate misuse
Large populations of scripts registering frequent updates can scale badly even if each handler is small.

### Event filtering
Reducing delivered/processed events using engine/native registration filters or early cheap guards.

### Central manager
One quest/native manager coordinating state for many objects rather than attaching expensive polling logic to every object.

### Distributed script instances
Many per-reference scripts that each hold state/events. Sometimes natural, but potentially expensive and harder to migrate than centralized data.

## Persistence and script lifecycle

### Save-persistent instance
Script instance whose variables/state are serialized in the save.

### Property default vs saved property
Changing a property/default in a new plugin/script does not necessarily overwrite values already serialized into an existing save instance.

### Script class rename
Changing ScriptName/class identity creates a different script definition. Existing serialized instances of the prior class do not automatically transform into the new class.

### Removed property
Old save can retain serialized variable/property data no longer used by current script definitions.

### Added property
New property may initialize from plugin/default data for newly initialized instances, but migration assumptions must be tested on existing saves.

### Maintenance quest
Quest/script used to perform version checks and state migration after loading/updating.

### Schema version
Stored integer/version describing persisted data format.

### Migration
One-way transformation from old saved schema to new schema.

### Idempotent migration
Migration safe to run/check repeatedly without duplicating effects.

### Revert
SKSE serialization lifecycle callback invoked when state should reset for a new game/revert context.

## SKSE native serialization

### SerializationInterface
SKSE API for a native plugin to save/load custom records alongside a Skyrim save.

### Unique serialization ID
Four-byte/plugin-specific identifier registered so SKSE can associate serialized data with the native plugin.

### Serialization record
Plugin-defined typed/versioned data block written through SKSE.

### Record type
Four-byte or numeric tag identifying a serialized data structure.

### Record version
Plugin-defined schema version supplied with serialized record data.

### Save callback
Native callback invoked when SKSE asks a plugin to serialize state.

### Load callback
Native callback invoked when restoring plugin serialization data from a save.

### Revert callback
Native callback invoked when the plugin should clear save-specific state.

### Form-delete callback
Native callback notifying serialization-aware plugin that a game form has been deleted.

### ResolveFormID
SKSE serialization helper mapping saved old FormIDs to current FormIDs after load-order/plugin-index changes.

### ResolveHandle
Equivalent concept for SKSE-managed handles where supported.

### Co-save
SKSE companion serialization file/data associated with an ESS save and carrying plugin-defined records.

### Serialization migration
Native Load callback reads older record versions and transforms them into current in-memory representation.

### Unknown record version
Serialized version the current plugin cannot safely parse. Correct behavior is to reject/skip/fail gracefully, not reinterpret arbitrary bytes.

### Partial read
Serialization record length/data does not match expected schema. Validate lengths before reading.

### Stable identifier
Persist form identity using SKSE resolution mechanisms or stable plugin-local identities rather than raw transient process pointers.

### Raw pointer serialization
Writing native memory addresses to save data. Invalid across process runs; never treat pointers as persistent object identities.

## External state frameworks

### StorageUtil state
PapyrusUtil key-value data that may be save-associated or globally keyed depending on API use.

### JContainers persistent object
JContainers data retained through its serialization/database mechanisms.

### JSON configuration
External disk state not automatically coupled to one save.

### Save-local vs global config
Critical distinction: resetting an ESS may not reset JSON/INI settings, while deleting an INI does not clear save-local script/native state.

## Performance diagnosis

### Papyrus profiler
Instrumentation/logging used to measure script/event/function activity. Use profiling rather than inferring performance solely from Papyrus log size.

### Hot event
Event/function consuming significant aggregate VM work because it is slow, frequent, or has many instances.

### Instance count
Number of active copies of a script. Tiny per-instance costs can become large at thousands of instances.

### Native-call cost
Papyrus call implemented in engine/SKSE. Native does not automatically mean free; some calls perform searches, filesystem access, scene updates or other expensive work.

### Game-thread requirement
Many engine APIs must execute on the game's main thread. Native plugins should not call arbitrary RE/game state from worker threads without documented synchronization.

### Worker thread
Background native thread appropriate for isolated computation/I/O when game objects are not touched unsafely.

### SKSE task queue
Mechanism for scheduling work back onto game-safe task execution.

### Lock contention
Native threads waiting for shared mutex/data, potentially creating stalls/deadlocks.

### Deadlock
Two or more threads/resources wait cyclically and never progress.

### Race condition
Behavior depends on uncontrolled timing between threads/events.

## Diagnostic rules

1. Optimize total event frequency × instance count × work per event, not just script file length.
2. Prefer event-driven behavior when the engine exposes a reliable event.
3. Do not raise Papyrus VM budgets as the first fix for backlog.
4. Existing-save migration must be deliberately tested; compile success/new game is insufficient.
5. Native serialization records must be versioned and bounds-checked.
6. Resolve saved FormIDs after load rather than trusting old numeric load indices.
7. Never persist raw native pointers.
8. Distinguish ESS Papyrus state, SKSE co-save state, JContainers/PapyrusUtil state and external JSON/INI state.
9. Off-thread native optimization must hand game-object work back to a safe game/task context.
10. A large Papyrus log does not necessarily imply high Papyrus CPU usage; profile/event counts matter.

## Sources

- Creation Kit Wiki Papyrus INI settings: https://ck.uesp.net/wiki/INI_Settings_%28Papyrus%29
- Creation Kit Wiki scripting category: https://ck.uesp.net/wiki/Category:Scripting
- CommonLibSSE-NG SKSE API: https://github.com/CharmedBaryon/CommonLibSSE-NG/blob/main/include/SKSE/API.h
- CommonLibSSE-NG SerializationInterface implementation: https://github.com/CharmedBaryon/CommonLibSSE-NG/blob/main/src/SKSE/Interfaces.cpp
- SKSE source/API lineage: https://github.com/ianpatt/skse64
- FallrimTools/ReSaver: https://github.com/mdfairch/FallrimTools

## Provenance notes

Papyrus VM internals are partly documented and partly reverse-engineered/community-observed. Avoid “Papyrus is slow” folklore. Promote performance claims only when backed by profiling, engine documentation/source-level evidence or reproducible tests.
