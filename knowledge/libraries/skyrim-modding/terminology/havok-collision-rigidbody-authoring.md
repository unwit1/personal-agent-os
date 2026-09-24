# Skyrim Modding Terminology — Havok Collision, Rigid Bodies, and NIF Physics Authoring

Imported: 2026-09-24
Status: sourced deep-ingestion pass 24

## Havok collision in Skyrim NIFs

### bhkCollisionObject
NIF collision object linking scene node to Havok rigid body.

### bhkRigidBody
Havok rigid body containing collision shape, mass, motion system, quality/material and physical parameters.

### bhkRigidBodyT
Rigid body variant with transform stored in body rather than only parent node.

### bhkShape
Base family of collision shapes.

### bhkBoxShape
Box collision primitive.

### bhkSphereShape
Sphere primitive.

### bhkCapsuleShape
Capsule primitive, common for elongated/simple collision.

### bhkConvexVerticesShape
Convex hull collision from vertex set.

### bhkMoppBvTreeShape
MOPP acceleration structure wrapping complex collision.

### bhkCompressedMeshShape
Compressed triangle-mesh collision format common in Skyrim SE statics.

### bhkCompressedMeshShapeData
Collision mesh data/chunks/material indices.

### Collision layer
Havok layer determining what the object collides/interacts with.

### Collision filter info
Packed collision-group/layer flags.

### Havok material
Material ID influencing footstep, impact and physical properties.

### Motion system
Rigid-body behavior type describing static, keyframed, dynamic, box/sphere-character-like movement.

### Quality type
Havok simulation quality/continuous collision mode.

### Mass
Rigid body mass.

### Inertia
Resistance to rotational acceleration.

### Center of mass
Point around which rigid-body motion is calculated.

### Linear damping
Reduces translational velocity.

### Angular damping
Reduces rotational velocity.

### Friction
Resistance to sliding at contact.

### Restitution
Bounciness.

## Static vs dynamic collision

### Static collision
Collision never simulated as moving; appropriate for architecture/terrain/static world geometry.

### Keyframed collision
Transform controlled externally/animation while still participating in collision.

### Dynamic collision
Havok simulation controls movement after forces/gravity/contact.

### MovableStatic / MSTT
World form for moving/animated static-like assets; collision/motion setup must match intended runtime behavior.

### Activator collision
ACTI object can be animated/scripted and may require keyframed collision.

### Furniture collision
FURN NIF combines visible geometry, interaction markers and collision.

### Animated collision
Collision changes/moves with Gamebryo animation; keyframed/body hierarchy must be authored correctly.

## Collision layers

### L_STATIC
General static-world collision layer.

### L_ANIMSTATIC
Animated static collision layer.

### L_CLUTTER
Movable clutter/object layer.

### L_WEAPON
Weapon collision.

### L_PROJECTILE
Projectile collision.

### L_BIPED
Actor/body collision family.

### L_NAVCUT
Collision primitive used to dynamically cut navmesh traversal.

### L_TRIGGER
Trigger-volume collision layer.

### Layer mismatch
Asset physically exists but engine interaction differs because collision shape is on inappropriate layer.

## Convex vs concave

### Convex collision
Any two points inside shape connect without leaving it; efficient stable Havok shape.

### Concave geometry
Complex mesh with cavities/interior angles; cannot be represented accurately by one convex hull.

### Convex decomposition
Split complex concave object into several convex shapes.

### Triangle mesh collision
Exact-ish surface triangles; useful for architecture but heavier and generally not ideal for freely dynamic clutter.

### Collision proxy
Simplified shape used instead of render mesh.

### Over-detailed collision
Too many triangles/chunks causing physics/pathing/performance issues with little gameplay benefit.

### Under-detailed collision
Player/projectiles clip into visible geometry or stand on invisible broad hulls.

## Collision generation/editing

### Chunk
Subsection of compressed mesh collision with material/triangle data.

### Material per chunk
Different collision areas can yield wood/stone/etc. footsteps/impacts.

### Collision export
Blender/NIF authoring pipeline creating bhk shapes from authoring meshes.

### Copy collision
NifSkope workflow reusing known-good collision structure from similar object.

### Collision transform
Shape position/rotation/scale relative to render hierarchy.

### Scale mismatch
Visible mesh and collision use different effective scale because transforms not applied/baked correctly.

### Havok scale
Bethesda/Havok unit conversion assumptions handled by export tools; manual arbitrary scaling can break physics.

## Character interaction

### Character controller
Special engine collision representation for Actors.

### Capsule
Actor movement often approximated by capsule-like collision rather than visible body mesh.

### Ground contact
Character controller detects walkable surface.

### Step height
Maximum ledge height actor can traverse without jumping.

### Slope
Surface angle considered walkable.

### Collision snag
Detailed/protruding collision catches player/AI.

### Invisible wall
Collision extends beyond visible mesh.

### Falling through
Missing/gapped collision or layer/filter prevents actor-ground contact.

## Projectiles and impacts

### Raycast
Physics query along line used by engine/mods for LOS/target/collision tests.

### Sweep test
Move shape through space and report collision.

### Projectile hit
PROJ intersects collision shape/layer.

### Impact material
Havok material selects IPDS/IPCT effects and sounds.

### Arrow sticking
Projectile behavior relies on collision surface and material response.

## Physics objects

### Clutter
Dynamic objects with mass/inertia.

### Havok settling
Objects simulated after cell load until resting.

### Exploding clutter
Bad mass/inertia/overlap spawns causing high forces and objects launching.

### Initial overlap
Two collision shapes start intersecting; solver forces them apart.

### Sleeping rigid body
Havok stops simulating resting object until disturbed.

### Wake
Force/contact reactivates simulation.

### Constraint
Joint linking bodies with limited relative movement.

## Navmesh interaction

### Collision vs navmesh
Collision physically blocks actor; navmesh determines AI path. One can disagree with the other.

### Dynamic navcut
L_NAVCUT blocks navmesh at runtime for small inserted obstacles.

### Static obstacle
Should usually have navmesh authored around it rather than relying on collision alone.

### AI collision failure
NPC path chooses route through collision because navmesh says traversable.

## Diagnostic rules

1. Visual mesh and collision mesh are separate assets/data.
2. Wrong footsteps/impacts often indicate wrong Havok material, not audio record.
3. AI getting stuck can be navmesh/collision disagreement.
4. Dynamic clutter should use suitable simple/convex collision rather than giant triangle meshes.
5. Initial overlaps cause "exploding" physics even when scripts are absent.
6. L_NAVCUT is a compatibility tool for appropriate small runtime/static additions, not a replacement for all navmesh work.
7. Apply/bake intended transforms before exporting collision.
8. Test projectiles, player movement and NPC movement; they can use different collision/filter paths.

## Sources

- NifSkope/NifTools: https://github.com/niftools/nifskope
- PyNifly: https://github.com/BadDogSkyrim/PyNifly
- Creation Kit Wiki community navcut notes: https://ck.uesp.net/wiki/User:DavidJCobb
- Unofficial Material Fix ecosystem for Havok-material correction
