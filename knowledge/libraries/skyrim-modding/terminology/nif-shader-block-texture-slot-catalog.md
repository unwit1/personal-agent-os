# Skyrim Modding Terminology — NIF Blocks, Shader Properties, Texture Slots, and Geometry Types

Imported: 2026-09-24
Status: sourced frontier-deepening pass

## Core NIF scene blocks

### NiObject
Base NIF object class.

### NiAVObject
Scene object with transform, flags, parent/child participation and bounds.

### NiNode
Scene-graph node containing child references.

### BSFadeNode
Bethesda scene root often used for statics/objects supporting fade/LOD behavior.

### NiTriShape
Older geometry block used heavily by Skyrim LE and still present in selected SSE assets.

### NiTriShapeData
Vertex/triangle/UV/normal data block paired with NiTriShape.

### BSTriShape
Skyrim SE optimized geometry block storing geometry in Bethesda-specific packed format.

### BSDynamicTriShape
Skinned/dynamic geometry variant used by headparts and other dynamic SSE shapes.

### BSMeshLODTriShape
Geometry block supporting mesh LOD behavior.

### BSSubIndexTriShape
Bethesda geometry subtype used more prominently in FO4-era formats but can appear in multi-game tooling.

### BSLODTriShape
LE-era LOD geometry subtype.

## Skinning

### NiSkinInstance
Skin-binding relationship between geometry and skeleton.

### BSDismemberSkinInstance
Skinned-geometry instance with body/partition metadata.

### NiSkinData
Bone transforms and skin data.

### NiSkinPartition
Partitioned vertex/triangle data optimized for skinned rendering.

### Skin partition
Subset of skinned triangles constrained by bone/partition limits.

### Body partition
Semantic partition mapped to biped/body slots.

### Bone index
Local index into skeleton/skin partition bone list.

### Bone weight
Influence of one skeleton bone on vertex.

### Max influences
Engine/tool limit on number of bones significantly affecting one vertex.

## Shader properties

### BSShaderProperty
Base Bethesda shader property.

### BSLightingShaderProperty
Primary Skyrim lighting/material shader block.

### BSEffectShaderProperty
Special-effect shader used by glows, magic, particles and effect-like geometry.

### BSShaderTextureSet
Separate block storing texture paths for BSLightingShaderProperty.

### Shader Type
BSLightingShaderProperty mode determining special material path such as Default, Environment Map, Glow, Parallax, Face Tint, Skin Tint, Hair Tint, MultiLayer Parallax, Eye Envmap and others.

### Shader Flags 1
First bitfield controlling material behavior such as specular, skinned, vertex alpha, own emit and other engine-specific flags.

### Shader Flags 2
Second bitfield controlling environment mapping, vertex colors, tree animation and other behavior.

### Skinned flag
Shader/geometry expects bone skinning.

### Specular flag
Enables specular lighting response.

### Vertex Colors
Shader uses per-vertex color/alpha values.

### Vertex Alpha
Per-vertex alpha influences transparency.

### Own Emit
Geometry uses configured emissive color/multiplier.

### Environment Mapping
Use cubemap/environment reflection.

### Parallax
Use parallax height map and corresponding shader type/flags.

### Double Sided
Render both face directions where supported by flags/material setup.

### ZBuffer Test
Depth test participation.

### ZBuffer Write
Writes to depth buffer.

### Decal
Special blending/depth semantics for projected/decal-like geometry.

### Soft Lighting
Soft-lighting shader behavior used by skin/foliage/effects depending on material.

### Rim Lighting
View-angle rim contribution.

### Back Lighting
Back-side/translucency-like lighting contribution.

### Tree Anim
Tree/foliage vertex animation.

## Common SSE texture slots

### Slot 0 — Diffuse / Base Color
Primary color texture.

### Slot 1 — Normal Map
Tangent-space normal map; Skyrim normal textures can also store specular-related information in alpha depending on workflow.

### Slot 2 — Glow / Subsurface
Usage depends on shader type/flags.

### Slot 3 — Height / Parallax
Height map for parallax-capable materials.

### Slot 4 — Cubemap
Environment-reflection texture.

### Slot 5 — Environment Mask
Mask controlling where cubemap reflection applies.

### Slot 6 — Tint / Detail
Usage varies by shader type, e.g. tint/detail/other specialized material data.

