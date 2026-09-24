# Skyrim Modding Terminology — Flora, Harvesting, Planting, and Growable Crops

Imported: 2026-09-24
Status: sourced deep-ingestion pass 22

## Flora records

### Flora / FLOR
Harvestable world object whose activation yields an ingredient/item and can change harvested visual/state.

### Tree / TREE
Tree-form world object; may also represent some harvestable plant-like objects depending on content setup.

### Grass / GRAS
Procedurally rendered grass form distributed by landscape/region data; ordinary grass is not a harvestable ObjectReference.

### Ingredient / INGR
Alchemy ingredient yielded by many FLOR records.

### Harvest item
Form produced when Flora is activated.

### Harvest sound
Audio played on successful harvest.

### Harvested state
Reference state after Flora has been picked and before it respawns.

### Harvested model
Alternate appearance/visibility representing picked plant.

### Respawn
Cell reset returns harvestable flora to unharvested state in eligible respawning cells.

### Flora activation
Engine-managed harvest interaction distinct from generic Activator scripts.

### Flora yield
Number/type of items returned; mods can alter it via scripts/perks/runtime hooks.

## Plantable Hearthfire system

### Planter
Hearthfire furniture/soil-plot system allowing eligible ingredients/plants to be planted.

### Soil
Planting reference/activator accepting selected item.

### Plantable FormList
FormList defining which ingredients/plants are accepted by vanilla planter scripts.

### flPlanterPlantableItem
Common Hearthfire FormList used in growable-plant compatibility mods.

### Planting script
Papyrus managing selected crop, consuming seed/ingredient, enabling planted Flora and growth timer.

### Crop reference
Preplaced plant/flora references enabled according to planter choice.

### Growth stage
Time/state between planted seed and harvestable plant.

### Regrowth
After harvest, planter crop returns according to script/reset timing.

### Clear planter
Remove current crop assignment and return soil to empty state.

### Planting compatibility patch
Adds new ingredient/flora pair to plantable FormLists/scripts without replacing core Hearthfire system.

### Input-output mismatch
FormList/order relationship maps ingredient to wrong Flora output after another mod inserts entries inconsistently.

### Instant growth
Script replacement skipping ordinary growth delay while retaining planting/harvest logic.

## Runtime integration

### FLM plant rule
FormList Manipulator supports simplified `Plant = source|plant|filter` patterns for compatible plant systems.

### Plant collection
Runtime grouping of ingredients/flora according to keywords/forms.

### KID flora keyword
Keyword Item Distributor can classify FLOR/Ingredient forms for harvest/season/UI frameworks.

### Seasonal flora swap
Seasons of Skyrim swaps Flora forms/models according to season.

### Plantable Creation
Official Creation-added ingredient/flora adapted into Hearthfire plantable list.

### Indoor-only plant
Framework/config restricts a plant to interior planters.

### Outdoor-only plant
Restricts planting to exterior soil/appropriate environment.

## Trees and plant assets

### Flora mesh
NIF model referenced by FLOR.

### Tree mesh
NIF/tree form asset.

### Wind animation
Shader/tree behavior moving foliage.

### Leaf animation
Texture/mesh/shader movement.

### Seasonal mesh
Alternate plant asset for winter/spring/etc.

### PBR flora
Plant textures/materials authored for Community Shaders TruePBR/modern material stack.

### Billboard flora
Distant representation where eligible; trees participate in dedicated Tree LOD while ordinary small flora often does not receive distant LOD.

### Collisionless flora
Decorative plant mesh deliberately lacks collision to avoid navigation/player interference.

## Gameplay frameworks

### Harvest multiplier
Perk/script/native tweak increasing harvested item count.

### Green Thumb
Vanilla Alchemy perk affecting ingredient harvest yield.

### Ingredient harvest event
Item-added/activation event used by mods to grant XP/quests.

### Auto harvest
Framework automatically gathers nearby FLOR/containers without manual activation.

### Harvest animation
Animation mod delays/synchronizes acquisition with picking animation.

### Harvest prompt
Activation text/UI indicating ingredient/action.

### Plant respiration/season rule
Survival/season mod decides when Flora is available/grown.

## Common failures

### Plant gives wrong ingredient
FLOR harvest-item link or runtime patch wrong.

### Planter gives wrong crop
FormList/script index/mapping conflict.

### Can't plant mod ingredient
Missing plantable-list pairing.

### Plant never regrows
Planter script/cell reset/timer state stuck.

### Seasonal plant disappears
No valid seasonal replacement or season config excludes form.

### Harvested visual remains
Reset/alternate-state reference does not restore.

### No collision
May be intentional decorative flora behavior.

## Diagnostic rules

1. Distinguish procedural GRAS from harvestable FLOR.
2. Planting is a separate Hearthfire scripted system layered on top of Flora/Ingredient records.
3. Adding a new FLOR does not automatically make its Ingredient plantable.
4. FormList ordering/pairing matters in planter compatibility.
5. Established saves preserve planter/crop script state.
6. Seasonal runtime swaps can change plant appearance without changing original FLOR in xEdit.
7. Grass LOD and plant harvesting are unrelated systems despite both being vegetation.

## Sources

- FormList Manipulator plant support: https://github.com/MaskedRPGFan/FormList-Manipulator
- Skyrim Anniversary Growable Plants: https://www.nexusmods.com/skyrimspecialedition/mods/58880
- Hearthfire planter compatibility example: https://www.nexusmods.com/skyrimspecialedition/mods/158027
- Seasons of Skyrim: https://github.com/powerof3/SeasonsOfSkyrim
