# Skyrim Modding Terminology — Seasons and Dynamic World Swapping

Imported: 2026-09-24
Status: sourced deep-ingestion pass 8

## Seasons of Skyrim

### Seasons of Skyrim
SKSE plugin/framework by powerofthree adding runtime seasonal world changes through model/form/landscape/LOD swapping and winter snow behavior.

### Season
Runtime state representing Winter, Spring, Summer or Autumn.

### Seasonal mode
Framework mode selecting season based on configured calendar/month mapping.

### Permanent season
Configuration locking the game to one season rather than calendar progression.

### Month-to-season map
Configuration mapping Skyrim months to seasonal states.

### Season override
Runtime/config state forcing a season independent of normal calendar selection.

### Seasonal worldspace
Worldspace enabled for season processing.

### Valid worldspaces
Configured set of worldspaces in which seasonal swaps are allowed.

### Form swap map
Mapping from original forms to season-specific replacement forms.

### WIN form
Naming/config convention used by Seasons of Skyrim's generated/default winter swapping workflow.

### Auto-generated winter formswap
Framework-generated mapping for winter variants that can be enabled/ignored or selectively skipped by form type.

### Seasonal static
Static base object swapped for a season-specific model/form.

### Seasonal tree
Tree base form swapped according to season.

### Seasonal flora
Flora base form swapped according to season.

### Seasonal grass
Grass/landscape-related seasonal swapping behavior.

### Seasonal activator
Activator base form eligible for seasonal replacement.

### Seasonal furniture
Furniture base form eligible for seasonal replacement.

### Seasonal movable static
MovableStatic eligible for seasonal replacement.

### Seasonal VFX
Reference-effect/visual-effect form eligible for seasonal replacement.

### Seasonal land texture
Landscape texture mapping replaced by season.

### Landscape swap
Runtime season-dependent substitution of land textures/material mapping.

### Winter snow shader
Season framework behavior applying snow-related rendering behavior during winter in valid worldspaces.

### Prefer Multipass
Current Seasons of Skyrim option preferring multipass material behavior where supported rather than single-pass handling.

## Seasonal LOD

### Seasonal terrain LOD
Distinct terrain LOD assets selected for a season.

### Seasonal object LOD
Distinct object LOD BTO assets selected for a season.

### Seasonal tree LOD
Distinct tree LOD BTT assets selected for a season.

### Season suffix
Short identifier such as WIN/SPR/SUM/AUT used in seasonal resource/config conventions.

### Seasonal LOD fallback
If expected seasonal LOD assets are absent, framework can fall back to default LOD instead of blindly referencing nonexistent files.

### Season-aware generation
Generating LOD with DynDOLOD/xLODGen so seasonal asset variants exist for runtime swapping.

### BTR
Terrain LOD mesh file extension.

### BTO
Object LOD mesh file extension.

### BTT
Tree LOD data/mesh file extension in Skyrim LOD workflows.

### Seasonal billboard
Tree/grass billboard generated for a particular season.

### Seasonal atlas
LOD texture atlas containing season-specific textures.

### Season/LOD mismatch
Nearby forms change season but distant LOD remains another season because seasonal LOD wasn't generated/loaded consistently.

## Serialization/state

### Serialized season list
Seasons framework metadata tracking save/season data outside or alongside ordinary plugin records.

### Save season state
Persisted relationship between a save and selected seasonal state/transition logic.

### Stale seasonal serialization
Saved/config season metadata referring to missing/deleted saves or old framework state.

### Season transition
Change from one season to another requiring model/landscape/LOD state refresh.

### Seasonal refresh
Runtime reload/re-evaluation to update forms/assets after season change.

## Ecosystem integration

### Seasonal asset pack
Mod supplying alternate textures/models/forms specifically for Seasons of Skyrim.

### Seasonal compatibility patch
Config/assets adapting another mod's world objects/landscape/LOD to seasonal swaps.

### Season-sensitive DynDOLOD
LOD generation configured to recognize seasonal variants and produce season-specific distant assets.

### Snow material
Material/shader setup designed for snow-covered seasonal assets.

### Multipass snow
Rendering/material technique layering snow response onto suitable assets.

### Single-pass seasonal model
Separate replacement asset that directly contains its seasonal appearance.

## Diagnostic rules

1. Distinguish runtime form swap from asset replacement and from seasonal LOD.
2. If close objects are seasonal but distant objects are not, inspect season-aware LOD generation/assets.
3. If only one worldspace fails, inspect valid-worldspace configuration before global asset changes.
4. Seasonal land/grass/tree/object systems are separate toggles/data paths.
5. Snow shader behavior can differ from explicit winter replacement models.
6. Season state may be save-sensitive; compare fresh/new save and established save when state appears stuck.
7. Regenerate dependent LOD after changing seasonal world assets or landscape mappings.

## Sources

- Seasons of Skyrim upstream: https://github.com/powerof3/SeasonsOfSkyrim
- Seasons configuration/source: https://github.com/powerof3/SeasonsOfSkyrim/blob/master/include/Seasons.h
- Seasons runtime checks: https://github.com/powerof3/SeasonsOfSkyrim/blob/master/src/Seasons.cpp
- DynDOLOD seasons documentation: https://dyndolod.info/Help/Seasons
