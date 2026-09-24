# Skyrim Modding Knowledge — Actor Values, Perks, Magic, Combat, Equipment, and Crafting Records

Imported: 2026-09-24
Status: sourced encyclopedia pass 4

This module records gameplay-data systems that are commonly edited together but have distinct engine semantics.

## Actor values

### Actor Value / AV
Named numeric game statistic exposed by the engine, such as Health, Magicka, Stamina, skills, resistances, movement-related values and many hidden/internal values.

### Base actor value
Underlying actor statistic before temporary modifiers.

### Current actor value
Effective current value after damage/restoration/modifiers.

### ActorValueInfo / AVIF
Record describing metadata for an actor value, including display/skill-related behavior where applicable.

### GetActorValue
Papyrus/condition-style query returning current actor-value state.

### GetBaseActorValue
Query returning actor's underlying base value.

### ModActorValue
Relative actor-value modification.

### ForceActorValue
Set-style actor-value operation that changes effective/base offset relationships differently from ordinary damage/restore operations; it should not be used interchangeably without understanding persistence.

### DamageActorValue
Reduce an actor value through damage semantics.

### RestoreActorValue
Restore previously damaged value.

### Peak Value Modifier
MagicEffect archetype that temporarily modifies a value while tracking the highest applicable magnitude behavior.

### Value Modifier
MagicEffect archetype that modifies an associated actor value according to effect flags/duration semantics.

### Actor-value persistence
Some AV changes can become saved actor/reference state. Scripted permanent AV modification should therefore be treated as save-persistent gameplay state.

## Magic-effect engine semantics

### MagicEffect / MGEF
Functional core of spell/enchantment/potion/scroll/ability/shout effects.

### Effect archetype
Native code behavior selected by a MagicEffect. Scripted code runs in addition to, not instead of, the archetype.

### Associated item
Form or actor value supplied to archetypes that require an extra parameter.

### Hostile
MagicEffect flag causing the effect to be treated as hostile/attack behavior. Creation Kit documentation notes only Hostile effects are resistible.

### Detrimental
Flag causing applicable actor-value effect magnitude to operate as negative/damage semantics.

### Recover
Flag causing applicable value-modifier effects to restore prior state when the effect ends rather than leaving cumulative change.

### Detrimental vs Hostile
Separate flags. An effect can be harmful in gameplay logic without both flags having identical meaning.

### Dispel with keywords
MagicEffect relationship allowing effects to be identified/dispelled through keyword matching.

### Casting type
Concentration, fire-and-forget, or other engine-supported casting lifecycle.

### Delivery
How a spell reaches its target: self, contact/touch, aimed/target actor/location variants as supported.

### Taper duration
Post-main-duration decay period supported by applicable MagicEffects.

### Taper weight
Coefficient affecting taper magnitude curve.

### Taper curve
Exponent/curve parameter controlling how effect magnitude decays during taper.

### Resistance
Actor value/keyword/engine calculation used to reduce or resist applicable hostile effects.

### Dual casting
Spell-casting behavior combining both hands and potentially applying perk/magnitude/cost modifiers.

### Costliest effect
Effect entry used by the engine for spell school/cost/display logic in many cases.

## Spells and effects

### Spell / SPEL
Form containing effect items and casting/type/equipment data.

### Ability
Spell type usually applied persistently without manual casting.

### Disease
Spell/effect category used for disease mechanics.

### Power
Spell type used through powers interface with frequency/use restrictions.

### Lesser Power
Power type with less restrictive usage semantics.

### Constant Effect
Effect that remains active while its source ability/equipment condition remains.

### Effect item
Entry referencing MGEF with magnitude, duration, area and condition data.

### Effect-item conditions
Conditions evaluated for the individual effect entry rather than the whole parent spell/enchantment.

### Enchantment / ENCH
Form containing effects applied through weapon/armor enchanting systems.

### Base enchantment
Parent/template enchantment relationship used by learned/player-created enchantment systems.

### Enchantment amount
Charge/cost/power-related value interpreted according to weapon/armor enchantment semantics.

### Weapon enchantment
Enchantment consumed through charge during weapon hits/attacks.

### Armor enchantment
Typically constant effect applied while equipped.

## Perks

### Perk / PERK
Record containing conditions and perk entries that alter actor/game behavior.

### Perk rank
Rank/index structure supporting multiple levels of a perk.

### Perk entry
Individual effect within a perk.

### Entry Point
Engine hook point where a perk can modify a calculation or event, such as damage, cost, detection or other supported process.

### Entry Point Function
Operation applied at an entry point, such as set value, multiply value, add value or call function depending on entry type.

### Entry Point conditions
Conditions deciding whether that perk entry applies to the current actor/context/target.

### Ability perk entry
Perk entry that grants an ability spell.

### Quest perk entry
Perk entry invoking quest/fragment-like behavior for supported entry mechanisms.

### Perk owner
Actor to whom the perk belongs. Entry-point subject/target semantics can refer to owner, target, weapon, spell or other contextual data.

### Hidden perk
Perk not exposed in normal perk UI but used internally by gameplay systems.

### Perk tree
Skill-tree node/connection representation plus associated PERK records.

### Skill tree position
AVIF/perk-node graphical placement distinct from the PERK record's functional logic.

## Combat

### CombatStyle / CSTY
Record controlling AI combat preferences such as attack/block/bash/ranged/magic behavior, movement and tactical weighting.

