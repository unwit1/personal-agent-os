# Skyrim Modding Terminology — Hearthfire Building, Workshops, and Constructible Homes

Imported: 2026-09-24
Status: sourced deep-ingestion pass 20

## Hearthfire construction architecture

### BYOH
Bethesda internal prefix commonly used for Hearthfire "Build Your Own Home" content.

### Hearthfire workshop
Crafting-station-driven construction system enabling/removing preplaced house/reference sets rather than dynamically modeling arbitrary geometry.

### Carpenter's Workbench
Furniture/crafting station used to construct house structures/furnishings.

### Drafting Table
Furniture used to choose house wings/layout plans.

### Building material
Crafting inputs such as sawn logs, clay, quarried stone, iron fittings, locks, nails and hinges.

### House plan
Quest/global/state representing selected construction option.

### Foundation stage
Early construction stage enabling foundation references.

### Wall stage
Construction stage enabling walls/structural set.

### Roof stage
Construction stage enabling roof/completion set.

### Furnishing
Interior object group enabled after construction recipe purchase/use.

### Building recipe
COBJ consumed at Hearthfire workbench to trigger construction stage/reference enabling.

### Recipe output token
Crafting recipe may create/remove an internal dummy/item while script handles actual world-state construction.

### Enable parent construction
Large groups of house/furniture references use enable-parent relationships so one marker/state toggles entire object set.

### Construction marker
Hidden reference representing one build state/room/furnishing group.

### Building quest
Quest/script holding property purchase/house construction globals and enabling stages.

### Workshop script
Papyrus attached to crafting output/workbench/reference that applies build changes after recipe completion.

## Hearthfire crafting categories

### BYOHHouseCraftingCategoryBuilding
Default keyword/category for HOUSE.

### BYOHHouseCraftingCategoryContainers
Category for containers.

### BYOHHouseCraftingCategoryFurniture
Category for furniture.

### BYOHHouseCraftingCategoryWeaponRacks
Category for weapon racks.

### BYOHHouseCraftingCategoryShelf
Category for shelves.

### BYOHHouseCraftingCategoryExterior
Category for exterior objects.

### BYOHHouseCraftingCategorySmithing
Category for building materials.

### Generic Craftable Keyword
Default Object/category slots used by Hearthfire to create special workbench menu categories.

### Hard-coded category slot
Crafting menu category mapping uses fixed Default Object/Game Setting pairs; Hearthfire reuses generic category slots.

## House wings

### Main Hall
Second-stage house expansion.

### East Wing
One selectable wing slot.

### North Wing
One selectable wing slot.

### West Wing
One selectable wing slot.

### Wing choice
Mutually exclusive room plan for one wing position.

### Armory
Possible wing/furnishing set.

### Kitchen
Possible wing/furnishing set.

### Library
Possible wing/furnishing set.

### Greenhouse
Possible wing/furnishing set.

### Enchanter's Tower
Possible wing.

### Alchemy Laboratory
Possible wing.

### Storage Room
Possible wing.

### Bedrooms
Possible wing.

### Trophy Room
Possible wing.

## Display/storage systems

### Weapon rack
Multi-reference trigger/activator/linked-ref system enabling weapon display.

### Plaque
Display system supporting one or more weapons/shield depending on scripts/markers.

### Mannequin
Actor-based display system storing/equipping armor.

### Bookshelf
Container/trigger/placement-marker system distributing books visually across shelf slots.

### Display case
Container/door/trigger combination for manual item display.

### Safe storage
Container whose contents do not respawn/reset away. Must verify actual container/cell reset configuration; "player home" alone is not proof.

### Respawning container
Container contents reset according to cell/encounter reset and should not be used for persistent player storage.

## Modding construction systems

### Buildable player home
Mod emulating Hearthfire pattern with recipes, enable parents and quest state.

### Upgrade purchase
Dialogue/gold transaction enables furniture/reference sets instead of workbench crafting.

### Modular construction
Individual components independently enabled through recipes.

### Destructive upgrade
New construction disables/replaces previous reference set.

### Construction persistence
Enabled states generally persist and CK cell reset does not reset reference enable state.

### Construction rollback
Explicit script process disabling built stages and restoring earlier state; ordinary cell reset will not undo house construction.

## Failure modes

### Recipe visible but build not appearing
COBJ succeeds but attached quest/script/global/enable-parent logic not firing.

### Built objects disappear
Wrong persistence/enable parent, source plugin disabled, or another mod replaces/removes refs; ordinary reset normally does not undo enable state.

### Duplicate furniture
Multiple construction paths enable overlapping furnishing groups.

### Weapon rack broken
Missing linked refs/triggers or enable-parent incorrectly attached to trigger.

### Bookshelf overflow
More books/incorrect container state than visual slots/script expects.

### Safe-storage loss
Modder used respawning/resetting container.

### House conflict
Two mods edit same Hearthfire cell/reference/navmesh/enable groups.

## Diagnostic rules

1. Hearthfire construction is primarily preplaced reference enabling, not runtime mesh creation.
2. Recipe COBJ, construction quest/script and enable parent must all be traced.
3. Enable state persists through ordinary cell reset; do not rely on reset to undo construction.
4. Copy complete weapon-rack/bookshelf/mannequin linked systems, not only visible mesh.
5. Use non-respawning containers for player storage and test reset interval.
6. Wing choices are mutually exclusive state; patching must preserve quest/global logic.
7. Hearthfire category keywords reuse hard-coded generic crafting category slots.

## Sources

- Creation Kit Wiki Customizing Crafting Categories: https://ck.uesp.net/wiki/Customizing_Crafting_Categories
- Creation Kit Wiki weapon rack script dissection: https://ck.uesp.net/wiki/Dissecting_the_Scripts_for_Weapon_Racks
- Creation Kit Wiki Creating a Mannequin: https://ck.uesp.net/wiki/Creating_a_Mannequin
- Creation Kit Wiki Cell Reset: https://ck.uesp.net/wiki/Cell_Reset
