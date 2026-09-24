# Skyrim Modding Terminology — KreatE and Live Weather/Lighting Editing

Imported: 2026-09-24
Status: sourced deep-ingestion pass 22

## KreatE

### KreatE
Kitsuune's Visual Real-time Editor: SKSE plugin providing non-destructive in-game editing/preview of weather, imagespace, volumetric-lighting, cell-lighting and lighting-template parameters.

### Real-time editor
Tool modifies loaded runtime values immediately so author can preview changes without repeated CK/xEdit save/relaunch cycles.

### Non-destructive edit
Runtime/preset change does not directly rewrite ESP/ESM/ESL.

### Preset
Named collection of live-edited values stored outside plugin.

### Active preset
Preset currently applied to matching records.

### Original value
Value loaded from plugin data before KreatE runtime changes.

### Revert
Restore current runtime value to original plugin-loaded state.

### Save to preset
Persist runtime-edited value into KreatE config/preset.

### Load preset
Apply saved values to current runtime form.

### Managed weather
Weather form registered in a preset for editing.

### Current weather
Weather presently active.

### Outgoing weather
Weather transitioning out.

### Weather override
Tool-controlled weather selected for authoring/preview.

### Time control
Tool changes/holds game time so author can inspect dawn/day/dusk/night values.

## Editable record families

### Weather / WTHR
KreatE edits sky/cloud/fog/color/lighting and related weather values.

### ImageSpace / IMGS
Environment/post-processing values applied by cell/weather.

### Volumetric Lighting
Time/weather volumetric lighting records/parameters.

### Cell Lighting
Interior CELL ambient/fog/lighting values.

### Lighting Template / LGTM
Reusable interior lighting template values.

### Directional Ambient Lighting Colors / DALC
Directional ambient-light color data used by weather/cell lighting.

### DALC fix
Optional KreatE runtime fix for Skyrim directional ambient lighting behavior.

### DALC middle value
KreatE/xEdit conversion tooling may treat/edit directional ambient values in ways that need rounding/axis awareness.

## EditorID integration

### Preset filename
KreatE often uses unique preset/record names and can default to EditorID when available.

### Native EditorID Fix integration
NEIF allows human-readable record IDs to appear reliably in KreatE and helps preset->xEdit conversion workflows use stable names.

### Unique preset name
KreatE requires unique names for managed entries to avoid ambiguity.

## Exporting to plugins

### KreatE-to-xEdit script
Community script reads saved KreatE preset files and writes values into a plugin through xEdit.

### Exterior conversion
Script family translating Weather/Volumetric Lighting preset values into plugin fields.

### Interior conversion
Script family translating Cell Lighting/Lighting Template/ImageSpace presets into plugin fields.

### Runtime preview -> static patch
Workflow: tune in game with KreatE, save preset, export selected values into ESP using xEdit, then test without runtime override.

### FormID resolution
Export script must map preset filename/EditorID to correct plugin form, including light-plugin FormIDs.

### Rounding difference
Float/color conversion can result in +/-1 RGB or other tiny numeric changes; verify generated fields.

## Environment authoring concepts

### Weather time slices
Weather color/lighting values vary across sunrise/day/sunset/night.

### Fog near
Distance at which fog begins.

### Fog far
Distance/end parameter affecting visibility.

### Fog power
Curve/intensity shaping distance fog.

### Directional ambient
Ambient lighting differentiated by world direction.

### Sunlight color
Directional sunlight tone.

### Ambient color
Non-directional/environmental light.

### Cloud layer
Weather cloud texture/speed/color/alpha layer.

### Volumetric color
Lighting color applied to volumetric fog/rays.

### Image-space exposure
ImageSpace value affecting brightness/tonemap-like game output.

### Interior fog
CELL/LGTM values independent from exterior weather.

## Compatibility

### Runtime visual override
KreatE preset can make current game look different from every static xEdit record.

### Preset conflict
Two presets/settings attempt to manipulate same weather/lighting record.

### Weather mod update
Original values change, so old KreatE preset may be based on stale source assumptions.

### Static export conflict
Generated plugin must still be conflict-resolved against weather/interior-lighting overhauls.

### ENB/Community Shaders interaction
KreatE changes game inputs; final appearance also depends on external/native rendering framework.

### Console conflict
KreatE UI captures input; documentation recommends avoiding console simultaneously because changes/UI state can be confusing.

## Diagnostic rules

1. If weather looks different from xEdit, check active KreatE preset/runtime overrides.
2. Use live editor for visual tuning, then explicitly decide whether preset or exported ESP is canonical.
3. EditorID filenames aid workflow but are not immutable semantic IDs.
4. Re-test exported static plugin with KreatE disabled/reverted.
5. Visual appearance must be evaluated under same ENB/CS/Reshade and time/weather context.
6. Record source weather mod version before sharing preset.

## Sources

- KreatE: https://www.nexusmods.com/skyrimspecialedition/mods/83757
- KreatE-to-xEdit scripts: https://www.nexusmods.com/skyrimspecialedition/mods/157525
- Native EditorID Fix: https://www.nexusmods.com/skyrimspecialedition/mods/85260
- Creation Kit world-data references: https://ck.uesp.net/wiki/Category:WorldData

## Dated snapshot

KreatE 1.5.1 was current on 2026-09-24, updated 2026-08-09.