### Slot 7 — Backlight
Backlighting-related texture in supported material path.

### Slot 8 — Specular
SSE-specific tooling may expose specular-related slot depending on shader/material path.

### Slot 9 — Lighting
Additional SSE lighting texture slot in tooling/schema.

Texture-slot meaning is shader-type dependent; never infer semantics from index alone without shader context.

## BSEffectShaderProperty slots

### Effect source texture
Primary effect texture.

### Effect normal texture
Normal map where used.

### Effect greyscale texture
Greyscale/palette input for recolored effects.

### Effect environment map
Cubemap.

### Effect environment mask
Mask for environment mapping.

## Material parameters

### UV Offset
Texture translation.

### UV Scale
Texture tiling scale.

### Emissive Color
Self-lit color.

### Emissive Multiplier
Intensity.

### Glossiness
Specular sharpness.

### Specular Color
Specular tint/intensity vector.

### Environment Map Scale
Cubemap/reflection strength.

### Alpha
Overall material transparency.

### Refraction Strength
Distortion amount for refractive shader modes.

### Grayscale To Palette Scale
Palette-remapping parameter for supported shaders.

## Alpha

### NiAlphaProperty
Legacy/parallel alpha-test/blend property controlling transparency mode.

### Alpha blending
Smooth transparency.

### Alpha testing
Binary cutoff transparency useful for foliage/fences.

### Alpha threshold
Cutoff value.

### Sort adjustment
Transparent geometry render order issues.

### Alpha hash/dither
Modern renderer-specific alternatives not part of vanilla NIF semantics unless framework adds them.

## Vertex data

### Vertex position
XYZ coordinate.

### Vertex normal
Surface direction used for lighting.

### Tangent
Tangent-space vector for normal mapping.

### Bitangent
Derived/explicit tangent-basis companion.

### UV coordinate
Texture coordinate.

### Vertex color
RGBA per-vertex data.

### Vertex alpha
Alpha component used when flags enable it.

### Index buffer
Triangle vertex indices.

### Bounds
Bounding sphere/box used for visibility/culling.

### Bad bounds
Object can pop/disappear because geometry lies outside recorded bounds.

## Other useful blocks

### NiStringExtraData
Named string metadata used by engine/tools/frameworks.

### BSXFlags
Root-level behavior flags influencing animation/collision/havok/etc.

### NiControllerManager
Animation controller manager.

### NiControllerSequence
Sequence of NIF-side animation controllers.

### NiTransformController
Animates transforms.

### NiFloatController
Animates float property.

### NiAlphaController
Animates alpha.

### NiTextKeyExtraData
Timed animation text keys/events in NIF animation workflows.

### BSInvMarker
Inventory-model rotation/zoom marker.

### BSBehaviorGraphExtraData
Behavior graph metadata on actor/skeleton NIFs.

### BSFurnitureMarkerNode
Furniture interaction marker.

### BSConnectPoint::Parents / Children
Attachment metadata for modular/connected objects.

## Diagnostics

### Purple texture
Missing/unresolved texture path.

### Black mesh
Shader/material/normal/cubemap/lighting mismatch.

### Invisible mesh
Alpha flags, shader type, missing geometry, bounds, skinning or culling.

### Exploding skin
Bad weights/bone transforms/partition/skeleton mismatch.

### Wrong reflection
Cubemap or environment-mask slot/flags incorrect.

### Flat surface
Normal map missing/incorrect encoding or shader flags don't use it.

### No parallax
Height map slot/type/renderer support mismatch.

### Texture shimmer
Mipmaps/normal/tangent/anisotropic sampling issue.

### Mesh pop
Bad bounds/LOD/controller/visibility state.

## Authoring rules

1. Preserve originals before NIF round trips.
2. Treat shader type and flags as one coherent material contract.
3. Texture slot meaning depends on shader.
4. Recalculate/validate tangents and normals after topology changes.
5. Morph/TRI meshes require stable vertex order/topology.
6. Skinned shapes require matching skeleton and partitions.
7. Collision blocks are independent from visible shader geometry.
8. Validate in game under target renderer, not only NifSkope.

## Sources

- NifSkope: https://github.com/niftools/nifskope
- PyNifly/Nifly: https://github.com/BadDogSkyrim/PyNifly
- BethesdaLibrary NIF/material docs: https://github.com/BadDogSkyrim/BethesdaLibrary
