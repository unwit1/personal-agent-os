# Skyrim Modding Terminology — Death, Bleedout, Ragdolls, Corpses, and Death Alternatives

Imported: 2026-09-24
Status: sourced deep-ingestion pass 18

## Vanilla actor death states

### Alive
Actor can perform ordinary AI/combat actions.

### Dying
Transition state after lethal event before full dead-state completion.

### Dead
Actor death state recognized by engine/Papyrus.

### OnDying
Papyrus event delivered as actor enters dying state.

### OnDeath
Papyrus event delivered after actor death semantics trigger.

### Killer
Actor/reference credited with lethal damage.

### Kill
Papyrus/native request to kill actor.

### KillEssential
Special operation bypassing ordinary essential protection.

### Essential
Actor normally cannot die from ordinary damage and enters bleedout.

### Protected
Actor normally survives NPC-inflicted lethal damage but can be killed by player/special sources.

### Bleedout
Incapacitated actor state used by essential/protected actors/followers and some death-alternative systems.

### Bleedout percentage
Actor/game parameter controlling health threshold/behavior for bleedout in contexts using it.

### GetNoBleedoutRecovery
Actor flag/state preventing automatic recovery.

### SetNoBleedoutRecovery
Papyrus method altering recovery behavior.

### Essential bleedout
Vanilla behavior where essential actor kneels/collapses then recovers.

### Player bleedout
Not ordinary vanilla player-death resolution; frameworks can intercept lethal conditions and place player into a defeat/bleedout-like custom state.

## Ragdoll

### Ragdoll
Havok-driven body simulation used for dead/staggered/knocked actors.

### Ragdoll state
Actor animation/physics state where skeleton bones are primarily physically simulated.

### Ragdoll impulse
Force applied to body/bones on hit/death.

### GetUp
Transition from ragdoll/knockdown back into animation/AI.

### Get-up animation
Animation selected after knockdown/bleedout.

### Ragdoll constraint
Skeleton physics joint limiting relative bone motion.

### Ragdoll collision
Physical collision shapes associated with actor skeleton.

### Animation-to-ragdoll transition
Blend from behavior animation pose into physics.

### Ragdoll-to-animation transition
Engine aligns physical body with get-up animation/actor transform.

### Ragdoll desync
Actor logical position differs from visual/physics body's apparent location.

### Corpsedrag/object move
External mods moving ragdoll/reference can alter saved Havok/reference state.

## Corpse lifecycle

### Corpse
Dead Actor reference remaining in world with inventory/3D/state.

### Dead-body cleanup
Quest/engine cleanup processes eventually disabling/deleting/moving eligible dead actors.

### DeadBodyCleanupCell
Vanilla cleanup holding cell used by game systems for some removed corpses.

### Corpse inventory
Runtime Actor inventory accessible after death.

### DeathItem
ActorBase leveled/item list added when actor dies.

### RemoveAllItems
Script/API can move corpse inventory before cleanup.

### Persistent corpse
Quest/persistent reference not cleaned like generic temporary corpse.

### Dead count
Game/Papyrus counters/statistics tracking kills/deaths.

### Respawning actor
Generic encounter actor may be recreated/reset when cell respawns, not resurrect the same persistent narrative identity.

### Resurrect
Console/native function restoring dead actor state, often unsafe as a generic quest repair because scripts/aliases/inventory can remain altered.

### Corpse reset
Cell reset may restore respawning actors according to encounter rules; unique/persistent actors follow different logic.

### Ash pile
Secondary reference created by disintegration effects for corpse representation/cleanup.

### Disintegrate
MagicEffect behavior replacing/removing corpse with ash pile.

### Reanimate
Necromancy state temporarily controlling a dead actor through reanimation effect.

### Reanimated corpse
Dead actor temporarily driven by magic/AI and potentially disintegrated on effect end depending on archetype.

## Death alternative frameworks

### Death alternative
System intercepting/avoiding ordinary reload-on-player-death and substituting defeat/rescue/penalty/respawn behavior.

### Defeat state
Framework state representing actor/player incapacitated but not fully vanilla-dead.

### Acheron
SKSE-driven combat death-alternative framework using defeat state for player/NPC under configured lethal/defeat conditions.

### Acheron NG
2026 SE/VR compatibility fork/extension using CommonLibVR/alternate UI integrations.

### Rescue event
Framework outcome after defeat moving/restoring actor, triggering scenario or handing off to addon.

### Defeat event
Framework API/event emitted so addons can provide consequences.

### Death interception
Native/script hook preventing ordinary player death under eligible conditions.

### Lethal bypass
Cases such as killmove/execution/non-combat damage intentionally allowed to cause true death despite death-alternative framework.

### Injury alternative
Framework prevents death but adds persistent/temporary injury debuffs.

### Lives-based death prevention
Consumable/limited resource intercepts lethal event one or more times, then vanilla death returns.

### Respawn
Player is restored/moved after death/defeat rather than loading previous save.

### Checkpoint death
Respawn at a remembered location/state.

### Death loop
Player repeatedly re-enters lethal state immediately after rescue due to lingering damage-over-time, hazard or improperly cleared effects.

## Killmoves

### Killmove
Cinematic/execution animation that directly resolves lethal combat.

### Paired killmove
Synchronized attacker/victim animation with constrained positions.

### Decapitation
Killmove/death behavior removing head and applying decapitated state/assets.

### Killmove immunity
Framework/setting suppressing killmoves on player/NPC to preserve death-alternative interception.

### Execution bypass
Death-alternative documentation may explicitly allow killmoves to bypass defeat system.

## Save/quest implications

### Dead flag persistence
Death/reference state saved for persistent/unique actors.

### Quest alias death
Quest can react to alias/reference OnDeath and set stages; resurrecting actor does not undo quest progression.

### Death stage
Quest stage set by death event.

### Essential toggle after death
Changing essential/protected flag after actor already died cannot retroactively undo saved death/quest state.

### Death replacement compatibility
Multiple mods hooking player lethal damage/death events can compete; only one should own final death-state transition unless integration is explicit.

## Diagnostic rules

1. Distinguish bleedout, defeat, dying and dead—mods may use all four differently.
2. Resurrecting a quest actor does not rewind quest aliases/stages/death events.
3. Death-alternative frameworks can conflict invisibly at native hooks even with no plugin conflict.
4. Lingering DoT/hazard must be cleared or handled to avoid rescue/death loops.
5. Ragdoll visual position and logical reference position can diverge.
6. Corpse cleanup depends on persistence/quest/respawn status.
7. Killmoves/executions may intentionally bypass defeat systems; check framework policy before calling it a bug.

## Sources

- Acheron NG current Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/175217
- Death Alternative - Your Money or Your Life: https://www.nexusmods.com/skyrimspecialedition/mods/13264
- Shades of Mortality: https://www.nexusmods.com/skyrimspecialedition/mods/136825
- Spark of Life: https://www.nexusmods.com/skyrimspecialedition/mods/169492
- CK scripting API/events: https://ck.uesp.net/wiki/Category:Scripting
