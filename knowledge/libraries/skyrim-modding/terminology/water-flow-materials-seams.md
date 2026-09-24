# Skyrim Modding Terminology — Water Records, Flow, LOD, Materials, and Seams

Imported: 2026-09-24
Status: sourced deep-ingestion pass 21

## Water data layers

### WaterType / WATR
Record defining water visual/physical properties such as color, opacity/refraction, fog, wave/noise, sound and shader-related settings.

### Cell water
Water-related data stored on CELL records, including selected WaterType and Skyrim SE flow information for exterior cells.

### Worldspace water
WRLD-level water defaults and distant-water/LOD relationships.

### Water height
Elevation of water surface associated with cell/worldspace/reference context.

### Default water
Worldspace/cell inherited WaterType when no specialized override is present.

### Interior water
Water plane/data inside interior CELL.

### Exterior water
Worldspace/cell water participating in adjacent-cell and distant-water systems.

### Flow data
Skyrim SE cell data controlling direction/behavior of flowing water at exterior-cell level.

### Flow map
Texture/data directing visual water flow direction.

### No-flow water
Water appearance without directional flow-map influence.

### Wave amplitude
Water shader parameter controlling apparent wave displacement amount.

### Wave UV
Texture-coordinate/flow scaling affecting perceived wave speed/size/direction.

### Displacement
ENB/Community Shaders rendering feature using height data to give water surface 3D-like wave geometry.

### Water height map
Texture/data used by displacement/parallax water rendering.

### Water cubemap
Environment reflection texture used by water shader.

### Refraction
Distortion/visibility of geometry beneath water surface.

### Reflection
Water surface representation of environment/sky/scene.

### Transparency
Water opacity/visibility parameter.

### Shoreline blending
Transition at shore/water boundary reducing hard seams.

### Water fog
Underwater/distance fog associated with WaterType.

### Water sound
Ambient/loop sound associated with water record/context.

## Skyrim SE flow-data history

### Update.esm water flow data
Skyrim Special Edition's Update.esm added flow information to exterior CELL records that did not exist in the same form in Oldrim/LE.

### Oldrim port water regression
LE-era mod port that overrides a CELL for unrelated reason can replace SE Update.esm cell data with older record content and unintentionally remove water flow/type fields.

### Cell record reversion
Later plugin copies older/vanilla-like CELL values and unintentionally discards SE water fields.

### Water seam
Visible discontinuity between adjacent water cells/regions due to mismatched water type, flow, color, height, LOD or shader data.

### Cell-boundary seam
Line where adjacent CELL water settings differ.

### WaterType seam
Adjacent cells resolve different WATR records/values.

### Flow seam
Adjacent cells contain incompatible/missing flow vectors/data.

### Height seam
Different water elevations or LOD/full-water mismatch.

### Color seam
Different WaterType color/transparency values.

### Distant-water seam
Worldspace/LOD water does not match nearby WaterType/worldspace changes.

## Water for ENB

### Water for ENB
Comprehensive water overhaul using water, CELL and WRLD edits plus textures/assets to provide ENB-oriented water appearance.

### W4ENB cell forwarding
Compatibility patches must preserve Water for ENB's intended cell water data when other mods also edit those cells.

### W4ENB worldspace forwarding
Worldspace water edits must also survive for distant LOD water to transition correctly.

### Water for ENB Synthesis patch
Automated patching approach forwarding Water for ENB's water fields through unrelated cell/worldspace conflicts.

### Shades of Skyrim
Water for ENB variant using regional water colors/types rather than one universal water appearance.

## Simplicity of Sea

### Simplicity of Sea
Lightweight water overhaul emphasizing textures/displacement and an optional ESP that edits only WATR records rather than CELL/WRLD data.

### Zero-cell-edit strategy
Avoiding CELL edits reduces traditional water seam compatibility patch surface.

### Zero-worldspace-edit strategy
Avoiding WRLD edits reduces distant-water conflict surface.

### Optional flow maps
Simplicity of Sea can enable/disable flow-map behavior through installer/plugin choices.

