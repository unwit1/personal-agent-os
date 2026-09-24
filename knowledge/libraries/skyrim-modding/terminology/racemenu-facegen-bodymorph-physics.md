# Skyrim Modding Terminology — RaceMenu, FaceGen, BodyMorph, and Physics

Imported: 2026-09-24
Status: sourced deep-ingestion pass 3

## NPC appearance and FaceGen

### FaceGen
Bethesda's generated NPC head system. NPC face appearance is not defined by plugin records alone; generated face mesh/tint assets can be required for the in-game result to match the NPC_ record.

### FaceGeom
Generated NPC head mesh output path under `meshes\actors\character\FaceGenData\FaceGeom\<plugin>\<formid>.nif`.

### FaceTint
Generated NPC face tint texture output path under `textures\actors\character\FaceGenData\FaceTint\<plugin>\<formid>.dds`.

### FaceGen export
Creation Kit operation that generates NPC face mesh/tint assets for selected actors. Historically associated with Ctrl+F4 workflows.

### Dark face bug
Symptom where an NPC's loaded head appearance does not match expected generated/plugin data, commonly involving mismatched NPC record data and FaceGen mesh/tint assets. Treat it as an appearance-data consistency problem, not merely "a texture bug."

### HeadPart
Form controlling modular head components such as hair, eyes, brows, scars, facial hair, or other head geometry.

### HeadPart race/gender compatibility
Head parts can be constrained by race and sex/gender metadata. Runtime frameworks may relax some selection rules, but ordinary NPC/head data still needs compatible parts.

### Tint mask
Texture/mask layer used in face tinting/overlays. FaceGen output and RaceMenu overlays can involve related but distinct systems.

### NPC head mesh
Generated/rendered NIF for an NPC head. It can carry head-part geometry and nodes required by other systems.

### FaceGen node pruning
Generated FaceGen meshes may omit skeleton/bone nodes that are not referenced by mesh data. This can matter for physics/constraints attached to head parts.

## RaceMenu / SKEE / NiOverride

### RaceMenu
SKSE-based character creation/appearance framework by expired6978. Beyond the menu UI, its native SKEE/NetImmerse Override layer supplies overlays, morphs, BodyGen, transforms, sculpting, and APIs consumed by other mods.

### SKEE
Native plugin/runtime component used by RaceMenu. Source exposes systems for overlays, body morphs, BodyGen, transforms, sculpting, and serialization.

### NetImmerse Override / NiOverride
RaceMenu/SKEE system for applying node, transform, shader, overlay, and morph-related runtime changes to actor/mesh data.

### Overlay
Runtime-applied texture/decal-like appearance layer used for body, hand, feet, or face overlays.

### Face overlay
Overlay applied to face/head rendering. Face overlays are not the same asset pipeline as CK-generated FaceTint files.

### BodyMorph
RaceMenu/SKEE runtime system that applies BodySlide-compatible morph deltas to actor meshes.

### Morph name
Named BodySlide/RaceMenu morph target, such as one slider-defined vertex-delta channel.

### Morph key
Key/source identifying one contributor to a morph value. Multiple systems can contribute values to the same morph name and RaceMenu can combine/evaluate them.

### Actor morph state
Per-actor BodyMorph data stored by SKEE. RaceMenu source explicitly implements save/load serialization for actor morph maps.

### Morph cache
Runtime cache of TRI/morph vertex data used to avoid repeatedly parsing/rebuilding morph information.

### Morph memory limit
RaceMenu/SKEE setting controlling morph cache memory usage.

### GPU morph copy
RaceMenu/SKEE optimization path for applying/updating body morph geometry using GPU-copy-related behavior where supported.

### BodyGen
RaceMenu system for automatically assigning BodyMorph templates to NPCs based on BodyGen configuration.

### BodyGen template
Named combination/range of morphs that BodyGen can evaluate for actors.

### BodyGen morph selector
Selection/range logic choosing values for one or more morphs inside a BodyGen template.

### BodyGenData
RaceMenu data directory/configuration used to associate NPCs/groups with BodyGen templates.

### Sculpt
RaceMenu head-sculpting system for vertex-level character face changes beyond ordinary vanilla slider parameters.

### Head export
RaceMenu feature that can export head-related data/assets independently of the Creation Kit FaceGen workflow.

### Equippable transforms
RaceMenu/SKEE runtime transform overrides applied in association with equipped items/nodes.

### BodyMorph serialization
SKEE source contains explicit Save/Load methods for morph data, so established-save appearance behavior can differ from a new game even when meshes/presets are unchanged.

## TRI and morph assets

### TRI file
Morph-target data file containing vertex deltas used for facial/body morphing workflows.

### Vertex delta
Stored per-vertex displacement used to transform a base mesh toward a morph target.

