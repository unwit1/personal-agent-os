# Skyrim Modding Terminology — Alchemy, Enchanting, Smithing, and Crafting

Imported: 2026-09-24
Status: sourced deep-ingestion pass 13

## Crafting foundation

### ConstructibleObject / COBJ
Recipe record defining created object, quantity, workbench keyword, components and conditions.

### Created Object
Form produced by recipe.

### Created Object Count
Quantity produced.

### Workbench Keyword
Keyword identifying crafting station/menu where recipe is eligible.

### Component
Input form/quantity consumed by recipe.

### Recipe condition
Condition controlling whether recipe appears/is usable.

### Crafting category
Menu category determined by Default Objects/keywords and hard-coded category mapping.

### Forge
Workbench keyword/default-object category for smithing new armor/weapons.

### Armor workbench
Station for tempering armor.

### Grindstone
Station for tempering weapons.

### Smelter
Station converting ores/scrap to ingots.

### Tanning rack
Station producing leather/leather strips.

### Cooking pot
Food crafting station.

## Smithing

### Smithing recipe
COBJ producing a weapon/armor/item at forge/crafting station.

### Temper recipe
COBJ improving existing weapon/armor.

### Tempering
Raising weapon damage/armor rating through item health/temper state.

### Item health percent
Per-instance ExtraData value representing temper condition/improvement.

### Tempering perk condition
Recipe condition checking Smithing perk/material perk.

### Material keyword
Armor/weapon keyword such as material family used by perks, recipes and distribution frameworks.

### Smithing perk
Perk enabling/improving specific material crafting/tempering.

### Improvement multiplier
Engine/perk result scaling temper benefit.

### Breakdown recipe
Mod-added reverse crafting converting item into components.

### Crafting injection
Adding new recipe without editing existing item where possible.

## Alchemy

### Ingredient / INGR
Consumable ingredient with up to four magic effects.

### Ingredient effect
MagicEffect association with magnitude/duration metadata.

### Known effect
Ingredient effect player has discovered.

### LearnEffect
Papyrus/SKSE API marking effect known.

### Potion / ALCH
Ingestible record representing potion, poison, food or other consumable.

### Potion
ALCH item with beneficial/neutral effects according to flags/archetypes.

### Poison
ALCH item flagged/treated as poison and applied to weapon.

### Food
ALCH item marked food with ingestible effects.

### Alchemy station
Workbench furniture opening alchemy crafting UI.

### Alchemy recipe
Unlike COBJ smithing recipes, vanilla alchemy dynamically combines ingredient effects according to shared effects and skill/perks.

### Shared ingredient effect
Two or more ingredients have same MagicEffect so alchemy can create resulting effect.

### Effect magnitude
Strength calculated from ingredient/base effect plus skill/perks.

### Effect duration
Duration calculation for created potion/poison.

### Costliest effect
Highest-valued effect often influences potion naming/value/classification.

### Alchemy value
Gold/XP relationship derived from resulting effect cost.

### Poison application
Equipped poison stored as weapon/inventory instance state.

## Enchanting

### Enchantment / ENCH
Record containing one or more effect items applied to armor/weapons.

### Base enchantment
Canonical enchantment from which item instance may derive.

### Object Effect
Bethesda form family/field linking item to enchantment.

### Weapon enchantment
Enchantment consuming charge on weapon use.

### Armor enchantment
Usually constant-effect enchantment while armor equipped.

### Enchantment charge
Per-instance remaining charge for weapon enchantment.

### Maximum charge
Item/enchantment capacity influencing number of uses.

### SoulGem
MiscObject-derived form with gem capacity/default soul metadata.

### Soul size
Creature/NPC soul category captured.

### Gem size
Maximum soul category accepted by SoulGem.

### Filled soul gem
SoulGem instance/base variant containing soul.

### Soul trap
Magic effect capturing killed target's soul into eligible empty soul gem.

### Enchanting station
Furniture opening enchanting menu.

### Learned enchantment
Player knows enchantment after disenchanting eligible item.

### Disenchant
Destroy item to learn base enchantment, subject to flags/known state.

### Disallow enchanting
Item/enchantment flags/keywords/conditions preventing disenchant or enchanting in specific contexts.

### Player-enchanted item
Runtime inventory instance with custom enchantment and ExtraData, not necessarily a new plugin form.

### ExtraEnchantment
Per-instance extra data representing enchantment on an inventory instance.

## Soul mechanics

### White soul
Non-humanoid soul category allowed in ordinary soul gems.

### Black soul
Humanoid soul category usually requiring black soul gem/Black Star behavior.

### Grand soul
Highest ordinary soul-size category.

### Soul trap ownership
Engine selects suitable gem from caster inventory according to soul/gem rules.

### Soul gem stacking
Identical base soul gems can have differing instance soul state, which affects inventory stack behavior/ExtraData.

## Crafting UI/category pitfalls

### Hard-coded category mapping
CK documents crafting categories as finite mappings between default-object slots/keywords and menu categories.

### Misc category fallback
Recipe/item whose keyword doesn't map to active crafting category can appear under Misc.

### Hidden recipe
Conditions prevent recipe from appearing.

### Missing station
Recipe has wrong workbench keyword for station being used.

### Duplicate recipe
Multiple COBJ records produce same output under same conditions.

### Runtime COBJ patch
SkyPatcher/Synthesis/etc. changes recipes after static plugins load.

## Diagnostic rules

1. Separate COBJ recipe visibility from output item's own record data.
2. Tempering is per-instance state; base WEAP/ARMO stats do not show every in-game tempered value.
3. Alchemy recipes are dynamic shared-effect calculations, not ordinary predefined COBJ records.
4. Player-created enchantments live partly in inventory ExtraData/runtime state.
5. Soul gem base form and contained soul are distinct concepts.
6. Crafting categories depend on hard-coded/default-object keyword mappings; arbitrary new keyword alone may fall to Misc.
7. If a recipe exists in xEdit but not UI, inspect workbench keyword and conditions first.

## Sources

- Creation Kit Wiki Customizing Crafting Categories: https://ck.uesp.net/wiki/Customizing_Crafting_Categories
- Creation Kit Wiki DefaultObjectManager: https://ck.uesp.net/wiki/DefaultObjectManager_Script
- Creation Kit Wiki SoulGem Script: https://ck.uesp.net/wiki/SoulGem_Script
- Creation Kit Wiki SKSE Script Objects: https://ck.uesp.net/wiki/Category:SKSE_Script_Objects
- Creation Kit Wiki Magic Effect: https://ck.uesp.net/wiki/Magic_Effect
