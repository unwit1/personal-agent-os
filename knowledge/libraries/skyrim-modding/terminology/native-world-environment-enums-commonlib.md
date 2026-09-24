# Skyrim Native Cell, Worldspace, Weather, Climate, and Water Enums — CommonLibSSE-NG

Imported: 2026-09-24
Status: finite reverse-engineered source catalog

## Sources

- `TESObjectCELL.h` blob `fa8a60c3986f907480c975155fc2cf1d6652b397`
- `TESWorldSpace.h` blob `8625640c09027fc17b7dfb416a0b9039ac6965ba`
- `TESWeather.h` blob `dc0d6c4a5e786216902aa55d6764d3734a05b6aa`
- `TESClimate.h` blob `1799438b2ffc9aea2c9b746f1aa2068b7fbf2982`
- `TESWaterForm.h` blob `c1b1e9765811f7e0b128ca7d2e4bb08a391d135c`

Upstream: https://github.com/alandtse/CommonLibSSE-NG

## CELL flags

| Flag | Bit/value |
|---|---|
| `kNone` | `0` |
| `kIsInteriorCell` | `1 << 0` |
| `kHasWater` | `1 << 1` |
| `kCanTravelFromHere` | `1 << 2` |
| `kNoLODWater` | `1 << 3` |
| `kHasTempData` | `1 << 4` |
| `kPublicArea` | `1 << 5` |
| `kHandChanged` | `1 << 6` |
| `kShowSky` | `1 << 7` |
| `kUseSkyLighting` | `1 << 8` |
| `kWarnToLeave` | `1 << 9` |

These are CELL-specific native flags. They are distinct from record-header flags and from save ChangeFlags.

## CELL state

| State | Value |
|---|---:|
| `kAttached` | `7` |

Cell attachment/loading state is a runtime lifecycle concept; a cell existing in the plugin does not imply it is attached/loaded.

## Landscape hide flags

| Flag | Bit/value |
|---|---|
| `kNone` | `0` |
| `kQuad1` | `1 << 0` |
| `kQuad2` | `1 << 1` |
| `kQuad3` | `1 << 2` |
| `kQuad4` | `1 << 3` |

These runtime/native landscape hide flags are separate from LAND texture/height data.

## WRLD flags

| Flag | Bit/value |
|---|---|
| `kNone` | `0` |
| `kSmallWorld` | `1 << 0` |
| `kCantFastTravel` | `1 << 1` |
| `kNoLODWater` | `1 << 3` |
| `kNoLandscape` | `1 << 4` |
| `kNoSky` | `1 << 5` |
| `kFixedDimensions` | `1 << 6` |
| `kNoGrass` | `1 << 7` |

## WRLD parent-use flags

| Parent inheritance flag | Bit/value |
|---|---|
| `kNone` | `0` |
| `kUseLandData` | `1 << 0` |
| `kUseLODData` | `1 << 1` |
| `kUseMapData` | `1 << 2` |
| `kUseWaterData` | `1 << 3` |
| `kUseClimateData` | `1 << 4` |
| `kUseImageSpaceData` | `1 << 5` |
| `kUseSkyCell` | `1 << 6` |

A child worldspace can inherit selected fields from a parent worldspace. As with NPC templates, patching the child value can be ineffective or misleading when the corresponding parent-use flag delegates that field.

## Weather sound type

| Type | Value |
|---|---:|
| `kDefault` | `0` |
| `kPrecip` | `1` |
| `kWind` | `2` |
| `kThunder` | `3` |

## Weather flags

| Flag | Bit/value |
|---|---|
| `kNone` | `0` |
| `kPleasant` | `1 << 0` |
| `kCloudy` | `1 << 1` |
| `kRainy` | `1 << 2` |
| `kSnow` | `1 << 3` |
| `kPermAurora` | `1 << 4` |
| `kAuroraFollowsSun` | `1 << 5` |

Weather flags affect engine behavior independently of colors/clouds/fog.

## Weather color times

| Time slice | Value |
|---|---:|


## Weather color channels/types

| Color type | Value |
|---|---:|


This is the native counterpart to weather color arrays used for sky, fog, ambient, sunlight, cloud and related channels.

## Climate sky objects

| Object | Value |
|---|---:|


## Climate moon phase length

| Enum | Value |
|---|---:|
| `kPhaseLengthMask` | `0x3F` |
| `kNone` | `0` |
| `kMasser` | `1 << 6` |
| `kSecunda` | `1 << 7` |

Climate controls weather selection and astronomical/timing behavior; it is not the same as WTHR appearance.

## Water flags

| Flag | Bit/value |
|---|---|
| `kNone` | `0` |
| `kCauseDamage` | `1 << 0` |
| `kEnableFlowmap` | `1 << 3` |
| `kBlendNormals` | `1 << 4` |

Water behavior combines WATR data, CELL/WRLD assignment, flow data, shader/rendering features and saved/reference state. A WATR flag is therefore only one layer of the final appearance.

## Cross-layer world diagnostics

### CELL vs WRLD
CELL owns local/interior/exterior cell state; WRLD supplies worldspace defaults/inheritance/map/LOD context.

### WTHR vs CLMT
WTHR describes one weather's appearance/behavior. CLMT determines which weathers are selected and when.

### WATR vs CELL flow
WATR describes a water type; exterior CELL data can carry flow information that gets reverted by unrelated old cell overrides.

### Static vs runtime
Cell state, weather transition state, runtime weather overrides, KreatE edits, renderer effects, save state and generated LOD can all make the game differ from a static xEdit view.

## Patch rules

1. Inspect WRLD parent-use flags before assuming a child's apparent field is authoritative.
2. Patch CELL fields by subsystem; do not copy whole CELL records to fix water or lighting.
3. Weather selection and appearance are separate.
4. Water record, cell water/flow, worldspace distant water and renderer are separate.
5. Cell attachment state matters for native/Papyrus operations that require loaded references.
6. Preserve version provenance when native enum fields are reverse-engineered rather than documented by Bethesda.
