# Skyrim Modding Terminology — Worldspace, Cells, Persistence, Saves, and LOD State

Imported: 2026-09-24
Status: sourced deep-ingestion pass 2

This reference covers world/cell state and save-game persistence. These concepts are deliberately separated from ordinary plugin conflict terminology because many Skyrim problems persist after the responsible plugin or asset is changed.

## Cells and worldspaces

### Cell
A spatial unit of Skyrim world data. Interior spaces are individual cells; exterior worldspaces are divided into coordinate-based cells.

### Interior cell
Self-contained cell not addressed through exterior X/Y coordinates.

### Exterior cell
Cell belonging to a worldspace and identified by exterior coordinates.

### Cell coordinates
X/Y grid coordinates identifying an exterior cell within a worldspace.

### Worldspace / WRLD
Top-level exterior-world record containing or relating to exterior cells, climate/water/map/world metadata, and worldspace-level systems.

### Persistent reference
Placed reference kept addressable beyond ordinary cell loading/unloading expectations because game systems, quests, scripts, or other references need stable access to it.

### Persist location
Creation Kit/reference metadata indicating the persistence context shown for an object in Cell View.

### Temporary reference
Reference governed primarily by ordinary cell loading/state rules rather than explicit persistence requirements. “Temporary” does not mean its changes can never be represented in a save.

### Initially Disabled
Reference state causing the placed reference to begin disabled until enabled by game logic.

### Enable state
Runtime enabled/disabled state of a reference. Enable-state changes can persist independently of whether a cell later resets.

### Cell reset
Engine process that resets/repopulates eligible cell state after configured game-time conditions. Reset semantics are not equivalent to restoring the entire cell byte-for-byte to plugin defaults.

### Cleared cell
Cell/location state indicating the player has cleared it; cleared and uncleared cells use different default respawn/reset intervals.

### Respawn interval
Game setting controlling how long an eligible cell must remain away/unloaded before respawn/reset rules apply.

### OnReset
Papyrus event sent to eligible objects when their reset behavior occurs.

### OnCellLoad
Papyrus event related to reference cell loading. It may not fire simply because the player moved locally if the area never unloaded.

### PCB
Console command commonly used during testing to purge cell buffers, useful when forcing unload/reload scenarios. It is a debugging aid, not a normal player-facing fix.

### COC
**Expansion:** Center On Cell. Console/developer command used to move the player directly to a named cell for testing.

### COW
**Expansion:** Center On World. Console/developer command used to move the player to specified coordinates in a worldspace.

### Reference state
Runtime/save-side state associated with an individual placed reference, such as enable state, movement, inventory, ownership-related state, Havok movement, activation-related changes, or other change flags.

## Navmesh and pathing

### Navmesh
Navigation geometry used by actors for movement/pathfinding through cells and worldspaces.

### Navmesh triangle
Basic traversable polygonal unit in navmesh geometry.

### Navmesh edge
Boundary/connection between navmesh triangles; valid connectivity determines where actors can path.

### Navmesh island
Disconnected navmesh region with no traversable connection to the intended surrounding navigation network.

### Navmesh portal/connection
Navigation relationship allowing pathing across cell boundaries or linked navmesh regions.

### Finalized navmesh
Navmesh that has undergone the editor's required finalization/connection process so edge links and related navigation data are valid for game use.

### Deleted navmesh
Navmesh record removed by an override. This is a high-risk compatibility condition because other navigation data can reference the original navmesh.

### Navmesh override
Plugin modification of an existing NAVM record. Multiple location mods modifying the same navmesh often require deliberate compatibility work rather than simple load-order advice.

### Pathfinding
Engine process that finds navigable routes across navmesh and related movement data.

### Navmesh conflict
Competing changes to the same navigation data that can produce inaccessible areas, actors stuck at boundaries, broken door transitions/pathing, or lost changes.

### Preferred pathing
Navigation metadata that biases actor route selection without simply making all other traversable geometry unavailable.

### Navmesh diagnostic principle
An actor failing to walk somewhere is not enough to conclude “AI package bug.” Inspect package target/conditions and navigation connectivity separately.

## Save-game state