### Morph-capable mesh
Mesh whose topology/names/data match the TRI/morph information expected by the runtime.

### Topology mismatch
Mismatch in vertex/order/shape data between a mesh and its morph data. Can cause morph failure, deformation, or invalid results.

### Build Morphs
BodySlide workflow that generates morph support for built meshes, usually including TRI data required by RaceMenu BodyMorph.

### Static BodySlide build
Final NIF shape baked from a preset without relying on per-actor runtime BodyMorph changes.

### Runtime morph
Actor-specific morph applied in game by RaceMenu/SKEE rather than baked identically into every generated mesh.

## HDT-SMP / FSMP physics

### HDT-SMP
Skinned Mesh Physics framework family for cloth/hair/body/accessory physics on Skyrim 64-bit runtimes.

### Faster HDT-SMP / FSMP
Actively maintained continuation of HDT-SMP for Skyrim SE/AE/VR.

### SMP object
Mesh/node hierarchy currently managed by the SMP physics engine.

### SMP configuration
XML/config data describing physics bones, rigid/soft bodies, constraints, collisions, and mesh associations.

### Physics bone
Skeleton/node transform driven or constrained by SMP simulation.

### Kinematic object
Physics object whose movement is driven by animation/skeleton transforms and influences simulated objects rather than being freely simulated.

### Dynamic object
Physics-simulated object influenced by constraints, collisions, and forces.

### Constraint
Physics rule restricting relative motion between objects/bones.

### Collision shape
Geometry used by the physics simulation for contacts. It is separate from visual geometry and separate from ordinary Skyrim Havok world collision.

### Bullet Physics
Open-source physics library used by HDT-SMP/FSMP implementations for simulation/collision.

### Physics timestep
Simulation step interval. Changes to timestep strategy can affect stability/performance.

### SMP distance culling
Optimization that disables or reduces simulation for actors farther from the player.

### SMP FOV culling
Optimization restricting simulated NPCs by camera field-of-view/angle.

### SMP reset
Console/runtime command used by implementations to reload physics config/reinitialize objects. It is a diagnostic action and may not perfectly recreate every object/constraint.

### SMP node tree
Skeleton/scene-node hierarchy inspected by FSMP diagnostics when troubleshooting missing physics attachments or expected bones.

### Physics-enabled hair/headpart
Head asset containing expected SMP nodes/config relationships. FaceGen generation can remove unreferenced bones/nodes, which may break physics assumptions.

### Skeleton requirement
Physics-enabled meshes can depend on a skeleton containing specific bones/nodes. Skeleton overwrite conflicts can therefore present as physics failures.

### XML conflict
Multiple mods supplying physics configs for the same asset or path. This is an asset/config conflict, not a plugin-record conflict.

### Physics performance budget
Combined CPU/GPU cost of active simulated objects, collision pairs, constraints, and actor count. Performance diagnosis should identify object count and simulation scope rather than just "FSMP is slow."

## Diagnostic rules

1. A dark/head mismatch can involve NPC_ overrides, HeadParts, FaceGeom NIFs, FaceTint DDS files, runtime RaceMenu overlays, and asset priority. Inspect all relevant layers.
2. BodySlide preset files do not guarantee RaceMenu runtime morphs work. Check built morph-capable meshes/TRIs and SKEE morph state.
3. Because RaceMenu serializes actor morph state, compare new-game and established-save behavior before rebuilding everything.
4. BodyGen is actor-specific runtime generation, not merely a BodySlide batch build.
5. Physics failures require checking skeleton bones, mesh nodes, SMP XML/config, FSMP runtime, and asset overwrites.
6. A physics-enabled FaceGen/head asset may fail if required nodes are pruned or missing from generated head data.
7. Treat RaceMenu/SKEE and FSMP as native runtime plugins: exact runtime/SKSE compatibility still matters.

## Sources

- RaceMenu/SKEE BodyMorph implementation: https://github.com/expired6978/SKSE64Plugins/blob/master/skee64/BodyMorphInterface.h
- RaceMenu/SKEE main configuration/runtime code: https://github.com/expired6978/SKSE64Plugins/blob/master/skee64/main.cpp
- Creation Kit Wiki packaging notes / FaceGen asset paths: https://ck.uesp.net/wiki/File_menu
- Creation Kit Wiki Dark Face documentation: https://ck.uesp.net/wiki/Dark_Face_Bug
- Faster HDT-SMP upstream: https://github.com/TwistedModding/hdtSMP64
- HDT-SMP/FSMP historical VR/AE fork documentation: https://github.com/alandtse/hdtSMP64

## Provenance notes

RaceMenu/SKEE and physics implementations are native code and runtime-sensitive. Preserve exact versions in troubleshooting cases. Historic GitHub issues are useful as symptom/reproduction evidence, but individual issue conclusions are not automatically canonical.
