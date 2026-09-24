# Skyrim Modding Terminology — Interior Optimization, Room Bounds, Portals, and Occlusion

Imported: 2026-09-24
Status: sourced deep-ingestion pass 24

## Interior optimization model

### Room Bound
Editor/runtime volume defining one logical interior visibility room.

### Portal
Rectangular connection between adjacent Room Bounds used by the engine to determine which neighboring rooms may be visible through an opening.

### Portalized interior
Interior cell whose Room Bounds and Portals partition geometry for visibility culling.

### Visibility set
Rooms/references considered potentially visible from the current camera room through connected portals.

### Occlusion
Skipping geometry that should not be visible because room/portal or occlusion data proves it is blocked.

### Frustum
Camera view volume; portal visibility is further constrained by the camera frustum.

### Room membership
Placed references/geometry associated spatially with one Room Bound.

### Unbound geometry
Reference outside intended Room Bounds and therefore potentially rendered when it should be culled or disappear unexpectedly.

### Overlapping Room Bounds
Room volumes intersect incorrectly, creating ambiguous room membership and visibility.

### Portal plane
Opening surface between rooms; should match actual doorway/window opening and sit between corresponding bounds.

### Portal normal
Portal orientation used by visibility traversal; incorrect orientation can contribute to one-sided/incorrect visibility.

### Portal chain
Sequence of visible connected rooms through multiple portals.

### Portal leak
Portal exposes area that should remain occluded because its dimensions/orientation are too broad.

### Portal clipping
Geometry visibly disappears because portal/bounds are too narrow or misaligned.

### Room marker
CK visualization/editor object used while authoring bounds/portals.

## Occlusion helpers

### Occlusion Plane
Invisible plane used by engine to cull geometry hidden behind it.

### Occlusion Box
Volume used to suppress rendering of obscured references.

### Manual occluder
Author-placed occlusion object complementing room/portal visibility.

### Large occluder
Best candidate such as thick wall/building; tiny detailed occluders can create overhead/artifacts.

### Occlusion false positive
Visible object culled even though player can actually see it.

### Occlusion false negative
Hidden object still rendered.

## Multibounds

### MultiBound
Optimization structure associating objects with a volume for culling/visibility management.

### MultiBound node
Runtime/editor grouping relationship between references and optimization bound.

### MultiBound room
Special optimization grouping used in some Bethesda cells.

### Bound association
Reference assigned to relevant MultiBound/room.

### Orphaned bound reference
Object remains tied to removed/moved bound and disappears incorrectly.

## Portals and load doors

### Portal opening
Architectural opening between rooms; not the same as a teleport Door reference.

### Load Door
Door whose activation teleports to another cell.

### Same-cell door
Animating door inside one interior can sit in a portal opening; portal remains visibility connection independent of door animation.

### Closed-door visibility
Portal system does not automatically infer every opaque animated door state unless authored/system-supported; test actual room visibility.

### Doorway seam
Portal/bound misalignment causes popping at threshold.

## Cell authoring workflow

1. Build interior geometry.
2. Establish Room Bounds covering navigable/visible architectural spaces.
3. Create Portals exactly across openings between adjacent rooms.
4. Ensure reference membership is correct.
5. Test from both sides and diagonally through portals.
6. Add occlusion planes/boxes only where useful.
7. Validate lights, FX and large statics do not pop.
8. Test first-person/third-person/free camera and high FOV.
9. Recheck after moving walls/doorways.

### Show portals/bounds
CK render-window visualization mode used while authoring optimization geometry.

### Portal snap
Aligning portal to architectural opening/adjacent bounds.

### Room merge
Combining over-partitioned rooms where portal overhead/artifacts exceed benefit.

### Room split
Separating large complex room to reduce visible object set.

## Lighting interaction

### Light room membership
Light/reference may disappear or stop affecting geometry if portal/room relationships cause it to be culled.

### Shadow caster across portal
Dynamic shadow/light can behave differently across room boundaries; test rather than assuming one large light crosses everything cleanly.

### FX pop
Particles/fog/visual effects can disappear abruptly if their reference origin/bounds fall outside currently visible room even while particles extend through opening.

## Common failures

### Objects disappear near doorway
Portal too small, room assignment wrong, bounds overlap/gap, reference assigned to wrong optimization structure.

### Entire room visible through wall
Missing/misaligned portal/room or geometry not associated with intended bound.

### Light pops
Light source culled by room logic while its lit surfaces remain visible.

### Particle cut-off
Emitter/reference leaves visibility set even though particles visually extend into camera room.

### Performance unchanged
Interior not actually partitioned effectively, portals expose most rooms, or dominant cost is scripts/AI/shadows rather than geometry draw.

### CTD after cell optimization edit
Malformed/invalid optimization data or unrelated cell record conflict; compare pre-edit and inspect CK/xEdit errors.

## Compatibility

### Interior overhaul conflict
Two mods move walls/doors/room geometry but only one supplies matching room/portal setup.

### Lighting overhaul conflict
Lighting mod edits CELL/LGTM/lights while architecture mod changes room/portal layout.

### Static replacer
Mesh-only replacer normally leaves portal geometry intact unless collision/bounds significantly differ.

### Cell merge patch
Patch may need both object placement and optimization references; copying only visible statics can leave stale room/portal data.

## Diagnostic rules

1. If disappearance occurs at a camera threshold/doorway, inspect portals/bounds before texture/NIF.
2. Room Bounds/Portals optimize visibility, not AI pathfinding; navmesh is separate.
3. Load doors and visibility portals are separate systems.
4. Effects/lights need testing because their visual extent can exceed their reference origin's room.
5. Architecture patches must reconcile optimization data when openings/walls change.
6. Avoid over-partitioning; too many tiny rooms/portals can increase authoring complexity and popping risk.
7. Test with free camera and high FOV to expose visibility mistakes.

## Sources

- Creation Kit Wiki interior optimization and Render Window documentation
- Creation Kit Wiki Cell View Window: https://ck.uesp.net/wiki/Cell_View_Window
- Creation Kit Wiki video/tutorial index includes room/lighting optimization workflows: https://ck.uesp.net/wiki/Video_Tutorials