### ESS
Common technical name for Skyrim save-game file data. FallrimTools/ReSaver models Skyrim save content as ESS data structures.

### Save header
Save metadata identifying game/version and other top-level save information.

### Plugin table
Save section recording plugins associated with the save's loaded form mapping.

### FormID array
Save-side table used in resolving forms referenced by saved state.

### ChangeForm
Save-game structure containing changed state for a game form/reference relative to its plugin-defined baseline.

### Change flag
Bit/flag describing categories of change represented in a ChangeForm, such as reference movement/Havok-related changes and many other form-type-specific changes.

### ChangeForm table
Collection of changed-form state serialized into the save.

### Created form
Runtime-created form/reference whose identity/state originates during gameplay rather than as an ordinary placed/static plugin form.

### Papyrus save section
Serialized Papyrus VM state stored in the save, including script definitions/instances, variables, stacks and related runtime data represented by the save format/tool.

### Script instance
Serialized runtime instance of a Papyrus script associated with a form/alias/other host.

### Active script / stack
Papyrus execution state that may be running or suspended when serialized.

### Suspended stack
Papyrus call stack paused awaiting latent work/event/timing and capable of continuing after load when valid.

### Orphaned script instance
Troubleshooting term for saved script-instance state whose expected backing mod/form/script relationship no longer exists or is no longer valid. Do not automatically delete all suspected instances without understanding dependencies.

### Unattached instance
ReSaver/FallrimTools troubleshooting concept for script instances not attached to a resolvable in-game object in the expected way. Whether removal is safe is context-dependent.

### Undefined element
Save-side Papyrus object/type/reference that cannot be resolved against the currently available script/plugin environment.

### Missing plugin in save analysis
A plugin recorded/expected by the save that is not present in the current environment, potentially making saved FormIDs or script data unresolved.

### Save-baked state
Informal modding term for runtime data already stored in a save. Replacing an ESP, PEX, INI, or DLL does not necessarily erase or rebuild that saved state.

### Clean save
Ambiguous community term. It may mean a save made after removing a mod and attempting cleanup, or simply a save without the target mod. Agent OS should ask/record the actual procedure rather than treating “clean save” as a precise technical state.

### New-game test
Troubleshooting test on a newly started save with no pre-existing state from the mod being diagnosed. Valuable for separating plugin/current-install defects from save persistence/migration problems.

### Existing-save test
Test using the user's established save, which preserves saved script/reference/quest/changeform state and therefore exercises migration/upgrade compatibility.

### Save migration
Intentional logic/process for moving persisted mod state from one version/schema to another.

### Serialization version
Version identifier stored by a native plugin or script system so saved custom data can be interpreted/migrated correctly after updates.

### SKSE co-save
Companion save data used by SKSE/native plugins to persist plugin-defined serialization records alongside the main Skyrim save.

### ReSaver
FallrimTools save-game inspection/repair application for Bethesda games, capable of parsing Skyrim save structures including plugins, ChangeForms, FormIDs and Papyrus data.

### FallrimTools
Project containing ReSaver and the underlying parsers/models for Bethesda save files.

### Save repair
Targeted modification of save data to remove or correct known invalid state. Save repair is inherently consequential: preserve backups and prefer an identified fault over generic “clean everything” operations.

### Truncated save
Save whose expected binary structures end prematurely or cannot be completely parsed. FallrimTools tracks truncation/broken-state conditions separately from ordinary script clutter.

### Broken Papyrus section
Save state where Papyrus structures fail parsing/validation. This is more severe than routine Papyrus log warnings.

### Nonexistent created form
Created-form identity referenced by saved Papyrus state even though the corresponding created ChangeForm no longer exists; FallrimTools contains targeted handling for this class of inconsistency.

### Null FormList entry
Saved/list state containing unresolved/null entries in a FormList. FallrimTools includes a targeted cleanup operation for null FormList entries; this should not be generalized into arbitrary list deletion.

### Havok ChangeForm state
Saved physical-movement state for references. ReSaver exposes targeted handling for reference ChangeForms carrying Havok movement state.

## LOD/worldspace state

### Active exterior cells
Nearby exterior cells loaded as full world data around the player. Distant systems cover content outside that active area.

