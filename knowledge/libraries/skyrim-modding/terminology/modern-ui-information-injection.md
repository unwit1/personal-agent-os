# Skyrim Modding Terminology — Modern UI Information Injection and Crafting Categories

Imported: 2026-09-24
Status: sourced deep-ingestion pass 16

## Inventory Interface Information Injector / I4

### I4
**Expansion:** Inventory Interface Information Injector. SKSE/SkyUI framework that injects item information such as custom inventory/favorites icons without requiring each addon to directly overwrite core SkyUI SWF files.

### Information injection
Runtime addition of metadata consumed by interface code rather than baking every display customization into one replacement SWF.

### Custom inventory icon
Icon identifier/style selected according to item type, keywords or framework configuration.

### Item classification
Mapping one form to a semantic UI category/icon using type, keywords and other runtime-accessible properties.

### Icon config
Framework configuration assigning an icon/colour/category according to filters.

### Scaleform API
I4 1.1+ interface exposing injected information to SWF/Scaleform consumers.

### SWF-independent addon
Addon that supplies I4 config/resources but does not need to overwrite InventoryMenu/Favorites SWF itself.

### Interface coexistence
I4's architectural goal of allowing multiple item-information addons to coexist with independently installed interface replacements.

### Runtime-generated keyword support
Current I4 versions can integrate with runtime keyword systems such as KID/related ecosystems where support is implemented.

### MergeMapper support
Current I4 metadata can account for plugin merge remapping so form identities survive merged-plugin workflows.

### SkyrimVRESL support
Current I4 line includes compatibility support for VR/light-plugin identity tooling.

### Alchemy-menu keyword gap
Historical I4 limitation where ingredient/alchemy menu data did not expose keyword information for matching.

### I4 Alchemy Fix
Replacement DLL/fork extending I4 keyword matching into AlchemyMenu so ingredient icons can be categorized by keyword.

### I4 log
Primary evidence for parser/runtime errors and unsupported config when icon injection fails.

## Dynamic Inventory Icon Injector

### Dynamic Inventory Icon Injector
Newer 2026 SKSE framework inspired by I4 that injects dynamic **status** icons such as enchantability/temper/quest/status indicators.

### Status icon
UI symbol describing dynamic item state rather than fixed semantic category.

### canLearn
Condition determining whether an item's enchantment can currently be learned/disenchanted.

### soulSize
Condition based on SoulGem/item soul state.

### FormList condition
Dynamic item classification based on membership in a FormList.

### conditionPerk
Icon condition based on player/perk state.

### Icon replacement
Rule replacing one status icon with another when conditions match.

### Dynamic contents
Condition source evaluated against current/runtime FormList data rather than only plugin-load snapshot.

### Injector API
Native API allowing other SKSE plugins to contribute/query icon state.

## COCKS

### COCKS
**Expansion:** Constructible Object Custom Keyword System. SKSE/SkyUI framework replacing SkyUI's coarse hardcoded crafting categories with extensible keyword-driven categories.

### Constructible Object Menu
SkyUI crafting menu showing COBJ recipes.

### Hardcoded category
Vanilla/SkyUI category encoded by menu implementation rather than dynamically supplied by arbitrary mod keywords.

### Extensible crafting category
COCKS category defined through framework configuration/keywords.

### Crafting-category keyword
Keyword used by COCKS to categorize a recipe/output into a UI tab/group.

### Category config
Framework data describing category name/icon/order/keyword relationships.

### Crafting-station support
COCKS applies to vanilla and modded crafting stations/menu contexts where the framework can identify them.

### Category ordering
Configured ordering of custom category tabs.

### Translation string
Localized UI category/name entry referenced by Scaleform translation convention.

### Dollar-prefix lookup
SkyUI/Scaleform translation key displayed with leading `$` when translation resource is missing or lookup fails.

### COCKS NG
CommonLibSSE-NG port maintaining COCKS across SE/AE/GOG/VR runtime families and current 1.7.x builds.

### Runtime-generated keyword lookup
Modern COCKS NG changes include fixes for keyword identities created at runtime.

## Description Framework

### Description Framework
SKSE framework adding descriptions to supported item/form categories without every mod replacing interface assets or base display text.

### Item description
Additional descriptive text shown in supported UI contexts.

### Description rule
Config/data mapping a target form/category to description text.

### Description injection
Runtime/interface addition of text without changing the underlying item's ordinary name.

### Description precedence
Order in which multiple description sources/rules resolve; should be verified from current framework config semantics.

### Localized description
Description routed through translated/string resources where supported.

## UI semantic frameworks

### Object Categorization Framework / OCF
Semantic keyword/FormList framework that can feed UI injectors such as I4/COCKS with consistent object categories.

### Semantic UI stack
Pattern: KID/OCF classify forms -> I4/COCKS/Description Framework display those categories/descriptions -> SkyUI/other menu presents them.

### Runtime UI metadata
Information exists in memory/config rather than as xEdit-visible field on the underlying item.

### UI-only classification
Category/icon affects presentation without changing gameplay behavior.

### Gameplay keyword
Keyword also consumed by perks/conditions/scripts. Do not assume every UI keyword is semantically harmless unless framework defines it as presentation-only.

## Diagnostic rules

1. Separate menu SWF conflicts from metadata-injector rules.
2. If one menu shows icons but AlchemyMenu does not, inspect menu-specific data exposure/framework version.
3. Missing `$KEY` text usually indicates translation lookup/resource issue, not bad COBJ data.
4. I4/COCKS config can depend on runtime-generated keywords not visible as static KEYM records.
5. Current DLL/runtime compatibility still matters even when addons are config-only.
6. Interface injectors can stack safely only when they target compatible APIs/data; do not assume arbitrary SWF replacements are equivalent.
7. Validate status icons from current item instance state (enchantment/soul/etc.), not just base form.

## Sources

- I4 current Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/85702
- I4 Alchemy Fix: https://www.nexusmods.com/skyrimspecialedition/mods/141883
- Dynamic Inventory Icon Injector: https://www.nexusmods.com/skyrimspecialedition/mods/174136
- COCKS current Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/81409
- COCKS NG: https://www.nexusmods.com/skyrimspecialedition/mods/81731
- Description Framework upstream: https://github.com/Nightfallstorm/DescriptionFramework

## Dated snapshot

On 2026-09-24, I4 1.1.1 was current on Nexus (updated 2026-08-28), COCKS 1.2.0 was current (updated 2026-08-27), and the COCKS NG port had a 2026-08-29 update for Skyrim 1.7.99+ support. Preserve exact framework build when diagnosing UI injection.
