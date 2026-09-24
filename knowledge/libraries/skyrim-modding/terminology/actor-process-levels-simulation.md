# Skyrim Modding Terminology — Actor Processing Levels, Simulation, and Loaded-State Behavior

Imported: 2026-09-24
Status: sourced deep-ingestion pass 26

## Processing levels

### AIProcess
Engine structure tracking actor AI/equipment/animation/combat/package processing state.

### ProcessLists
Engine singleton tracking actors grouped by processing level.

### High Process
Highest-detail actor processing tier.

### Middle High Process
Intermediate actor processing tier.

### Middle Low Process
Lower-detail actor processing tier.

### Low Process
Minimal processing tier for distant/unloaded actors.

### Processing level
Current engine tier deciding which actor systems are actively simulated in detail.

### GetActorsByProcessingLevel
po3 Papyrus Extender function exposing actors by process tier: High=0, MiddleHigh=1, MiddleLow=2, Low=3.

### HighProcessData
Reverse-engineered structure containing detailed actor runtime data such as combat, detection/head tracking, animation and other high-process state.

### MiddleHighProcessData
Intermediate process structure with reduced runtime state.

### MiddleLowProcessData
Lower-detail process data.

## Loaded-state relation

### Loaded cell
Interior/current exterior grid whose references/3D are present.

### Attached cell
Cell active in process/world simulation around player.

### High-process actor
Usually near/loaded enough for detailed AI, pathing, animation and combat.

### Distant actor
Often reduced to low process and does not run all high-detail behaviors continuously.

### Actor 3D loaded
Skeleton/NiNode exists.

### Actor logically loaded
Actor/form/reference exists in game/save even if 3D is absent.

### High process != simply persistent
Persistence controls lifetime/addressability; process level controls simulation detail.

### High process != simply essential
Importance flags can affect behavior but process tier is a separate engine concept.

## AI behavior

### Package evaluation
AIProcess selects/updates package according to tier and engine scheduling.

### High-detail pathing
Nearby actors receive full navigation/movement updates.

### Low-process travel
Distant actors may advance package/location state using simplified simulation rather than literal rendered walking.

### Combat processing
Combat actors are generally promoted to detailed processing where possible.

### Detection processing
Detailed detection state exists primarily for actors receiving adequate process level.

### Head tracking
High-process visual behavior.

### Lip/facial animation
Depends on actor being processed/rendered at sufficient detail.

### Equipment state
Intermediate/high process structures maintain equipped object state needed for rendered actors.

## Actor limits

### High actor count
Number of actors in detailed process around player.

### Actor process limit
Engine hard/static limits can cap some mover/morph behaviors; Actor Limit Fix raises selected limits.

### High Actor threshold
Performance cost rises as more actors require pathing, animation, AI and physics.

### Crowd
Many actors simultaneously in loaded/high process.

### Simulation budget
CPU time available for actor AI/pathing/animation systems.

### Process promotion
Actor moves from lower to higher processing tier as player approaches/loads relevant cell.

### Process demotion
Actor moves to lower tier as player leaves area.

## Save and state implications

### Temporary high-process state
Some modifiers/data exist only while actor has middle/high processing and can reset/recalculate after unload.

### Persistent actor values
Other ActorValue/script/quest data remains in save regardless of process tier.

### Package catch-up
Distant actor may appear at a logical destination when cell loads rather than having simulated every step.

### Unloaded animation state
No 3D means OAR/graph/node operations may be unavailable/deferred.

### Deferred morph
Body/Face/Node frameworks often wait until actor 3D loads to apply visual state.

### Deferred equipment display
IED/physics/display systems attach when actor skeleton exists.

## Scripting implications

### Nearby actor scan
Polling all High-process actors is much cheaper/more relevant than iterating every Actor form in the game.

### Global actor scan
Enumerating Low-process actors can involve thousands of references and should be avoided unless necessary.

### OnLoad-driven initialization
Visual/node operations should initialize when 3D/process state is ready rather than assuming actor always has a skeleton.

### Is3DLoaded guard
Check before node/visual manipulation.

### Distance polling anti-pattern
Scripts repeatedly scanning all actors to discover nearby ones; use process/event/native queries where available.

### Low-process limitation
Animation graph variables, node transforms, active combat details and some packages cannot be treated as fully available for unloaded actors.

## Common symptoms

### NPC appears to teleport
Distant simplified package simulation/catch-up rather than literal path traversal.

### NPC frozen in crowd
Mover/actor processing limit, pathing overload or AI budget pressure.

### No facial animation on distant actor
Actor not in detailed morph/visual processing.

### Node API returns nothing
3D not loaded.

### Animation event missing
Actor graph not currently instantiated/active at required process level.

### Follower disappears then catches up
Follower package continues logically while actor unloads and later teleports/reloads according to framework/game.

### Remote script behaves inconsistently
Logic assumes a distant actor has same live AI/3D state as a High-process actor.

## Diagnostic rules

1. Record whether actor is loaded, 3D-loaded and which process level it is in.
2. Persistent/unique/essential flags do not guarantee High Process.
3. Node/animation/UI effects often require loaded 3D.
4. Avoid global scans of Low-process actors.
5. Actor Limit Fix changes hard limits, not CPU cost per actor.
6. Distinguish logical package progress from physically simulated movement.
7. New process-level symptoms after crowd mods may be workload/engine-limit issues rather than record conflicts.

## Sources

- powerofthree Papyrus Extender GetActorsByProcessingLevel documentation
- CommonLibSSE reverse-engineered AIProcess, HighProcessData and ProcessLists structures
- Creation Kit actor/package documentation

## Provenance note

Exact promotion/demotion heuristics are reverse-engineered and can vary by runtime/context. Treat tier names and exposed structure semantics as reliable; avoid inventing exact distance cutoffs without runtime-specific evidence.