### Combat style
Actor's assigned combat-behavior parameter set.

### Offensive multiplier
Combat-style weighting affecting tendency to attack.

### Defensive multiplier
Weighting affecting defensive action.

### Bash multiplier
AI tendency to bash under applicable combat state.

### Power-attack multiplier
AI tendency toward power attacks.

### Ranged preference
AI weighting for maintaining/using ranged engagement.

### Dueling/circle behavior
Movement/tactical parameters controlling spacing and circling.

### Combat AI
Native decision system combining actor data, packages, combat style, available equipment/spells, navmesh and target state.

### Detection
Native stealth/perception calculation using light, movement, sound, skill, distance and perk/effect modifiers.

### Aggression
Actor AI data controlling when actor initiates combat.

### Confidence
Actor AI data controlling when it flees/continues fighting.

### Assistance
Actor AI data controlling whom the actor helps in combat.

### Morality
Actor AI setting limiting willingness to perform criminal/immoral actions under AI/package commands.

## Weapons and armor

### Weapon / WEAP
Weapon base form containing damage, speed, reach, animation/equip type, keywords, models, sounds, critical and other data.

### Base damage
Record damage before actor/perk/tempering/enchantment/combat modifiers.

### Speed
Weapon attack-speed parameter; actual animation timing also matters.

### Reach
Weapon engagement/range parameter distinct from visible mesh length.

### Stagger
Weapon stagger parameter influencing impact response.

### EquipType
Form defining how an item/spell occupies actor hands/equipment slots.

### Keyword classification
Weapon material/type/staff/etc. tags used by perks, recipes, distributors and conditions.

### Critical data
Weapon fields controlling critical chance/damage/effect behavior.

### Armor / ARMO
Inventory/equipment record defining value, rating, slots, keywords and linked ArmorAddons.

### ArmorAddon / ARMA
Renderable race/body model relationship used by ARMO equipment.

### Biped object slot
Numeric equipment/body slot indicating which body regions an armor occupies/hides.

### ARMO slot mask
Slots claimed by the armor item.

### ARMA slot mask
Slots associated with the rendered ArmorAddon. ARMO/ARMA masks should be compatible.

### Armor rating
Base armor defense before perks/tempering/actor factors.

### Weight class
Heavy/light/clothing classification through record fields/keywords as applicable.

### Alternate texture
Record-level texture-set substitution allowing one NIF material/shape to use different textures without duplicating the whole mesh.

### TextureSet / TXST
Record listing texture paths used for model material replacement.

### Model data
Record field pointing to NIF path and associated alternate-texture substitutions.

## Crafting

### Constructible Object / COBJ
Crafting recipe record describing created object, required components, station keyword and conditions.

### Created Object
Output form produced by a recipe.

### Created Object Count
Quantity produced.

### Workbench Keyword
Keyword selecting which crafting station/menu exposes the recipe.

### Component
Required input form/count.

### Recipe condition
Condition controlling whether recipe appears/is usable.

### Tempering recipe
COBJ that improves a weapon/armor rather than creates a fresh item, using appropriate crafting-station keyword and output semantics.

### Smithing perk condition
Recipe condition requiring a perk/skill/material relationship.

### Crafting category keyword
Keyword controlling grouping/category display in supported crafting menus.

### Breakdown recipe
Recipe converting an item into component materials.

## Items and leveled distribution

### LeveledItem / LVLI
List that selects item entries according to level/chance/count/list flags.

### Calculate from all levels <= player
Leveled-list behavior allowing selection from all qualifying lower-level entries instead of only closest level band.

### Use All
Leveled-list flag causing all eligible entries to be included instead of choosing one.

### Chance None
Probability that the leveled list returns no item/actor.

### Global chance
GlobalVariable optionally controlling Chance None.

### Nested leveled list
Leveled-list entry pointing to another leveled list.

### Outfit / OTFT
List of items equipped/given through actor outfit system.

### Default Outfit
NPC outfit used in normal state.

### Sleep Outfit
Alternate outfit for sleep behavior where used.

### DeathItem
Leveled/list item data used to populate actor corpse/death inventory.

## Compatibility/design rules

1. Native MagicEffect archetype behavior must be understood before adding Papyrus scripts to “fix” it.
2. Hostile, Detrimental and Recover are separate effect semantics.
3. Permanent actor-value script mutations can bake into saves; prefer reversible effects/perks where appropriate.
4. Perk Entry Points modify engine calculations and are not equivalent to ordinary spells.
5. Combat style changes cannot fix inaccessible navmesh or unavailable attacks.
6. ARMO and ARMA slot/race/model data must be inspected together for equipment rendering bugs.
7. Weapon visible reach and WEAP reach can disagree; gameplay uses engine data, not merely mesh length.
8. Crafting visibility bugs often come from workbench keyword/conditions, not missing COBJ output.
9. Leveled-list conflicts require semantic merging of flags/chance/nested entries, not blind concatenation.
10. Runtime distributors can avoid direct NPC/list overrides when their semantics match the desired change.

## Sources

- Creation Kit Wiki Magic Effect: https://ck.uesp.net/wiki/Magic_Effect
- Creation Kit Wiki scripting/game-form reference: https://ck.uesp.net/wiki/Category:Scripting
- Creation Kit Wiki crafting categories: https://ck.uesp.net/wiki/Customizing_Crafting_Categories
- Tome of xEdit record inspection: https://tes5edit.github.io/docs/