### Seamless LOD design
Water mod architecture that leaves cell/worldspace data intact so distant/near water remains less sensitive to load-order conflicts.

### Green cubemap bug
Vanilla issue where water can inherit/retain inappropriate green interior cubemap after transitioning outdoors; Simplicity of Sea includes a fix.

## Water Seams Fix Synthesis

### Water Seams Fix
2026 Synthesis patcher family scanning winning CELL records and forwarding correct water fields from a truth source.

### Vanilla water patcher
Uses Update.esm/USSEP water data as source of truth for cells whose unrelated mods reverted water fields.

### Water for ENB patcher
Forwards W4ENB-specific water types/heights/environment/LOD fields rather than blindly restoring vanilla.

### Truth source
Selected upstream record from which water-specific fields should be forwarded.

### Field-level forwarding
Patch copies only relevant water fields while preserving unrelated winning cell changes.

### Automated cell scan
Patcher iterates all exterior cells rather than requiring a hand-maintained patch list.

## Water LOD

### Distant water
Simplified worldspace water representation drawn at distance.

### Water LOD
Distant water rendering tied to WRLD/water settings rather than ordinary object LOD mesh.

### LOD transition
Boundary between nearby high-detail water and distant-water representation.

### Distant reflection
ENB/renderer option affecting reflection on distant water.

### Water LOD mismatch
Near water looks correct but horizon/distant region has different color/reflection/height.

## Water/material rendering

### ENB water
ENBSeries water shader features including displacement, reflection/refraction enhancements.

### Community Shaders Water Effects
CS feature stack providing advanced water rendering such as displacement/reflection/refraction according to current framework.

### Parallax water
Height/displacement-driven water surface detail.

### Caustics
Light patterns projected beneath/through water.

### Underwater effect
ImageSpace/shader/fog behavior activated while camera/player is submerged.

### Water edge foam
Texture/mesh/effect used where moving water meets rocks/shores.

### Waterfall
Usually separate mesh/effect/texture system rather than WATR plane itself.

## Water compatibility strategy

### Water-record-only mod
Edits WATR but not CELL/WRLD. Lower compatibility surface.

### Cell water mod
Edits CELL water fields and needs forwarding around city/landscape/location mods.

### Worldspace water mod
Edits WRLD water/LOD settings and must win/patch those fields.

### Water patch
Conflict-resolution plugin forwarding desired water values while preserving unrelated CELL/WRLD changes.

### Water synthesis
Generated patch resolving water fields load-order-wide.

### Flow-map patch
Plugin restoring or altering SE flow fields while preserving other cell edits.

## Diagnostic rules

1. If seam follows a CELL border, inspect CELL water/flow overrides before textures.
2. LE ports that edit exterior cells are high-risk for reverting SE flow data.
3. Water for ENB needs both CELL and relevant WRLD forwarding; simple load-after can overwrite unrelated changes.
4. Simplicity of Sea deliberately avoids cell/worldspace edits, reducing seam patch burden.
5. Distant-water mismatch is not ordinary DynDOLOD object LOD.
6. Regenerating object/tree LOD does not repair a CELL flow-data conflict.
7. Do not use a generic "water fix" that restores vanilla fields if the installed water overhaul intentionally changes those fields.
8. Renderer (ENB/CS), water records and texture/flow assets are distinct layers.

## Sources

- Water for ENB: https://www.nexusmods.com/skyrimspecialedition/mods/37061
- Simplicity of Sea: https://www.nexusmods.com/skyrimspecialedition/mods/56520
- Water Seams Fix — Synthesis Patcher: https://www.nexusmods.com/skyrimspecialedition/mods/171509
- Realistic Water Two FAQ: https://www.nexusmods.com/skyrimspecialedition/articles/626
- Realistic Water Two: https://www.nexusmods.com/skyrimspecialedition/mods/2182

## Dated evidence

The 2026 Water Seams Fix Synthesis documentation explicitly identifies SE Update.esm water-flow data loss from Oldrim-ported/unrelated CELL overrides as a common cause of seams and provides separate vanilla vs Water for ENB forwarding strategies.
