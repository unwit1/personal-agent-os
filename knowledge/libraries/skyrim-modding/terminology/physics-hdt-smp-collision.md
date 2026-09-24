# Skyrim Modding Terminology — Physics, Havok, HDT-SMP, Collision, and Skeleton Integration

Imported: 2026-09-24
Status: sourced encyclopedia pass 3

This module covers runtime skinned-mesh physics and distinguishes it from Skyrim's ordinary Havok rigid-body physics, animation, skeleton weighting, and static NIF collision.

## Core physics concepts

### Havok
Physics/middleware technology used by Skyrim for rigid-body simulation, collision, animation behavior and related systems.

### Rigid body
Physics object treated as a mostly non-deforming body with mass, shape, velocity and collision response.

### Constraint
Physics relationship limiting relative movement between bodies, such as hinge/ball/socket-like restrictions.

### Collision shape
Geometric representation used for physics collision tests.

### Collision layer
Classification controlling which categories of physics objects interact.

### Kinematic body
Physics object driven by animation/transforms rather than fully simulated dynamics, while still participating in collision.

### Dynamic body
Physics object whose motion is simulated from forces/constraints/collisions.

### Static collision
Non-moving collision geometry used by environment/world objects.

### Convex collision
Collision representation based on convex geometry, generally cheaper/more stable than arbitrary concave collision.

### Concave collision
Collision shape with inward regions; often represented with specialized mesh/static collision structures rather than one convex hull.

### Physics timestep
Amount of simulated time advanced per physics step.

### Substep
Additional physics simulation step within one rendered/game update.

### Solver iteration
Repeated constraint-solving pass used to improve physical stability/accuracy.

### Simulation instability
Explosive/jittering/nonphysical movement caused by bad constraints, extreme timestep, penetrations, scale issues or numerical instability.

### Tunneling
Fast-moving object passes through collision because discrete simulation misses the contact.

## Skyrim NIF collision

### bhk block
Family of Havok-related NIF blocks representing collision objects, shapes, rigid bodies and constraints.

### bhkCollisionObject
NIF collision attachment connecting scene geometry/nodes to Havok collision data.

### bhkRigidBody
Havok rigid-body representation stored in NIF data.

### bhkShape
Generic family/base terminology for Havok collision shapes in NIFs.

### Collision material
Physics material controlling friction/restitution/surface behavior and potentially sound/impact associations.

### Collision filter
Layer/group data controlling what a collision object can interact with.

### Ragdoll
Physics simulation of an actor skeleton after/dependent on death/knockdown behavior.

### Ragdoll bone
Skeleton bone participating in actor ragdoll rigid-body/constraint setup.

## HDT-SMP / FSMP

### HDT-SMP
Skinned Mesh Physics framework lineage for simulated cloth/hair/body accessories and other skinned-mesh movement in Skyrim.

### Faster HDT-SMP / FSMP
Actively maintained HDT-SMP continuation for Skyrim SE/AE/VR, providing skinned-mesh physics and modern performance/tooling improvements.

### SMP
Common shorthand for skinned-mesh physics framework/configuration.

### SMP mesh
Skinned NIF configured so selected bones/vertices participate in SMP-driven movement.

### Physics XML
Configuration describing SMP bones/nodes, constraints, collision shapes, parameters and interactions.

### DefaultBBPs.xml
Common historical/configuration entry point pattern used to associate meshes/nodes with HDT-SMP configuration; exact conventions vary by package/version.

### Config path
Reference from mesh/framework configuration to the XML that defines physics behavior.

### Bone
Skeleton transform influenced by animation and potentially driven/modified by SMP simulation.

### Physics bone
Bone included in SMP simulation configuration.

### Virtual ground/body collision
Collision representations used so simulated cloth/hair does not freely pass through body/world shapes.

### Capsule
Common simplified collision primitive used around limbs/body parts.

### Sphere
Simple collision primitive used for body/physics collision.

### Plane
Collision primitive representing an infinite/large flat boundary in applicable physics systems.

### Collision group
Grouping/mask system controlling which SMP objects collide.

### Self-collision
Simulated mesh/bones collide with other parts of the same physics object.

### Inter-object collision
Two separate SMP objects interact through configured collision.

### Constraint stiffness
Strength resisting deviation from desired relation between simulated nodes/bones.

### Damping
Parameter reducing oscillation/velocity over time.

### Gravity
Acceleration applied to simulated physics objects.

### Wind
Environmental/engine-driven influence affecting supported SMP simulations.

### Mass
Simulation mass parameter influencing acceleration and collision response.

