# Skyrim Modding Terminology — Object Reference Lifecycle and Interactions

Imported: 2026-09-24
Status: sourced deep-ingestion pass 13

## Base forms and references

### Base form
Reusable definition such as STAT, ACTI, DOOR, CONT, FURN, NPC_ or WEAP.

### ObjectReference
Placed/runtime instance of a base form with position, enable state, ownership, inventory, links, scripts and ExtraData.

### Persistent reference
Reference retained/addressable across ordinary cell unloading because quest/alias/engine relationships require stable identity.

### Temporary reference
Reference primarily governed by cell attach/load/unload lifecycle.

### Created reference
Reference instantiated during gameplay via PlaceAtMe, script, summon, leveled spawn or engine systems.

### Reference handle
Engine-managed weak/stable-ish runtime handle used by native code instead of storing raw pointers across object lifetime changes.

### Raw pointer
Native memory address to current object instance. Unsafe to retain across unload/destruction without lifetime guarantees.

### 3D
Loaded scene-graph representation (NiAVObject tree) for a reference.

### Is3DLoaded
Runtime test indicating scene representation exists.

### Load
Reference/cell 3D/data becoming available.

### Unload
Reference/cell 3D being discarded while logical/saved reference can continue to exist.

### OnLoad
Papyrus event when object 3D loads.

### OnUnload
Papyrus event when object 3D unloads.

### OnCellAttach
Event when reference's cell attaches.

### OnCellDetach
Event when cell detaches.

### OnCellLoad
Event indicating cell load lifecycle; not a universal per-reference initialization event.

### OnReset
Event on cell/reference reset.

## Enable/delete lifecycle

### Enable
Make disabled reference active/visible according to engine rules.

### Disable
Hide/deactivate reference while preserving identity.

### Initially Disabled
Plugin flag making reference start disabled until enabled.

### Enable parent
Reference whose enable state drives child references.

### Enable state opposite
Child inverses parent's enable state.

### Delete
Papyrus/runtime request deleting a created/reference object when permitted.

### DeleteWhenAble
Marks/request deletion when engine can safely remove reference.

### Disabled vs deleted
Disabled reference remains a valid identity and can be re-enabled; deleted reference should not be treated as reusable.

### MarkForDelete
Native/internal deletion state; pointers/references can become invalid later rather than instantly.

### RecycleActor
Aggressive actor reset/reinit command, not equivalent to safe deletion/recreation.

### Resurrect
Restores dead actor state; does not necessarily reset scripts/quests/inventory to plugin defaults.

## Placement and movement

### PlaceAtMe
Creates a new reference near another reference from a base form.

### PlaceActorAtMe
Actor-specific creation helper.

### MoveTo
Moves existing reference to another reference/location.

### MoveToWhenUnloaded
Defers/moves reference according to unloaded-state semantics.

### MoveToMyEditorLocation
Moves reference back to editor placement.

### Editor location
Original plugin-defined placement.

### Package location
AI package destination/current package location.

### TranslateTo
Interpolated scripted movement of a reference.

### SplineTranslateTo
Spline/path interpolated movement.

### Havok move
Physics-driven movement whose transform can be saved as ChangeForm state.

### Teleport door
Moves activating actor to linked destination reference/cell.

## Activation

### Activate
Engine/Papyrus action causing reference's activation behavior.

### OnActivate
Papyrus event delivered when reference is activated.

### Activation blocked
Reference blocks normal activation through BlockActivation.

### BlockActivation
Papyrus/native state preventing default activation while optionally retaining event handling.

### Activation parent
Parent relationship causing one activation to trigger another reference.

### Activate child
Reference receiving propagated activation from parent.

### Player Activation primitive
Trigger/primitive configured to receive player activation interaction.

### TalkingActivator
Non-actor activator capable of dialogue through VoiceType.

## Links

### Linked Ref
Reference-to-reference relationship used by AI, scripts, traps, doors, markers and quest systems.

### Linked Ref keyword
Named relationship allowing multiple independent linked refs.

### GetLinkedRef
Returns linked reference, optionally keyed.

### Nth linked ref
Indexed relationship access in SKSE/native extensions.

### Activation parent link
Specialized link controlling activation propagation.

