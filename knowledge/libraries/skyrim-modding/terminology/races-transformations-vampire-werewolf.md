# Skyrim Modding Terminology — Races, Transformations, Vampires, and Werewolves

Imported: 2026-09-24
Status: sourced deep-ingestion pass 11

## Race records

### Race / RACE
Record defining actor-race data including models, skeleton relationships, head/body data, movement/behavior, spells/abilities, keywords, skill/stat data and playable/child/other flags.

### Playable race
Race exposed for player character selection/usage.

### Actor race
Current Race assigned to actor.

### Original race
Race identity before temporary/scripted transformation.

### SetRace
Papyrus Actor function changing actor's race at runtime.

### Race switch
Runtime operation rebuilding actor race-dependent 3D/stats/animation behavior.

### OnRaceSwitchComplete
Papyrus event sent after actor race switch completes.

### Race compatibility
HeadParts, ArmorAddons, skeletons, behavior projects and animation assets may be restricted by race.

### Morph race
Race/head morph configuration controlling chargen face geometry.

### Armor race
ARMA race restrictions deciding which wearable model is valid.

### Skin
Race/NPC body armor/skin data used to render naked body.

### Skeleton path
Race model data selecting skeleton NIF.

### Behavior graph path
Race/actor animation graph relationship; creature races often use distinct projects.

### Race spell
Ability/spell automatically granted by race.

### Race keyword
Keyword used to classify race for conditions/frameworks.

## Transformations

### Transformation
Runtime switch changing race, abilities, equipment/player controls and quest/global state.

### Beast form
Werewolf-style transformation mode.

### SetBeastForm
Game/Papyrus function indicating beast-form state for engine/UI systems.

### Werewolf archetype
MagicEffect archetype capable of changing target race to specified race.

### Werewolf Feed archetype
MagicEffect archetype used in werewolf feeding mechanics.

### PlayerWerewolfQuest
Vanilla quest family coordinating werewolf transformation, feeding/perks/state.

### Werewolf race
Special race used while transformed.

### Transformation spell
Spell/magic effect triggering transformation logic.

### Revert form
Logic restoring original race/appearance/equipment after transformation.

### Transformation equipment stripping
Removal/unequip of equipment during race switch.

### Transformation inventory state
Weapons/armor may remain in inventory but unequipped/hidden while special race is active.

### Transformation camera
Special camera/state transition used during transformation.

### Transformation controls
Player control restrictions/enabling around transformation sequence.

### Transformation animation
Behavior/animation sequence expected by transformation scripts/quest.

### Transformation save state
Saving during/around transformation can preserve race/quest/effect state requiring careful migration/debugging.

## Vampirism

### Vampire state
Gameplay state represented through race variants, spells, factions, quests and globals rather than one single boolean.

### Vampire race
Race variant used for vampire player/NPC appearance/stat behavior.

### Vampire Lord
Special transformation with dedicated race, behavior, camera, spells/perk tree and quest scripts.

### Vampire Lord race
Transformed player race.

### PlayerVampireQuest
Vanilla quest coordinating player vampirism state/feeding/progression logic.

### VampireFeed
Gameplay/script event/action applying feeding changes.

### Vampire stage
Progression/hunger state controlling abilities/appearance/penalties depending on implementation.

### Cured vampirism
Quest/script transition clearing/replacing race/spells/faction state.

### RaceCompatibility
Framework/mod lineage historically used to make custom races compatible with vampire/werewolf transformations by coordinating expected race mappings.

### Custom race transformation patch
Patch registering/mapping custom race and its vampire/beast variants so transformations revert correctly.

## Transformation compatibility

### Custom race
Mod-added Race requiring compatible ArmorAddon/headpart/skeleton/transformation handling.

### Race alias mapping
Framework mapping original race to transformed/alternate race.

### Revert mapping
Mapping transformed race back to correct original/custom race.

### HeadPart carryover
Appearance/head data transition that may fail when custom race uses incompatible headpart types.

### Skeleton swap
Race transformation changes skeleton/model path; physics/equipment/camera mods may need to rebind nodes.

### BodyMorph rebind
RaceMenu/BodyMorph state may need rebuild/rebind after 3D/race switch.

### Equipment display refresh
IED/SDS and similar systems need to update displayed nodes after race/skeleton transformation.

### OAR race condition
Animation replacer may select different animation submods based on current transformed race.

### Creature behavior graph
Transformed race can switch actor into different behavior project, invalidating human animation assumptions.

### Native hook race cache
SKSE plugin may cache race/skeleton data and must respond correctly to race-switch events.

## Common failure modes

### Stuck transformed race
Revert script/quest/effect failed or save state preserved transformation state.

### Invisible body after transform
Race skin/ARMA/skeleton/head/body asset mismatch.

### Wrong head after revert
Race/headpart/FaceGen/RaceMenu state not rebuilt consistently.

### Animation T-pose after transform
New race expects behavior/skeleton/project missing or generated output lacks support.

### Physics stretch after transform
Old skeleton/physics nodes persist while new race skeleton differs.

### Lost custom race
Revert hard-coded to vanilla race instead of original custom race.

### Duplicate transformation effects
Two overhaul/frameworks manage same vampire/werewolf state.

## Diagnostic rules

1. Treat transformation as multi-layer state: race + quest + magic effects + spells + factions + equipment + animation + camera.
2. Never diagnose a stuck werewolf/vampire solely from current Race record.
3. For custom races, inspect both transform mapping and revert mapping.
4. Race switch can invalidate skeleton-node-dependent systems; force/rebuild appropriate runtime state rather than only re-equipping items.
5. Established saves can preserve transformation quest/script state.
6. Animation replacements conditioned on race may change immediately after transform even if behavior graph stays the same.
7. Native plugins should listen/respond to race/3D lifecycle rather than cache player nodes forever.

## Sources

- Creation Kit Wiki Magic Effect (Werewolf/Werewolf Feed archetypes): https://ck.uesp.net/wiki/Magic_Effect
- Creation Kit Wiki Papyrus API index (SetRace, SetBeastForm, OnRaceSwitchComplete): https://ck.uesp.net/wiki/Category:Scripting
- Creation Kit Wiki DefaultObjectManager (Werewolf Spell key): https://ck.uesp.net/wiki/DefaultObjectManager_Script