### Drag
Velocity resistance controlling movement decay.

### Max linear/angular velocity
Safety/stability limit restricting extreme physics speeds.

### Penetration
Collision objects overlap/intersect, potentially causing explosive solver corrections.

### Physics reset
Reinitialize/reload SMP state for an object/framework after configuration or scene changes.

### smp reset
Console/runtime command family used by FSMP to reset/reload physics state, depending on current command set.

### smp report
FSMP diagnostic command described by upstream docs to validate/report physics configuration across the load order.

### SMP Modder Guide
Upstream FSMP author documentation for XML, mesh setup and schema validation.

### XSD
XML Schema Definition used by FSMP tooling/docs to define valid XML structure.

### Schematron
Rule-based XML validation schema used for semantic validation beyond basic XSD structure.

### DynamicHDT
FSMP-associated dynamic control/API layer allowing physics behavior to be influenced at runtime.

### DynamicHDT Papyrus API
Papyrus-facing interface for controlling supported physics features from scripts.

### smp_replay
FSMP development/benchmark tool for replaying/benchmarking physics behavior outside ordinary gameplay workflows.

## Physics/skeleton integration

### XPMSSE
**Expansion:** XP32 Maximum Skeleton Special Extended.  
Widely used extended character skeleton providing extra nodes/bones used by weapon positioning, animations and physics-equipped assets.

### Skeleton node requirement
Physics mesh/config references named bones/nodes that must exist in the active skeleton.

### Missing bone
Configured/skinned bone absent from skeleton, causing missing deformation, warnings, or physics failure.

### Bone hierarchy
Parent/child relationship of skeleton nodes. Physics configuration may depend on expected hierarchy and transforms.

### Rest pose
Base skeleton/mesh pose from which animation/physics transforms are applied.

### Skin weights
Vertex influences binding visible geometry to bones.

### Weight painting
Authoring/editing those influences.

### Physics-only bone
Bone added primarily for simulated deformation rather than vanilla animation.

### Animation-driven bone
Bone ordinarily positioned by animation graph/keyframes.

### Mixed animation/physics control
Bone chain transitions between animation-driven anchors and physics-driven descendants.

## Performance and diagnostics

### Physics CPU cost
SMP simulation is substantially CPU-sensitive because bones/collisions/constraints must be solved over time.

### Collision complexity
Number/type of collision objects and interactions; higher complexity increases solver workload.

### Physics object count
Number of active SMP simulations, often scaling cost with visible actors/equipment.

### Off-screen physics
Whether simulation continues for objects not currently visible/nearby; configurable behavior can affect performance.

### Physics culling
Skipping/reducing simulations based on distance/visibility/state.

### Jitter
Rapid small oscillations from constraints/collision/timestep instability.

### Explosion
Simulation diverges dramatically, sending vertices/bones far from expected positions.

### Frozen cloth/hair
Simulation is not updating, often due to missing framework/config/bones or object lifecycle state.

### Stretching to origin
Vertices stretch toward world/origin/incorrect bone because a required bone transform is absent/invalid.

### Physics crash
Native crash involving SMP code/config/mesh data. Diagnose runtime DLL version, PDB/symbol stack, XML validity, skeleton, mesh and reproduction rather than assuming all SMP crashes are framework bugs.

## Diagnostic rules encoded for Agent OS

1. Distinguish ordinary NIF collision from SMP skinned-mesh physics.
2. An animation issue can look like a physics issue when anchor bones receive unexpected animation transforms.
3. Verify skeleton node names/hierarchy before tuning XML parameters.
4. Validate XML with current FSMP schemas/tools before guessing at solver settings.
5. Physics exploding is usually a stability/configuration symptom, not evidence that more stiffness is always needed.
6. High FPS/timestep settings can interact with physics; record Display Tweaks/Havok configuration.
7. Test one physics asset/actor at a time when isolating CPU cost or crashes.
8. PDB/symbolized native crashes plus reproducible asset conditions are stronger evidence than “FSMP appears in the stack.”
9. Treat generated BodySlide meshes and physics XML as a coupled asset set where the physics rig depends on expected bones/topology.
10. Record FSMP version and Skyrim runtime because native compatibility evolves.

## Sources

- Faster HDT-SMP upstream: https://github.com/DaymareOn/hdtSMP64
- Faster HDT-SMP Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/57339
- NifSkope upstream: https://github.com/niftools/nifskope
- BodySlide/Outfit Studio: https://github.com/ousnius/BodySlide-and-Outfit-Studio