### Door link
Teleport relationship between load doors.

### Patrol link
Linked markers/references forming patrol path.

## Ownership and locks

### Owner
Actor/faction that owns reference.

### Lock
Door/container lock state.

### Lock level
Novice/Apprentice/Adept/Expert/Master difficulty corresponding to lockpicking skill bands.

### Requires Key
Lock cannot be picked ordinarily and expects matching key.

### Lock key
Key object associated with locked door/container.

### Lock()
Papyrus/ObjectReference function setting locked state/level behavior.

### Unlock()
Papyrus/ObjectReference function removing lock.

### OnLockStateChanged
Extended/native event available in some frameworks/runtime APIs; version/source specific.

## Containers/inventory references

### Container base contents
Items defined on CONT base record.

### Reference inventory
Actual runtime contents after base initialization plus changes.

### Inventory ChangeForm
Save-side delta preserving additions/removals.

### Reset container
Cell/reset restores eligible container contents according to reset rules.

### Quest alias protection
Objects in/created by quest aliases can be exempt from portions of ordinary cell reset.

## Destruction

### Destructible data
Base-form stages describing health thresholds, alternate models, debris/explosions/sounds.

### Destruction stage
Current runtime stage of a destructible object.

### OnDestructionStageChanged
Event delivered when destruction stage changes where supported.

### Destroyed state
Reference/base behavior after final destruction stage.

### Destructible reset exception
CK documentation states destructible objects do not reset during ordinary cell reset.

## Trigger volumes

### Trigger
Invisible primitive/reference detecting actors/objects entering/leaving volume.

### OnTrigger
Event while another reference intersects trigger.

### OnTriggerEnter
Event when a reference enters.

### OnTriggerLeave
Event when a reference exits.

### Trigger count
Number of overlapping trigger objects/references.

### Primitive
Box/sphere/etc. editor geometry used for triggers, navcut, occlusion and collision.

## Furniture and idles

### Furniture / FURN
Interactive base form used for chairs, beds, workbenches, crafting stations and animation markers.

### Furniture marker
Node in furniture NIF defining actor entry/exit/pose positions.

### Furniture marker ID
Engine marker index/category historically used by idle manager to select enter/exit animation.

### IdleMarker / IDLM
Placed/world object defining available idle animations/conditions for actors.

### Sit state
Actor state while using furniture.

### Furniture in use
Runtime occupancy state.

### Interaction location
Precise marker position actor moves to before furniture/paired interaction.

### OnSit / OnExitFurniture
Events around furniture use where supported by Papyrus/runtime.

## Reset semantics

Cell reset generally restores:
- respawning creatures/items;
- actor defaults/health/ActorValues;
- doors/container open/lock state;
- container contents;
- traps;
- many script variables/state with reinitialization.

CK documentation also notes ordinary reset exceptions including:
- enable state;
- destructible state;
- encounter-zone locked level;
- many player-dropped items;
- some alias-protected objects.

These rules are engine-context dependent and should be validated in target cells.

## Diagnostic rules

1. Do not retain native raw ObjectReference pointers across unload/deletion; use handles/FormIDs and re-resolve.
2. Disable is reversible; delete is identity/lifecycle destructive.
3. A reference can logically exist while its 3D is unloaded.
4. Runtime inventory differs from base container contents because save-side deltas persist.
5. Linked refs are semantic dependencies; moving/deleting markers can break packages/traps without record errors.
6. Cell reset does not erase every state category.
7. Load-door tests should use actual linked door/pathing where behavior matters; COC is not equivalent.
8. Script initialization should account for object/load lifecycle rather than assuming OnInit equals every 3D load.

## Sources

- Creation Kit Wiki Cell View Window: https://ck.uesp.net/wiki/Cell_View_Window
- Creation Kit Wiki Cell Reset: https://ck.uesp.net/wiki/Cell_Reset
- Creation Kit Wiki Door: https://ck.uesp.net/wiki/Door
- Creation Kit Wiki Complete Example Scripts: https://ck.uesp.net/wiki/Complete_Example_Scripts
- Creation Kit Wiki scripting category: https://ck.uesp.net/wiki/Category:Scripting
