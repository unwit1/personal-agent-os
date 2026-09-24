# Skyrim Modding Terminology — Multiplayer and Networking

Imported: 2026-09-24
Status: sourced deep-ingestion pass 9

## Skyrim Together Reborn / Tilted Online

### Skyrim Together Reborn / STR
Co-op multiplayer mod/framework synchronizing Skyrim gameplay across multiple clients.

### Tilted Online
Underlying multiplayer framework/codebase used by Skyrim Together Reborn lineage.

### Client
Player's Skyrim process connected to a multiplayer server.

### Server
Authoritative/coordinating network process managing multiplayer session data.

### Party
Group of connected players sharing synchronization/quest/gameplay session rules.

### Host / party leader
Client/player given special responsibility for quest/session progression according to framework rules.

### Session
Period of connected multiplayer gameplay.

### Replication
Sending state changes from one machine to others.

### Authority
Which machine/server is considered responsible for deciding a particular piece of synchronized state.

### Desync
Clients disagree about actor/world/quest/inventory or other state.

### Resync
Framework action restoring clients to a common state.

### Entity
Network-synchronized actor/object representation.

### Entity ID
Network identity separate from ordinary local process pointer and potentially separate from Skyrim FormID.

### Spawn
Creating/network-registering an entity/reference on clients.

### Ownership
Network authority/association determining which participant drives an entity/state.

### Position replication
Synchronizing actor/reference transform.

### Animation replication
Synchronizing animation events/state across clients.

### Inventory replication
Synchronizing item additions/removals/equipment.

### Quest synchronization
Coordinating quest stage/objective/state across party members. Particularly difficult because vanilla quests were authored for one player/save state.

### Dialogue synchronization
Handling conversation state when multiple players share NPC/quest interactions.

### World-state synchronization
Doors, containers, enemies, weather, time and other mutable world state exchanged between clients.

### Papyrus synchronization
Multiplayer handling of script-driven changes; local Papyrus execution can produce divergent outcomes if framework does not replicate relevant result.

### Native mod compatibility
SKSE/native mods can alter state only on one client unless their effects are deterministic/replicated appropriately.

### Determinism
Same input/state produces same result across clients. Randomized/local-time behavior can create desync.

### Server tick
Periodic server update cadence used to process/synchronize state.

### Latency
Network delay between state generation and receipt.

### Jitter
Variation in network latency.

### Packet
Unit of network data.

### Reliable message
Network message requiring ordered/guaranteed delivery semantics.

### Unreliable message
Lower-overhead message allowed to drop/reorder, appropriate for high-frequency state like transforms.

### Interpolation
Rendering remote actor motion smoothly between received states.

### Extrapolation
Predicting remote state beyond latest packet to hide latency.

## Mod compatibility implications

### Client-side-only mod
Mod affecting visuals/UI locally without changing authoritative gameplay state.

### Gameplay mod
Mod changing spells/perks/AI/records/scripts and potentially requiring every player to use matching setup.

### Load-order parity
Clients use same relevant plugins/order so FormID/data meaning is consistent.

### Asset parity
Clients share relevant meshes/animations/scripts/config so synchronized events look/behave consistently.

### Native-DLL parity
Clients run compatible native plugin versions when those plugins influence synchronized gameplay.

### Server-side mod
Modification applied to multiplayer server behavior rather than local Skyrim data.

### Multiplayer-safe
Mod whose changes do not meaningfully break synchronization under documented conditions. This is version/framework-specific, not a permanent label.

### Unsynchronized randomization
Runtime distribution/random systems choose different outcomes on each client and can cause divergent state.

### Local-only AI
AI mod changes NPC decisions on one client without network authority agreement.

### Save incompatibility
STR sessions still interact with Skyrim saves; multiplayer session state may make arbitrary single-player save manipulation unsafe.

## Version/platform scope

### Supported runtime
STR documentation currently scopes support to specific Steam Skyrim SE runtime generations. Do not infer GOG/VR support.

### Modlist parity requirement
All players should follow the same multiplayer-compatible mod setup where gameplay data matters.

### Unsupported Creation
Official/mod content not shared by all clients can produce FormID/state mismatches.

## Diagnostic rules

1. Determine whether a symptom is local game bug or network desync.
2. Reproduce with unmodded/minimal STR before blaming general Skyrim data.
3. Compare load order, runtime and native DLL versions across every client.
4. Separate client visual-only mods from mods that alter replicated gameplay.
5. Quest desync should be diagnosed against party-leader/quest-sync rules, not repaired by arbitrary setstage on each client.
6. Random runtime patchers can create divergent results unless outcomes are deterministic or replicated.
7. Multiplayer support claims are framework-version-specific and stricter than ordinary single-player compatibility.

## Sources

- Skyrim Together Reborn/Tilted Online project: https://github.com/tiltedphoques/TiltedEvolution
- Project wiki/FAQ source: https://github.com/tiltedphoques/gitbook-wiki
- Current FAQ documentation surfaced from the project's GitHub wiki.