### uGridsToLoad
INI-controlled active exterior grid size. Increasing it is not a general modding fix and can have wide performance/state consequences.

### Large reference
Skyrim SE/VR feature allowing selected full models to remain displayed outside ordinary active exterior cells.

### Large-reference grid
Distance/grid system controlled separately from ordinary active-cell distance and LOD.

### Large-reference list
Worldspace RNAM data identifying eligible large references. DynDOLOD documents that the relationship to ESM-flagged masters is important to correct engine behavior.

### Large-reference bug
Vanilla SSE/AE/VR rendering/state bugs triggered under documented conditions, especially when large-reference records are changed by non-master plugins. This is not the same thing as ordinary object-LOD mismatch.

### Dynamic LOD
DynDOLOD runtime/dynamic distant-reference system capable of using object-LOD, full or specialized dynamic models according to distance/grid behavior.

### NearGrid
DynDOLOD dynamic-LOD grid beginning outside the active uGridsToLoad area for ordinary dynamic references.

### FarGrid
DynDOLOD dynamic-LOD grid used farther away; in SSE/VR its relationship to large-reference distance differs from NearGrid.

### Full model vs LOD model
Nearby/large-reference rendering can use a full asset, while ordinary distant object/tree/terrain LOD uses optimized distant representations. A visual mismatch may be a transition problem between these systems rather than “bad texture” alone.

### LOD transition
Distance at which rendering switches between full reference representation and one of Skyrim's distant LOD systems.

## Diagnostic rules encoded for Agent OS

1. If a bug occurs only on an established save but not a new game, investigate persisted ChangeForms, Papyrus/native serialization, quests, aliases and migration before blaming current plugin load order alone.
2. Do not use “clean save” as a precise diagnostic term; record exactly which mods/scripts/state were present and what cleanup procedure was performed.
3. Back up saves before any ReSaver/save-repair operation. Prefer narrow, evidence-backed repairs to bulk deletion.
4. A removed mod can leave meaningful persisted state; deleting its files does not imply its save-side state vanished.
5. Cell reset does not reset every form of persistent quest/script/enable state.
6. Navmesh conflicts are navigation-data conflicts, not merely asset or package conflicts.
7. Large-reference problems are a distinct SSE/VR world-rendering system and should be diagnosed separately from object/tree/terrain LOD.
8. For worldspace visual bugs, record whether the symptom occurs as a full model, large reference, dynamic LOD, object LOD, tree LOD, or terrain LOD and at what distance.
9. Treat uGridsToLoad changes as environment changes with broad consequences, not a default troubleshooting recommendation.
10. Save-side evidence and current-plugin evidence must be reconciled; either one alone can misidentify the cause.

## Sources

- Creation Kit Wiki — Cell View Window: https://ck.uesp.net/wiki/Cell_View_Window
- Creation Kit Wiki — Cell Reset: https://ck.uesp.net/wiki/Cell_Reset
- Creation Kit Wiki — CenterOnWorld: https://ck.uesp.net/wiki/CenterOnWorld
- DynDOLOD — Large References: https://dyndolod.info/Help/Large-References
- DynDOLOD — Dynamic LOD: https://dyndolod.info/Help/Dynamic-LOD
- DynDOLOD — terminology/reference pages: https://dyndolod.info/Terminology
- FallrimTools/ReSaver upstream: https://github.com/mdfairch/FallrimTools
- FallrimTools ESS implementation/model: https://github.com/mdfairch/FallrimTools/blob/main/src/main/java/resaver/ess/ESS.java

## Provenance notes

- Save-game internals are partly reverse-engineered; FallrimTools is strong technical evidence for structures the tool parses but is not an official Bethesda file-format specification.
- Creation Kit Wiki cell/reset behavior is historical documentation and should be validated against current runtime behavior when exact edge cases matter.
- DynDOLOD documentation is the preferred specialist source for large-reference and dynamic-LOD terminology.
- Navmesh terms in this file are intentionally conservative. A later dedicated navmesh ingestion should add CK/xEdit record-level details and reproducible compatibility procedures before Agent OS attempts automated navmesh repair.
