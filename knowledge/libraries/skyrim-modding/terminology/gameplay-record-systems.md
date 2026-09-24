# Skyrim Modding Terminology — Gameplay Record Systems

Imported: 2026-09-24
Status: sourced deep-ingestion pass 6

This module fills out the gameplay-data layer used by the Creation Kit, xEdit, Papyrus and runtime patchers.

## Actors and actor data

### Actor / ACHR
A placed actor reference in the world.

### ActorBase / NPC_
Base NPC/creature definition from which placed or spawned actors derive identity, stats, factions, outfits, AI and appearance data.

### Template actor
NPC_ record used as a source for selected inherited traits/data through actor template flags.

### Template flag
Controls which categories of NPC data are inherited from a template rather than defined locally.

### Unique actor
ActorBase marked as unique, normally representing one persistent named individual rather than an interchangeable population entry.

### Essential
Actor protection state preventing ordinary death and instead forcing bleedout/other engine behavior.

### Protected
Actor state where ordinary NPCs generally cannot deliver the final killing blow, but the player can.

### ActorValue
Named numeric game statistic such as Health, Magicka, Stamina, skills, resistances, movement-related values and many internal state variables.

### ActorValueInfo
Engine/SKSE-exposed form-like metadata for an actor value.

### Base actor value
Underlying actor-value level before transient modifiers.

### Current actor value
Effective actor value after damage/restoration/modifiers.

### Permanent modifier
Persistent modifier layer applied to an actor value.

### Temporary modifier
Transient modifier layer applied while an effect/state is active.

### Damage modifier
Actor-value change representing damage/depletion rather than base/permanent configuration.

### Class
Actor template describing skill weighting and related NPC progression characteristics.

### CombatStyle
Record controlling combat decision weights/preferences such as melee/ranged behavior, blocking, bash and positioning tendencies.

### Aggression
Actor AI setting describing conditions under which an actor initiates hostility/combat.

### Confidence
Actor AI setting influencing willingness to continue/flee from combat.

### Assistance
AI setting governing whom the actor will help in combat.

### Morality
AI setting used by crime/behavior decisions.

### Relationship
Pairwise relationship between actors represented by AssociationType/rank-related data and used by conditions/dialogue/AI.

### AssociationType
Defines semantic relationship category between references/actors.

## Inventory and equipment

### Inventory item
Base form currently held by an ObjectReference/Actor.

### ExtraData
Runtime per-instance metadata attached to references/inventory stacks, including enchantment, health, ownership, count and many engine-specific states.

### ExtraDataList
Native container for per-instance extra-data entries.

### Equipped item
Inventory instance currently equipped by an actor.

### EquipSlot
Form defining an equipment slot relationship used by spells/weapons and other equippable forms.

### Biped slot
Numbered body/equipment regions used primarily by armor/headparts and corresponding NIF partitions.

### Outfit
Predefined item set assigned to NPCs for default/sleep/death/etc. contexts.

### Default outfit
ActorBase outfit used for ordinary clothing/equipment initialization.

### Sleep outfit
Optional alternate outfit for sleep behavior.

### Death item
Leveled/item list used to add inventory when an actor dies.

### Container changes
Runtime inventory delta stored on a reference/save rather than rewriting the base Container record.

## Crafting

### ConstructibleObject / COBJ
Recipe form defining crafted output, quantity, workbench keyword and component requirements/conditions.

### Workbench keyword
Keyword identifying the crafting station/menu context in which a COBJ can appear.

### Component
Required ingredient/item entry consumed by a crafting recipe where applicable.

### Recipe condition
Condition restricting whether the recipe is visible/usable.

### Temper recipe
COBJ used to improve weapon/armor items at sharpening/grindstone/workbench stations.

### Crafting category
Menu category derived through hard-coded Game Settings, Default Objects and Keywords. CK documentation notes that category count/mapping is partly hard-coded.

### Default Object
Hard-coded engine slot pointing to a configurable form such as a keyword, sound, FormList or other well-known object.

### DefaultObjectManager
Engine/Papyrus access point for predefined default-object slots.

## Perks

### Perk / PERK
Gameplay record containing conditions and perk entries that modify engine behavior.

### Perk entry
One effect inside a perk, often using an engine-defined entry point or ability/quest relationship.

### Entry Point
Hard-coded engine hook where a perk can modify a calculation/action such as damage, cost, detection or other gameplay behavior.

### Perk entry function
Operation applied at an entry point, such as multiply/add/set values or choose behavior according to engine-supported functions.

### Perk condition
Predicate controlling whether the perk or a perk entry applies.

### Perk rank
Rank value allowing multiple stages/levels of a perk.

