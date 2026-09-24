# Skyrim Modding Knowledge — LOD, Grass, Seasons, Occlusion, and Distant-World Generation

Imported: 2026-09-24
Status: sourced encyclopedia pass 4

This module consolidates the complete distant-world generation stack: terrain LOD, object LOD, tree LOD, grass LOD, dynamic LOD, large references, seasonal variants, texture atlases, and occlusion.

## Native Skyrim LOD systems

### Terrain LOD
Distant ground meshes/textures representing worldspace terrain beyond active cells.

### Object LOD
Distant static geometry built into BTO meshes and texture atlases for eligible world objects.

### Tree LOD
Dedicated billboard-based distant-tree system in Skyrim.

### Water LOD
Distant water representation coupled to terrain/world LOD data.

### LOD level
Distance tier. Object and terrain LOD use multiple levels such as LOD4/8/16/32 depending on system/tool terminology.

### LOD4
Nearest ordinary object/terrain LOD tier outside full-detail region.

### LOD8
Farther LOD tier.

### LOD16
Still farther LOD tier.

### LOD32
Very distant terrain/object world representation.

### BTO
Bethesda object-LOD mesh file generated for worldspace cell blocks.

### BTR
Terrain LOD mesh file.

### BTT
Tree LOD data/mesh representation in applicable Skyrim LOD formats.

### DDS atlas
Texture atlas referenced by combined LOD geometry.

## xLODGen / LODGen

### xLODGen
xEdit-derived world scanner/generator used especially for terrain LOD and Bethesda-style static object/tree LOD workflows.

### xLODGen terrain LOD beta
Current development branch/tool used to generate high-quality terrain LOD before DynDOLOD in common modern workflows.

### LODGen
Command-line generator consuming data exported by xLODGen/DynDOLOD to create object/terrain LOD meshes.

### Terrain LOD mesh
Generated low-resolution distant terrain geometry.

### Terrain LOD diffuse texture
Distant terrain color texture.

### Terrain LOD normal texture
Distant terrain normal map controlling distant lighting detail.

### Terrain underside
Generated geometry beneath terrain intended to stop sunlight/rays from leaking through mountains/landforms in distant rendering.

## TexGen

### TexGen
DynDOLOD companion generator that derives selected object-LOD textures plus tree/grass billboards from the current installed assets.

### TexGen Output
Generated mod containing current-load-order-specific LOD textures/billboards used as input by DynDOLOD.

### Stitched object LOD texture
Texture assembled from existing full-resolution texture regions according to TexGen configuration.

### Rendered object LOD texture
Texture produced by rendering a source NIF/model into a distant representation.

### Object LOD texture atlas
Combined atlas packed from LOD source textures and referenced by generated object LOD.

### Billboard
Rendered/texture representation of an object/tree/grass used at distance.

### Tree billboard
Tree LOD image/metadata used by standard or generated tree LOD.

### Grass billboard
Billboard generated for eligible grass used in grass-LOD object generation.

### Billboard dimensions
World/model dimensions stored/derived so billboard displays at correct scale.

### Billboard CRC/source matching
DynDOLOD/TexGen mechanisms comparing source full models/textures and generated billboard state to detect outdated inputs.

### Outdated billboard
Billboard generated against different source model/texture/load order. Regenerate TexGen when the full asset changes.

## DynDOLOD

### DynDOLOD
Advanced xLODGen-derived system creating improved object/tree/dynamic LOD and supporting data for Skyrim/Enderal.

### DynDOLOD Resources
Required resource package containing meshes/textures/configuration/support data used by generation/runtime features.

### DynDOLOD output
Generated plugin/assets/scripts/config representing one exact source load order and generation configuration.

### Reference rule
DynDOLOD rule deciding how an eligible reference is represented at various LOD distances.

### Mesh mask rule
Rule selecting/replacing/controlling LOD models based on mesh path/pattern.

### LOD model
Simplified NIF used for distant object representation.

### Full model
Normal nearby game mesh, sometimes also used by dynamic/ultra LOD under configured rules.

### Static object LOD
Vanilla-style combined distant geometry.

### Dynamic LOD
DynDOLOD system creating runtime-manageable distant references that can react to enable states and use full/specialized models.

### NearGrid
Dynamic LOD region immediately outside active exterior cells.

### FarGrid
Farther dynamic LOD region.

### Ultra tree LOD
DynDOLOD mode representing trees through object/dynamic LOD rather than relying solely on vanilla standard tree-LOD restrictions.

### 3D tree LOD
Simplified three-dimensional distant tree model instead of a flat billboard.

### Hybrid tree
LOD model combining billboard-like planes and 3D geometry.

### Billboard tree LOD
Traditional texture-plane distant tree representation.

### Tree LOD atlas
Single standard-tree atlas per worldspace under vanilla standard tree LOD; DynDOLOD documentation notes a 256-billboard limit for standard tree LOD.

## Grass

### Full grass
Nearby actual grass meshes generated by Skyrim from GRAS/LAND data.

### Grass cache
Precomputed per-cell grass data used by No Grass In Objects/related workflows to preserve generation beyond loaded-cell constraints.

### No Grass In Objects / NGIO
SKSE framework/tooling historically used to pre-cache grass placements and prevent grass inside excluded objects; modern runtime support depends on exact build/ecosystem.

### Grass LOD
Distant billboard representation inserted into object LOD using cached external grass data.

### Grass LOD density
Generation multiplier/settings controlling fraction/amount of cached grass represented at distance.

### Grass LOD brightness
TexGen/DynDOLOD adjustment used to match billboard appearance to nearby full grass.

### Complex grass
ENB/Community-Shaders-related grass material/lighting ecosystem requiring compatible billboard/generation settings when used for LOD.

