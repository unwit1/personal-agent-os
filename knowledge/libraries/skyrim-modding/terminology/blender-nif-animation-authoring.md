# Skyrim Modding Terminology — Blender, NIF, Skeleton, and Animation Authoring

Imported: 2026-09-24
Status: sourced deep-ingestion pass 9

## Modern Blender tooling

### Blender
General-purpose open-source 3D creation package commonly used for Skyrim mesh, rig, animation and asset authoring.

### PyNifly
Blender addon importing/exporting Bethesda NIFs and related animation/skeleton data, using the Nifly library from the BodySlide/Outfit Studio ecosystem.

### Nifly
Native library used by BodySlide/Outfit Studio and PyNifly to read/write Bethesda NIF data.

### Blender scene
Authoring workspace containing meshes, armatures, materials and animation data before export.

### Armature
Blender skeleton object containing bones used to rig/skinning meshes.

### Pose bone
Blender representation of a bone's animated pose transform.

### Rest pose
Base skeleton transform from which animation/skinning is evaluated.

### Bind pose
Pose/matrices associated with mesh-to-skeleton skin binding.

### Bone hierarchy
Parent/child relationship among bones.

### Bone roll
Orientation of a bone's local axes; incorrect roll can create unexpected rotations during export/animation.

### Vertex group
Blender group storing weights tying vertices to a named bone.

### Weight paint
Blender mode for editing bone influence weights.

### Normalized weights
Vertex bone influences adjusted to sum to the expected total.

### Unweighted vertex
Skinned mesh vertex with no valid bone influence, potentially causing export/runtime deformation problems.

### Armature modifier
Blender modifier binding mesh deformation to an armature.

## NIF authoring

### NIF import
Converting Bethesda scene data into Blender objects/materials/skeleton representation.

### NIF export
Serializing authored Blender data back into Skyrim-compatible NIF structures.

### Round-trip loss
Information a tool may not preserve perfectly when importing and re-exporting an existing NIF. Always compare output for complex/specialized assets.

### Connect point
Bethesda/NIF attachment metadata used by some equipment/weapon/animation/display systems.

### Furniture marker
NIF/game data controlling interaction position/animation semantics for furniture.

### Collision mesh
Geometry exported as Havok collision rather than visible rendering.

### Shader translation
Mapping Blender material values/textures into Bethesda shader properties/flags.

### BSShaderTextureSet
NIF structure holding texture paths for Bethesda shader properties.

### BSTriShape
Skyrim SE renderable triangle-mesh block.

### NiTriShape
Older Gamebryo geometry block common in LE-era files.

### Skin instance
NIF structures associating mesh geometry with bones and skin transforms.

### Skin partition
Skyrim-optimized subdivision of skinned geometry according to bone/partition limits.

### Dismember/body partition
Partition metadata associated with body/equipment slot visibility and skinning.

### NIF node name
String identity used by engine/mod frameworks; changing node names can break attachments, animation, physics or display logic.

### Transform bake
Applying object transforms into geometry before export so scale/rotation do not remain unexpectedly in object hierarchy.

### Negative scale
Mirrored/negative transform that can invert normals/winding or produce export issues if not properly applied.

## Mesh topology

### Topology
Vertex/edge/face structure of a mesh.

### Vertex order
Ordering of vertices in exported geometry. Morph/TRI systems often require exact topology/order correspondence.

### Triangulation
Converting polygon faces to triangles before/at export.

### Degenerate triangle
Triangle with zero/nearly-zero area that can create rendering/collision issues.

### Non-manifold geometry
Mesh edges/faces that do not form a clean manifold surface; may or may not be valid depending on asset purpose.

### Duplicate vertex
Overlapping separate vertices; can affect normals, seams, morphs and performance.

### Weld
Merging appropriate coincident vertices.

### Hard edge
Normal split producing a sharp shading transition.

### Smooth shading
Interpolated vertex normals across connected faces.

### Tangent basis
Normal/tangent/bitangent coordinate system required for normal mapping.

## Animation authoring

### Keyframe
Stored transform/value at a specific animation time.

### F-curve
Blender curve representing animation channel over time.

### Action
Blender animation clip container.

### NLA
Nonlinear animation editor/system combining actions/tracks.

### Animation export
Converting Blender keyframed skeletal motion to Bethesda/Havok animation data.

### HKX import/export
PyNifly functionality for Bethesda animation/skeleton I/O.

### Animation project
Behavior-side relationship between exported clip and character/project event/binding data.

### Root bone
Top-level bone whose motion may represent actor/root motion.

### Root motion
Translation/rotation intended to move the actor through the world.

### In-place animation
Animation whose root stays approximately stationary and relies on game movement.

### Animation annotation
Timed text/event metadata associated with exported animation.

### Looping animation
Clip whose end transitions cleanly back to start.

### Additive animation
Animation representing deltas layered over another pose/animation.

### Retargeting
Transferring animation between skeletons with compatible semantic bones but possibly different proportions/structure.

### Skeleton compatibility
Requirement that an animation's expected bone names/hierarchy exist in the runtime skeleton.

## Authoring pipelines

### High-poly source
Detailed mesh used for sculpting/baking.

### Low-poly game mesh
Runtime-appropriate optimized mesh.

### Normal bake
Generating normal map from high-poly-to-low-poly surface differences.

### UV unwrap
Mapping 3D mesh surface into 2D texture coordinates.

### UV island
Connected region in UV space.

### Texel density
Texture resolution per unit of model surface.

### LOD authoring
Creating lower-detail model variants for distant rendering rather than relying only on automatic simplification.

### Collision proxy
Simplified collision geometry separate from visual mesh.

## Diagnostic rules

1. Keep original NIFs before import/export round trips.
2. Morph-capable meshes require stable topology/vertex order relative to TRI data.
3. Rigging issues may originate in bone hierarchy/rest pose/weights, not the animation itself.
4. Apply intended object transforms before export and validate scale/unit conventions.
5. Node names are API-like identifiers in many Skyrim systems; do not rename casually.
6. Visible geometry, skin partitions, body slots and collision are separate data layers.
7. A Blender material preview does not prove Skyrim shader flags/texture slots are correct.
8. Animation export does not add behavior events/state transitions automatically.

## Sources

- PyNifly upstream: https://github.com/BadDogSkyrim/PyNifly
- PyNifly developer guide: https://github.com/BadDogSkyrim/PyNifly/blob/main/DEVELOPERS.md
- NifSkope: https://github.com/niftools/nifskope
- BodySlide/Outfit Studio: https://github.com/ousnius/BodySlide-and-Outfit-Studio
