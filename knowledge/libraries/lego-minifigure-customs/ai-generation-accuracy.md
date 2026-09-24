# AI Generation Accuracy for Minifigure Renders and Print Templates

The goal is to stop relying on text prompting alone. High-accuracy output should be constrained by real geometry, catalog metadata and explicit production layers.

## Best architecture
Use a deterministic 3D reference model as the geometry authority, then let image models handle appearance and ideation.

Recommended pipeline:
1. choose exact canonical part IDs,
2. assemble the figure in Studio/LDraw/Blender,
3. pose deterministically,
4. render orthographic/perspective reference passes,
5. render depth, normal, silhouette, material-ID and UV-space maps,
6. feed those as controls/reference images to the image model,
7. generate appearance variants,
8. project/transfer selected design back to canonical UV/print templates,
9. manually/vector-clean production art,
10. generate separate CMYK/white/varnish/primer plates.

Do not ask a diffusion model to invent exact minifigure geometry when exact geometry already exists.

## Why structural conditioning matters
Modern controllable diffusion workflows can condition on edge and depth maps. Hugging Face Diffusers documents ControlNet using canny and depth controls and combining multiple controls; ControlNet documentation also describes normal-map conditioning, which is useful for preserving fine surface geometry.

For minifigure work, ideal conditioning set:
- RGB clay render,
- depth map,
- world/camera normal map,
- silhouette mask,
- edge/canny map,
- semantic part mask,
- optional material/color ID mask.

## Canonical views
For every figure maintain:
- orthographic front,
- orthographic back,
- left,
- right,
- front 3/4,
- rear 3/4,
- top if headgear/accessory matters,
- neutral exploded view,
- production flat art views.

Store exact camera transforms and focal length so views are reproducible.

## Geometry authority
Use LDraw or Studio/PartDesigner geometry where licensing permits. LDraw uses a right-handed coordinate system and defines 20 LDU per brick width/depth, 24 LDU per brick height, 8 LDU per plate, with approximately 0.4 mm/LDU. LDraw itself warns that real-world approximations should be verified against physical interactions.

Use geometry for:
- silhouette,
- proportions,
- connection positions,
- camera blocking,
- accessory clearance,
- AI conditioning,
- render-to-template projection.

Use physical measurement for:
- final UV print placement,
- exact jig surfaces,
- resin fits,
- tolerances.

## Part semantics
AI prompts should reference structured semantics, not vague prose. Example:
- head: standard cylindrical minifigure head
- torso: classic trapezoidal minifigure torso shell
- arms: standard left/right arms
- hands: standard C-grip hands
- legs: standard articulated hips + left/right legs
- headgear: exact catalog/design ID
- accessory: exact catalog/design ID

Include part IDs and human-readable names in generation metadata.

## Style specification
Build a reusable “minifigure visual grammar”:
- face feature scale,
- eye size and separation,
- mouth line weight,
- eyebrow line weight,
- facial hair simplification,
- torso seam conventions,
- pocket/buckle simplification,
- outline weights,
- highlight convention,
- shadow convention,
- print color limits,
- no-photorealistic-fabric rule when aiming for printed-minifigure aesthetics.

Store examples as feature primitives, not only finished characters.

## Prompt schema
Prompts should have fields:
- canonical body configuration,
- exact part IDs,
- color IDs,
- pose,
- camera,
- lens/projection,
- lighting,
- background,
- material finish,
- artwork style,
- character description,
- forbidden geometry changes,
- allowed creative freedom,
- target output type.

Example target types:
- concept_render,
- catalog_render,
- print_art_front,
- print_art_back,
- head_wrap_concept,
- arm_art,
- accessory_concept,
- resin_part_concept.

## Negative constraints
Explicitly forbid:
- extra joints,
- human fingers,
- realistic anatomical hands,
- non-minifigure shoulder geometry,
- elongated limbs,
- incorrect head diameter,
- merged arms/torso,
- sculpted clothing when print-only artwork is desired,
- invented studs/connectors,
- asymmetry unless specified,
- perspective distortion for template images.

## AI render dataset
For each canonical part/assembly render:
- neutral gray clay,
- white,
- black,
- several common LEGO colors,
- front/back/sides,
- multiple poses,
- depth,
- normals,
- silhouette,
- part-ID masks.

This synthetic set can train or condition models without contaminating geometry.

## Decal/template generation
Never treat an AI image as directly print-ready. The AI should propose graphics inside a physically calibrated 2D template. Production cleanup should:
- vectorize/redraw,
- remove raster noise,
- correct symmetry,
- enforce line minimums,
- map colors to calibrated swatches,
- generate white underbase,
- add choke,
- clip to safe area,
- validate at actual size.

## Multi-view consistency
If a character has front/back/side designs, maintain one canonical character specification and one seed/reference bundle across views. Whenever possible, derive all views from the same textured 3D asset rather than separately generating each side.

## Sources
Hugging Face ControlNet documentation:
https://huggingface.co/docs/diffusers/using-diffusers/controlnet

ControlNet depth/normal reference:
https://github.com/lllyasviel/ControlNet

BrickLink Studio decorated minifig:
https://studiohelp.bricklink.com/hc/en-us/articles/5877834417303-Creating-a-decorated-minifig

LDraw coordinate/units:
https://www.ldraw.org/article/218.html