### Grass fade
Distance range where full grass fades before distant grass LOD takes over.

### Grass LOD transition
Visual handoff between full grass and billboard/object-LOD grass.

## Seasons

### Seasons
Runtime ecosystem allowing world assets/landscape/objects to use season-specific variants.

### Seasonal LOD
Separate LOD assets/generated data for enabled seasons/worldspaces.

### Season identifier
Configured seasonal state such as WIN/SPR/SUM/AUT depending on framework/tool convention.

### Seasonal swap
Base/model/texture selection changing with current season.

### Seasonal object LOD
LOD generated using season-specific model/texture rules.

### Seasonal tree LOD
Tree/dynamic LOD generated for seasonal tree variants.

### Seasonal atlas
Object/tree texture atlas produced for one seasonal state.

### Season-aware generation
DynDOLOD scans/generates required seasonal variants when Seasons support is enabled for a worldspace.

### Snow shader LOD
Distant material/shader behavior used to represent snow-covered seasonal objects.

## Occlusion

### TVDT
CELL subrecord/field containing terrain LOD occlusion data used to hide distant LOD behind terrain.

### Occlusion data
Per-exterior-cell data telling the engine which distant LOD can be culled because terrain blocks the view.

### Occlusion.esp
Generated plugin containing TVDT cell overrides. DynDOLOD can generate this separately and light-flag it where possible.

### Occlusion generation
Calculation performed after appropriate terrain/object LOD is available to derive distant visibility blocking.

### Occlusion culling
Skipping distant geometry known not to be visible.

### Terrain occlusion
Using terrain LOD geometry to decide which distant object LOD regions can be hidden.

### Stale occlusion
Occlusion data no longer matches changed terrain/worldspace/LOD and should be regenerated.

## Large references and distant state

### Large reference
SE/VR engine feature rendering certain full models outside normal active cells.

### Large-reference grid
Distance region for large-reference full models.

### Large-reference bug
Known engine inconsistency when large refs are changed/overridden under certain plugin conditions, producing flicker/disappearing/LOD transition defects.

### Neverfade
Reference with Is Full LOD behavior, displayed beyond normal active cells.

### Has Distant LOD
Base-record flag/data indicating availability/eligibility for distant LOD representation.

### Persistent + Is Full LOD
Flag combination used by some neverfade/reference behaviors.

### Large-reference workaround
DynDOLOD DLL/runtime mechanism mitigating documented large-ref engine issues under supported setup.

## Generation order

### Terrain-first workflow
Generate terrain LOD with xLODGen before TexGen/DynDOLOD so later systems can use matching world terrain/occlusion.

### TexGen-before-DynDOLOD
TexGen should generate current source-dependent LOD textures/billboards and be installed before running DynDOLOD.

### DynDOLOD generation
Run after source mods, TexGen output and required terrain/grass data are in their intended final state.

### Occlusion-last
Generate occlusion from the final relevant terrain/object world state; changing terrain/world data afterward can stale it.

### Regeneration trigger
Any relevant change to world references, full models, tree/grass assets, terrain, seasons, load order or LOD rules can require regenerating affected outputs.

## Common failure signatures

### LOD mismatch
Distant shape/color differs visibly from full nearby object.

### LOD pop
Abrupt noticeable transition between distant and full model.

### Stuck object LOD
Engine bug where old object LOD remains after the full cell loads/after travel; DynDOLOD dynamic LOD or specific fixes may address it.

### Floating LOD
Distant representation does not match changed terrain/reference transform.

### Missing LOD
Eligible object/tree/terrain absent at distance because source rule/model/billboard/generation failed.

### Wrong LOD texture
Generated atlas uses stale or wrong source texture.

### Black LOD
Material/texture/shader/atlas generation problem producing dark distant geometry.

### Billboard mismatch
Tree/grass billboard does not resemble active full model.

### Atlas overflow
Too many/too-large source textures cannot fit target atlas constraints; standard tree LOD has stricter billboard-count/atlas limits than ultra tree LOD.

### LOD seam
Visible border between terrain LOD tiles or transition from full terrain to distant terrain.

## Diagnostic rules encoded for Agent OS

1. Identify whether symptom is terrain, object, tree, grass, dynamic, large-reference or full-model state before changing settings.
2. TexGen output is load-order-specific generated input, not a generic static resource.
3. Run TexGen before DynDOLOD and install its output so generation sees it.
4. Regenerate billboards after source tree/grass models/textures change.
5. Occlusion data should reflect the final terrain/world configuration.
6. Standard tree LOD and ultra/object-based tree LOD have different constraints; do not generalize the 256-billboard limit to all tree-LOD modes.
7. Grass LOD consumes object-LOD resources/performance and depends on compatible cached grass data.
8. Seasons multiply generated states; confirm every enabled worldspace/season has matching LOD.
9. Large-reference bugs are engine/reference-flag/override issues, not necessarily generated-mesh defects.
10. Treat DynDOLOD warnings/errors as structured evidence; don't suppress them merely to complete generation.

## Sources

- DynDOLOD Reference: https://dyndolod.info/DynDOLOD-Reference
- TexGen: https://dyndolod.info/Help/TexGen
- TexGen Configuration: https://dyndolod.info/Help/TexGen-Configuration
- Occlusion Data: https://dyndolod.info/Help/Occlusion-Data
- Advanced Mode / Seasons: https://dyndolod.info/Help/Advanced-Mode
- Texture Resolution: https://dyndolod.info/Help/Texture-Resolution
- DynDOLOD terminology: https://dyndolod.info/Terminology
- DynDOLOD FAQ: https://dyndolod.info/FAQ
- DynDOLOD changelog: https://dyndolod.info/Changelog
