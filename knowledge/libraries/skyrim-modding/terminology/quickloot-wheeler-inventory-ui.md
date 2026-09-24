# Skyrim Modding Terminology — QuickLoot, Wheeler, Favorites, and Inventory Interaction UI

Imported: 2026-09-24
Status: sourced deep-ingestion pass 18

## QuickLoot

### QuickLoot
Fallout-style loot interface concept showing contents of targeted container/corpse without opening full ContainerMenu.

### QuickLoot EE
Modern native QuickLoot lineage on Skyrim SE/AE providing real-time container popup behavior.

### QuickLoot IE
Current maintained/forked QuickLoot EE lineage adding bug fixes, features and native compatibility integrations.

### Loot menu
Popup UI showing current crosshair container contents.

### Crosshair container
Reference currently targeted and eligible for QuickLoot display.

### Lootable reference
Container/corpse/reference whose inventory can be exposed by QuickLoot.

### Item list
Runtime inventory entries displayed by QuickLoot.

### Take
Move one selected item from container to player.

### Take all
Transfer all eligible items.

### Steal state
QuickLoot must respect ownership/crime metadata when target/item is owned.

### Harvest
Flora/activator interaction that may be represented through loot-like UI only with explicit integration.

### Corpse loot
Actor corpse inventory displayed after death.

### Container mutation
QuickLoot list must refresh when scripts/runtime distributors add/remove items.

### QuickLoot icon integration
QuickLoot IE can consume I4 metadata so custom item icons appear in loot popup.

### QuickLoot PapyrusUtil dependency
Current QuickLoot IE requires PapyrusUtil for parts of its state/integration.

### BEES dependency
Current QuickLoot IE documents Backported Extended ESL Support for runtimes older than 1.6.1130 because of modern plugin/header requirements.

### Native compatibility integration
QuickLoot IE incorporates support for mods previously requiring explicit compatibility patches.

### Loot menu conflict
Two mods attempt to display/replace container interaction UI simultaneously.

### QuickLoot + Skyrim Souls
Unpaused-menu mods change time flow while loot UI is open, requiring integration/behavior checks.

## Wheeler

### Wheeler
Native quick-action wheel framework by dTry for weapons, spells, shouts, consumables and other inventory/magic actions.

### Wheel
Top-level radial selection menu.

### Slot
Position on wheel containing one or multiple selectable items.

### Item stack in slot
Several actions/items can cycle within one wheel slot.

### Wheel hierarchy
Wheels -> slots -> items.

### Edit mode
Wheeler state used inside inventory/magic menus to add/remove/reorganize entries.

### Gameplay mode
Wheel opened while moving/fighting for quick selection/use.

### Hold-to-open
Menu stays visible while hotkey held.

### Toggle-open
Short press toggles menu persistently.

### Slow-time factor
Game timescale/slowdown applied while Wheeler is open.

### Item equip
Selecting weapon/armor/spell/shout through Wheeler invokes same underlying equip/use systems rather than creating duplicate item state.

### Wheeler preset
INI/config describing style/control layout.

### dMenu
Native configuration/menu framework used by Wheeler and related modern mods.

### Emergency wheel reset
Recovery option clearing corrupt/invalid wheel contents if a stored item entry crashes/breaks menu.

### QuickLoot integration
Wheeler can cooperate with QuickLoot/inventory selection flows in supported versions.

### Wheeler Refined
2026 stability/feature overhaul built on dTry's Wheeler, addressing CTDs, controller behavior and adding modern QoL.

### Ammo wheel
Wheeler Refined feature specializing ammunition selection.

### Direct shout
Selecting/using shout from wheel without ordinary menu navigation.

### Release to Use
Input mode triggering selection/action when wheel hotkey is released.

### Favorites Wheeler
Variant synchronizing wheel content from vanilla favorites.

### Favorites Wheeler Advanced
2026 standalone favorites-wheel/compact-inventory system with configurable categories and optional Wheeler Refined integration.

## Favorites system

### Favorite
Inventory/magic item flagged for vanilla favorites menu.

### FavoritesMenu
Vanilla/SkyUI menu listing favorite forms.

### Favorite sync
Framework automatically mirrors favorites additions/removals into wheel.

### Form instance issue
Favorite base form may have multiple inventory instances with different enchantment/temper ExtraData; UI must select correct instance semantics.

### Transform-mode favorites
Vampire Lord/other transformation can expose different power/spell set and wheel/favorites implementation may rebuild accordingly.

## UI/input interoperability

### Menu focus
Which UI currently owns keyboard/mouse/controller input.

### Typing Mode
Utility/integration used by modern native menus to avoid action hotkeys firing while text input is active.

### Menu conflict
Two native menus use same hotkey/input and open/consume events simultaneously.

### Gamepad binding collision
Controller has limited buttons; modifier-key/controlmap combinations often used to multiplex DAK/Wheeler/dodge/power attack/etc.

### Item-card integration
UI frameworks can display I4/Description Framework metadata inside quick/favorites menus.

### Time-paused menu
UI sets timescale/pause flag.

### Unpaused menu
World simulation continues while UI open.

## Diagnostic rules

1. QuickLoot UI state comes from runtime container inventory, not just CONT base record.
2. Ownership/crime must be tested through QuickLoot, not assumed from full ContainerMenu behavior.
3. If one specific item crashes Wheeler/QuickLoot, inspect that item's form/ExtraData/icon/description/enchantment, not only menu DLL.
4. Stored wheel entries can outlive removed plugins; use reset/rebuild before blaming current assets.
5. Separate input focus conflicts from UI rendering conflicts.
6. I4/Description Framework issues can surface differently across InventoryMenu, FavoritesMenu, AlchemyMenu and QuickLoot.
7. Exact runtime DLL version matters for QuickLoot/Wheeler/dMenu stacks.

## Sources

- QuickLoot IE current Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/120075
- Wheeler: https://www.nexusmods.com/skyrimspecialedition/mods/97345
- Wheeler Refined: https://www.nexusmods.com/skyrimspecialedition/mods/167380
- Favorites Wheeler Advanced: https://www.nexusmods.com/skyrimspecialedition/mods/176861
- I4: https://www.nexusmods.com/skyrimspecialedition/mods/85702

## Dated snapshot

QuickLoot IE 3.4.1 was current as of 2026-09-24 (updated 2026-04-07). Wheeler Refined 1.3.3.0 was updated 2026-04-29. Preserve exact native UI stack versions and control bindings during troubleshooting.
