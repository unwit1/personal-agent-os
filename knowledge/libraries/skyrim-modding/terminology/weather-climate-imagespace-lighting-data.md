# Skyrim Modding Terminology — Weather, Climate, ImageSpace, and Lighting Data

Imported: 2026-09-24
Status: sourced deep-ingestion pass 24

## Weather records

### Weather / WTHR
Record defining sky colors, clouds, fog, precipitation, lighting, sounds, transition behavior and related exterior atmosphere.

### Cloud layer
One of multiple cloud textures with speed, alpha and color values.

### Cloud speed
Movement rate of cloud layer.

### Cloud alpha
Opacity by time-of-day phase.

### Weather color
Time-sliced values for sky, horizon, fog, sunlight, ambient and other channels.

### Sunrise
Weather time slice around dawn.

### Day
Daytime weather values.

### Sunset
Weather time slice around dusk.

### Night
Nighttime weather values.

### Fog distance
Near/far values controlling atmospheric visibility.

### Fog power
Curve controlling density progression.

### Precipitation
Rain/snow particle system associated with weather.

### Lightning
Thunderstorm flash behavior.

### Thunder sound
Audio entries triggered by storm weather.

### Weather transition
Engine blend from outgoing to incoming weather.

### Volatility
Climate/weather selection weighting/transition behavior.

## Climate

### Climate / CLMT
Record controlling which Weather types are selected in a worldspace, timing, sunrise/sunset and probability data.

### Weather list
Weighted set of WTHR records available to climate.

### Chance
Relative probability/weight of one weather.

### Sunrise Begin
Climate time controlling start of dawn transition.

### Sunrise End
End of dawn period.

### Sunset Begin
Start of dusk transition.

### Sunset End
End of dusk period.

### Phase length
Duration relationship between climate transitions.

### Moon phase
Climate/moon settings affecting moon visibility cycles.

### Worldspace climate
WRLD points to climate; changing climate changes weather selection without editing every cell.

### Regional weather
REGN records can contribute weather selection/ambient data depending on setup.

## ImageSpace

### ImageSpace / IMGS
Record controlling post-process-like scene parameters such as HDR/exposure/bloom/eye adaptation/tint-related values used by cells/weather.

### ImageSpaceModifier / IMAD
Transient modifier layered on top of current ImageSpace, often used by magic, damage, menus and scripted effects.

### Base ImageSpace
Cell/region/weather-selected image-space values before transient modifiers.

### HDR parameters
Engine values controlling eye adaptation/tonemapping-like behavior.

### Bloom
Engine brightness spread parameters.

### Saturation
Color intensity.

### Contrast
Difference between dark and bright portions.

### Tint
Color overlay/shift.

### Blur
Screen-space blur amount.

### Double vision
IMAD effect producing offset image.

### Radial blur
ImageSpaceModifier effect often used for combat/magic impact.

### Depth of field
Engine/image-space focus blur where supported.

### Eye adaptation
Brightness adjustment over time moving between dark/light spaces.

## Lighting Template

### LightingTemplate / LGTM
Reusable interior lighting/fog template referenced by CELL.

### Ambient color
Base environmental light color.

### Directional color
Directional ambient/light contribution.

### Fog near
Start distance for interior fog.

### Fog far
End distance.

### Fog color
Interior fog color.

### Fog power
Fog density curve.

### Directional rotation
Orientation of directional ambient/light.

### Directional fade
Strength/fade relationship.

### Specular color
Lighting response for shiny materials.

### Inherit flag
CELL can inherit selected values from LGTM while overriding others directly.

### Cell lighting override
CELL stores its own values overriding template fields.

## DALC

### DALC
Directional Ambient Lighting Colors data.

### X+
Ambient light contribution from positive X direction.

### X-
Ambient light contribution from negative X direction.

### Y+
Ambient light contribution from positive Y direction.

### Y-
Ambient light contribution from negative Y direction.

### Z+
Ambient light contribution from above.

### Z-
Ambient light contribution from below.

### Specular/ambient middle
Tool-specific representation/derived values; verify source schema when editing.

## Region

### Region / REGN
World-data record assigning objects, weather, map data, grass/sounds and other procedural/environmental features to geographic areas.

### Region area
Polygonal exterior region boundary.

### Weather region
REGN entry influencing climate/weather choice.

### Sound region
Ambient sound distribution.

### Object region
Procedural placement of rocks/plants/objects.

### Grass region
Grass distribution data.

### Map region
Map-label/region-related data.

### Region overlap
Two region definitions apply to same location; engine-specific priority/order determines effects.

## Volumetric lighting

### Volumetric lighting
Atmospheric light scattering/fog/rays based on weather/environment values.

### God rays
Visible shafts from sun/light through atmosphere.

### Volumetric color
Color applied to scattering/fog.

### Volumetric intensity
Strength of effect.

### Volumetric distance
Range over which scattering applies.

### Community Shaders volumetric feature
Native renderer extension can reinterpret/enhance vanilla weather inputs.

### ENB weather settings
ENB can provide per-weather overrides independent of plugin WTHR values.

## Runtime manipulation

### SetWeather
Force/transition to configured Weather via script/console.

### ForceWeather
Immediate weather override.

### ReleaseWeatherOverride
Return control to climate/weather selection.

### Current weather
Weather presently active.

### Outgoing weather
Weather being blended out.

### Weather percent
Transition fraction between outgoing/current states.

### KreatE override
Runtime live-edit layer changing WTHR/IMGS/LGTM values without static plugin edit.

## Compatibility

### Weather overhaul
Replaces climate weather lists and/or WTHR records.

### Lighting overhaul
Edits CELL/LGTM/IMGS/light references.

### ENB preset
External renderer can dramatically change interpretation of the same WTHR/LGTM/IMGS data.

### Community Shaders preset/config
Renderer feature configuration layered over game weather data.

### Interior lighting patch
Reconciles architecture/cell records with desired LGTM/IMGS values.

### Weather patch
Forwards WTHR/CLMT values while preserving unrelated worldspace/region changes.

## Diagnostic rules

1. Distinguish Weather selection (CLMT/REGN) from Weather appearance (WTHR).
2. Exterior and interior lighting pipelines differ; LGTM/CELL does not control ordinary exterior sky.
3. IMAD is transient and can make screenshots differ even when IMGS/WTHR are unchanged.
4. ENB/CS can override reinterpret final appearance; reproduce with renderer config recorded.
5. KreatE can make runtime values differ from xEdit.
6. Cell lighting inheritance flags matter when patching LGTM vs direct CELL values.
7. If weather never appears, inspect climate/region weights before editing WTHR visuals.

## Sources

- Creation Kit Wiki World Data category and Weather/Climate/ImageSpace/Lighting Template pages
- KreatE: https://www.nexusmods.com/skyrimspecialedition/mods/83757
- Creation Kit Wiki video/tutorial index: https://ck.uesp.net/wiki/Video_Tutorials
