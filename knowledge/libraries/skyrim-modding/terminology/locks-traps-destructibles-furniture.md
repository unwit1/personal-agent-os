# Skyrim Modding Terminology — Locks, Traps, Destructibles, Activators, and Furniture

Imported: 2026-09-24
Status: sourced deep-ingestion pass 13

## Locks

### Lock level
Difficulty assigned to lockable Door/Container references.

### Novice lock
Lowest lock difficulty.

### Apprentice lock
Difficulty approximately associated with Lockpicking 25.

### Adept lock
Difficulty approximately associated with Lockpicking 50.

### Expert lock
Difficulty approximately associated with Lockpicking 75.

### Master lock
Difficulty approximately associated with Lockpicking 100.

### Requires Key
Lock mode requiring key rather than ordinary lockpick resolution.

### Key
KEYM form matching lock data.

### Lockpicking menu
UI/minigame invoked when player activates pickable lock.

### Lock level override
Reference-specific lock state overriding default/open state.

### Lock reset
Eligible doors/containers restore configured lock state on cell reset.

### Broken lock
Runtime state where lock has been broken/unavailable according to engine operations.

### UnlockOwnedDoorsInCell
Papyrus/Game/actor utility used by some systems to unlock doors owned appropriately; context-sensitive.

## Doors

### Animating door
Door whose mesh animation opens/closes in same cell.

### Load door
Door teleporting activator to linked reference in another cell/worldspace.

### Random destination door
Door with configured destination list resolved at first activation; CK docs note selected destination can be saved in save state.

### Automatic door
Door activated by entering a defined area rather than manual activate.

### Sliding Door
Door flag for sliding animation behavior.

### Hidden door
Door flag suppressing local-map representation.

### Minimal Use
Door flag discouraging quest/NPC path routing through it if alternatives exist.

### Do Not Open In Combat Search
Door flag preventing combat-search actors from opening it.

### Open state
Closed/open/opening/closing runtime state.

### SetOpen
Papyrus control changing door/container open state.

## Traps

### Trap
World interaction built from activators/triggers/moving parts/projectiles/hazards/scripts.

### Trap trigger
Trigger volume/activation reference initiating trap.

### Trap controller
Script/reference coordinating trap components.

### Trap hit
Engine/Papyrus event when trap damage/collision affects target.

### OnTrapHit
Event delivered for trap impact where supported.

### Trap reset
Cell reset returns traps to initial state according to CK documentation.

### Pressure plate
Activator/trigger commonly used to start traps.

### Tripwire
Trigger/activator detecting traversal.

### Swinging blade
Animated trap driven by physics/animation/script.

### Projectile trap
Trap spawning/firing Projectile forms.

### Hazard trap
Trap creating Hazard form.

### Linked trap
Trap components connected through linked refs/activation parents.

## Activators

### Activator / ACTI
Interactive world object whose activation behavior is usually provided by scripts/engine hooks.

### TalkingActivator / TACT
Activator capable of dialogue via VoiceType.

### Activation text
Player-facing prompt/name derived from base/reference/menu behavior.

### BlockActivation
Suppress default activation while script handles interaction.

### Activation parent
Reference whose activation propagates to child.

### Random Anim Start
Base flag causing animated activators/doors to start loops at varying time.

### Looping sound
Sound played continuously while activator exists/active.

## Destructibles

### Destruction Data
Base-form configuration defining staged damage behavior.

### Destruction health
Hit points/threshold controlling stage transition.

### Destruction stage
Stage reached at percentage/health threshold.

### Replacement model
Alternate mesh shown for damaged stage.

### Debris
Objects spawned at destruction transition.

### Destruction explosion
Explosion triggered at stage/final destruction.

### Destruction sound
Audio event at stage transition.

### Disable on destruction
Stage behavior making original object disappear.

### Destruction persistence
Destruction state can persist in save and CK notes ordinary cell reset does not restore destructible objects.

## Furniture

### Furniture / FURN
Interactable base form for chairs, beds, workbenches, crafting stations, idle positions and special interaction animations.

### Furniture marker
Named/indexed node embedded in NIF defining interaction location and animation role.

### Entry point
Marker/animation path actor uses to enter furniture.

### Exit point
Marker/animation path used to leave.

### Furniture occupancy
Runtime state marking furniture being used by actor.

### IsFurnitureInUse
Papyrus/condition query.

### IsFurnitureMarkerInUse
Marker-specific occupancy query.

### Workbench furniture
Furniture configured as crafting station linked to keyword/menu.

### Bed
Furniture marker/type enabling sleep interaction.

### Chair
Furniture marker/type enabling sit animation.

### Mannequin
Actor+marker+trigger system mimicking static display mannequin while equipping stored items.

### Weapon rack
Activator/link/trigger system displaying equipped/stored weapon meshes at markers.

### Display case
Door/container/activation assembly used for player housing displays.

### Bookshelf
Container/trigger/script system distributing book meshes into shelf slots.

## Idle markers

### IdleMarker
World object advertising one or more idle animations with conditions.

### Idle animation
IDLE record/animation behavior actor can play.

### Idle marker conditions
Restrictions on race/sex/state/other data determining eligible actors/animations.

### Patrol idle
Idle associated with patrol marker/reference.

### Sandbox furniture
Furniture/idle target discovered by Sandbox procedure.

## Diagnostic rules

1. Doors, containers and traps have reset semantics separate from enable/destruction state.
2. A lock can be reference-specific; editing base Door does not necessarily change placed lock states.
3. Furniture problems often originate in NIF marker nodes, navmesh approach, occupancy or animation—not the FURN record alone.
4. Mannequins/weapon racks/bookshelves are multi-reference scripted systems; copy all required linked/trigger components.
5. Random-destination load doors can bake selected destination into save.
6. Destructible state not resetting can be expected engine behavior rather than a broken script.
7. Trigger/activation and visible mesh are separate layers.

## Sources

- Creation Kit Wiki Door: https://ck.uesp.net/wiki/Door
- Creation Kit Wiki Cell Reset: https://ck.uesp.net/wiki/Cell_Reset
- Creation Kit Wiki TalkingActivator: https://ck.uesp.net/wiki/TalkingActivator
- Creation Kit Wiki Creating a Mannequin: https://ck.uesp.net/wiki/Creating_a_Mannequin
- Creation Kit Wiki Furniture marker notes: https://ck.uesp.net/wiki/GetFurnitureMarkerID
## Native lock representation — CommonLibSSE-NG

Source: `include/RE/E/ExtraLock.h` blob `c3f8eaff91728cbc697a357f3a5d556f8ba22026`.

### Lock level

| Native value | Lock level |
|---:|---|
| -1 | Unlocked |
| 0 | Very Easy |
| 1 | Easy |
| 2 | Average |
| 3 | Hard |
| 4 | Very Hard |
| 5 | Requires Key |

These are native engine enum labels. The player-facing Novice/Apprentice/Adept/Expert/Master terminology is a gameplay/UI convention layered over this lock representation.

### REFR_LOCK flags

- `Locked = 1 << 0`
- `Leveled = 1 << 2`

Current `REFR_LOCK` also stores a base level, optional `TESKey*`, flags, number of tries, and additional reverse-engineered state. `ExtraLock` attaches that structure to an individual reference.

### Diagnostic implications

1. A Door/Container base form does not uniquely determine live lock state; the placed reference's ExtraLock matters.
2. `RequiresKey` is a lock-level enum value while the actual key is a separate TESKey reference.
3. A leveled lock can derive effective difficulty dynamically rather than behaving as one fixed literal level.
4. Established-save/reference state can preserve changed lock data independently of later base-form edits.