## Magic

### Magic item
General engine family including Spell, Enchantment, Ingredient/Potion-related effects and similar records that contain effect entries.

### EffectItem
Instance/configuration of a MagicEffect inside a parent magic item, including magnitude, area, duration, cost and conditions.

### MagicEffect archetype
Native implementation class for a magic effect, determining fundamental behavior independently of scripts.

### Resist value
ActorValue used by the magic system to reduce/resist an effect where configured.

### Detrimental
MagicEffect flag marking effect as harmful for engine/UI logic.

### Hostile
MagicEffect/spell hostility designation affecting crime/combat/reaction behavior.

### Dispel keyword
Keyword-based cancellation mechanism where one effect can remove other active effects carrying configured keywords.

### Casting type
Fire-and-forget, concentration or other engine casting behavior.

### Delivery type
How an effect is applied: self, aimed, target actor, target location/contact depending on record configuration.

### Projectile
Record controlling projectile flight/visual/impact behavior used by ranged spells/weapons.

### Explosion
Area-effect record spawned by projectiles/hazards/other gameplay systems.

### Hazard
Persistent area effect/visual/damage entity such as ground effects.

### ImpactDataSet
Mapping of impact materials/types to impact effects, sounds and decals.

## Leveled systems

### LeveledItem / LVLI
List selecting item entries according to player/encounter level and flags.

### LeveledActor / LVLN
List selecting actor bases or nested lists for spawning.

### LeveledSpell / LVSP
List selecting spells.

### Chance None
Leveled-list probability that no entry is selected.

### Calculate from all levels <= player
Leveled-list flag enabling candidate selection from all qualifying lower/equal levels rather than only the closest level band.

### Calculate for each item in count
Leveled-list flag causing each requested count selection to be rolled independently.

### Nested leveled list
Leveled list containing another leveled list as an entry.

### Encounter Zone
Record controlling level/minimum-level and reset/ownership-related behavior for locations/cells used by encounter scaling.

### Minimum encounter level
Lower bound enforced by an EncounterZone for relevant enemies/content.

## Keywords, locations and semantic tagging

### Keyword / KYWD
Named semantic tag referenced by conditions, records and frameworks.

### Location / LCTN
Hierarchical semantic area record used for quests, Story Manager, conditions, ownership, encounter data and location-based systems.

### Parent location
Location hierarchy relationship.

### LocationRefType / LCRT
Semantic role assigned to placed references inside locations, used by quests/Story Manager and lookup logic.

### Boss LocRefType
Location-reference role identifying boss/objective-related references where expected by location/quest systems.

### Map marker
Placed reference used for world/local map discovery/travel behavior.

### Keyword hierarchy
Convention where related keywords form semantic families through naming/framework usage; vanilla keywords themselves do not automatically imply arbitrary inheritance unless engine/framework behavior explicitly implements it.

## Books, words and shouts

### Book / BOOK
Readable/takeable record that may teach a spell/skill or contain text.

### Skill book
Book configured to increase a skill once under vanilla book-reading behavior.

### Spell tome
Book configured to teach a spell.

### WordOfPower / WOOP
Record representing one dragon-language word.

### Shout / SHOU
Record tying WordOfPower entries to associated spells/recovery behavior.

## Diagnostic rules

1. Distinguish ActorBase/NPC_ data from placed Actor/ACHR state and save-side reference state.
2. Inventory stack ExtraData can explain why two copies of the same base item behave differently.
3. Armor appearance crosses ARMO, ARMA, race, biped slots, NIF partitions, skeleton and textures.
4. Perk effects can alter engine calculations without any Papyrus execution.
5. MagicEffect archetype behavior can be the root cause even when scripts are attached.
6. Crafting categories are partly hard-coded through Game Settings/Default Objects; adding a keyword does not create arbitrary new category infrastructure.
7. Encounter Zone behavior is distinct from leveled-list content.
8. Runtime distribution frameworks may modify these systems after xEdit-visible records load.

## Sources

- Creation Kit Wiki Customizing Crafting Categories: https://ck.uesp.net/wiki/Customizing_Crafting_Categories
- Creation Kit Wiki DefaultObjectManager Script: https://ck.uesp.net/wiki/DefaultObjectManager_Script
- Creation Kit Wiki Magic Effect: https://ck.uesp.net/wiki/Magic_Effect
- Creation Kit Wiki scripting/form object references: https://ck.uesp.net/wiki/Category:Scripting
- SKSE Script Objects index: https://ck.uesp.net/wiki/Category:SKSE_Script_Objects
- Tome of xEdit: https://tes5edit.github.io/docs/
