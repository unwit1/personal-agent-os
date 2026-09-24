# Skyrim Modding Terminology — Mounts, Horses, and Dragon Riding

Imported: 2026-09-24
Status: sourced deep-ingestion pass 20

## Mount fundamentals

### Mount
Actor/reference used by another actor as a ridden vehicle, normally horse or dragon.

### Mounted actor
Rider currently attached to mount state.

### Mount keyword
Default Object key MNT2 references engine keyword used to classify mounts.

### GetPlayersLastRiddenHorse
Papyrus/Game API returning the player's last ridden horse.

### IsPlayersLastRiddenHorse
Condition/API testing horse identity.

### TetherToHorse
Actor/Papyrus behavior linking actor movement/state to horse.

### Dismount
Transition from mounted to ordinary actor locomotion.

### Mounted camera
Camera state used while riding.

### Mounted combat
Special animation/input/combat state used on horse.

### Mount furniture relationship
Riding internally shares interaction/state concepts with furniture/paired-animation systems.

### Horse base
NPC_/Race/Actor definitions for horse.

### Horse reference
Placed/persistent actor instance representing owned horse.

### Owned horse
Horse associated with player through ownership/quest/reference tracking.

### Stable
World location/package system housing available horses.

### Horse follow
Package/script behavior making owned horse travel/follow player across transitions.

### Horse teleport
Framework/script moves horse near player after fast travel/world transition.

### Horse death persistence
Horse reference can remain dead in save; replacing base data does not necessarily resurrect established horse.

## Dragon riding

### Dragon mount
Dragon Actor used in Dragonborn riding system.

### Dragon riding state
Special player/mount/camera/AI system introduced by Dragonborn.

### Allowed dragon-mount worldspace
Default-object/formlist logic restricting worldspaces where dragon riding is permitted.

### PCMD
Default Object key for "Player Can Mount Dragon Here" FormList.

### DMXL
Default Object key for "Dragon Mount No Land List."

### FMYS
Default Object key for flying-mount allowed spells.

### FMNS
Default Object key for flying-mount disallowed spells.

### FMFF
Default Object key for worldspaces where flying mount can use fast-flight behavior.

### Dragon landing marker
World marker used to coordinate landing location.

### DLZM
Default Object key for Dragon Land Zone Marker.

### Forced landing marker
Actor API/state selecting a desired landing location.

### Dragon flying state
Actor/native state representing taking off, hovering/flying/landing.

### AllowFlying
Actor function/state allowing dragon flight.

### ForceLanding
Native/scripted transition requesting dragon landing.

### Dragon target
Actor/reference selected for dragon combat while mounted.

### Bend Will riding
Quest/magic flow that transitions dragon into mountable player-controlled relationship.

## Mount/animation compatibility

### Mounted behavior graph
Behavior project/state for rider/mount interactions.

### Horse skeleton
Skeleton/animation set specific to horse race.

### Rider alignment
Paired animation transform aligning actor to saddle/mount.

### Mount node
Skeleton/interaction point representing rider attachment.

### Mounted weapon animation
Special weapon draw/attack animations while riding.

### Mount camera offset
Camera configuration specific to horseback/dragon state.

### Mount dismount animation
Paired transition placing rider back on terrain.

## Framework interactions

### Convenient Horses-style framework
Follower/mount-management mods can replace ownership, summoning, inventory and AI packages around horses.

### Horse whistle/summon
Script/native input teleporting/calling last owned horse.

### Mounted follower
Framework allows follower actors to acquire/use mounts.

### DAK horse interaction
Dynamic Activation Key can expose alternate horse action such as pet vs ride.

### IED mounted nodes
Equipment-display transforms can require mount-state conditions so sheathed gear does not clip horse/rider.

### OAR mounted condition
Animation replacer selects mount-specific clip according to mounted/state conditions.

## Common failure modes

### Horse missing after fast travel
Quest/reference ownership state, horse package or teleport integration failed.

### Wrong horse recalled
Framework's stored "last ridden"/owned reference differs from intended horse.

### Stuck mounted camera
Camera state did not transition cleanly after dismount/death/teleport.

### Floating rider
Mount skeleton/animation/root transform mismatch.

### Cannot mount dragon
Worldspace/formlist/quest/dragon state not eligible.

### Dragon refuses to land
Landing marker/world/navmesh/flying-state restrictions.

### Mount T-pose
Missing behavior/animation/skeleton output for mount/rider state.

## Diagnostic rules

1. Distinguish mount ActorBase, persistent horse reference and "last ridden horse" state.
2. Camera, behavior and rider transform are separate mounted systems.
3. Dragon riding has worldspace/spell/landing restrictions represented through Default Objects/forms.
4. Established saves can preserve dead/lost horse references.
5. Generic follower/mount frameworks can compete with custom horse quest scripts.
6. Test mount transitions through real mount/dismount rather than only MoveTo/console repositioning.
7. Custom mount race needs compatible skeleton, behaviors, furniture/interaction semantics and camera support.

## Sources

- Creation Kit Wiki DefaultObjectManager Script (mount/dragon keys): https://ck.uesp.net/wiki/DefaultObjectManager_Script
- Creation Kit Wiki Papyrus API index: https://ck.uesp.net/wiki/Category:Scripting
- Creation Kit Wiki Actor API references for flying/landing/mount-related functions
