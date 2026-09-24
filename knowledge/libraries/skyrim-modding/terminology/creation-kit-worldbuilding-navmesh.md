# Skyrim Modding Terminology — Creation Kit Worldbuilding, Navmesh, Optimization, Locations, and Encounter Design

Imported: 2026-09-24
Status: sourced encyclopedia pass 3

This module expands the worldspace/cell glossary into practical level-design and compatibility concepts used by the Creation Kit.

## Creation Kit editing context

### Object Window
Creation Kit browser for base forms grouped by record category.

### Render Window
3D editor viewport used to place/edit references, landscape, navmesh and other spatial data.

### Cell View
Editor window listing cells and references, including exterior coordinates, ownership, Location, persistence and reference flags.

### Active File
Plugin receiving editor changes in the current Creation Kit session.

### Render Window selection
Placed reference/object currently selected for transform/property editing.

### Gizmo
Translation/rotation/scale manipulator in the editor.

### Snap to Grid
Placement option constraining transforms to grid increments, useful for modular kits.

### Snap to Angle
Rotation snapping for modular architecture.

### Drop to Ground
Editor operation placing selected references/navmesh vertices at detected surface height; effects/collision quirks can make results unreliable.

### Duplicate
Create a new form or reference based on an existing one; duplicating a base record creates a new identity, while copying a placed reference creates another instance.

## Cells and worldspaces

### Interior
Cell loaded as a self-contained indoor space.

### Exterior
Cell belonging to a worldspace grid.

### Wilderness cell
Unnamed exterior cell identified mainly by worldspace coordinates.

### Named exterior cell
Exterior cell with an EditorID/name for important locations.

### WorldSpace / WRLD
Exterior world container with cells, climate, map, water, LOD and other world-level data.

### Parent worldspace
Worldspace inheriting or relating to another worldspace for map/LOD/coordinate purposes.

### Fixed dimensions
Worldspace bounds/config limiting navigable/generated cell area.

### Land height
Terrain elevation stored in LAND data.

### LAND record
Cell terrain data containing height, textures, vertex color and related landscape information.

### Landscape
Editable terrain surface of an exterior worldspace.

### Landscape vertex
Grid point storing terrain elevation and other per-vertex data.

### Landscape texture
Ground material layer painted onto terrain.

### Landscape texture layer
One of multiple textures blended on cell terrain.

### Heightmap
Large-scale elevation dataset used to generate/shape worldspace terrain.

### Heightmap import
Creation Kit workflow generating landscape from an external heightmap.

### Cell border
Boundary between exterior cells. Terrain and navmesh continuity across borders requires special care.

### Water height
Cell/worldspace water-plane elevation.

### Default land height
Worldspace baseline terrain height used during generation/initialization.

### Map data
Worldspace information controlling map presentation/bounds/scale.

## References and spatial relationships

### Static / STAT
Non-animated base model typically used for architecture, rocks, clutter geometry and many world objects.

### Movable Static / MSTT
Static-like object type with runtime movement/behavior differences and eligibility for certain large-reference behavior.

### Activator / ACTI
Interactive world-object base capable of activation/scripts and other runtime logic.

### Marker
Invisible/editor-visible reference used as an anchor, target, spawn point or system helper.

### XMarker
Generic invisible marker.

### XMarkerHeading
Marker with meaningful position and facing orientation.

### MapMarker
Reference providing world/local map discoverable/travel metadata.

### Enable parent
Reference relationship where one reference's enabled state controls another.

### Enable state opposite
Child enable-state logic inverted relative to its parent.

### Linked Ref
Explicit reference-to-reference relationship.

### Linked Ref keyword
Keyword distinguishing the semantic purpose of one linked reference when multiple links exist.

### Activation parent
Reference relationship forwarding/controlling activation behavior.

### Ownership
Actor/faction ownership on cells/references/items used by crime/interaction systems.

### Location Ref Type
Keyword-like classification attached to a reference so Location/Story Manager/game systems can locate semantically important objects such as bosses, entrances, treasure, beds or other roles.

## Location system

### Location / LCTN
Hierarchical semantic area representing a place independent of raw cell boundaries.

### Parent Location
Location containing another Location in the location hierarchy.

### Location keyword
Keyword classifying location type/properties.

### Location Ref Type / LCRT
Classification identifying what role a reference plays within its Location.

### Location data
Runtime/quest/Story Manager information associated with a Location.

### Cleared Location
Location state marked cleared through encounter/quest systems.

### Boss LocRefType
Reference designated as the boss for a Location/encounter where applicable.

### Boss container
Container marked through location/reference typing for encounter reward logic.

### Entrance marker
Reference/type identifying a location entrance for quests/story systems.

## Encounter design

### Encounter Zone / ECZN
Record defining level-scaling, reset and combat/encounter behavior for cells/locations.

### Minimum level
Encounter-zone lower bound used when determining spawned/scaled enemy level.

### Maximum level
Encounter-zone upper bound where configured.

### Never Resets
Encounter-zone setting preventing ordinary reset behavior.

### Match PC Below Minimum
Encounter-zone option controlling behavior when player level is below zone minimum.

### Combat boundary
Encounter/AI behavior limiting pursuit or combat across configured spaces.

### Leveled actor marker
Placed reference using a leveled actor list so runtime selects an NPC/creature.

### Leveled item marker
Placed/reference/container relationship selecting loot from a leveled list.

### Spawn point
Reference/marker where a runtime-selected actor/object is created/placed.

### Ambush
Encounter setup delaying/revealing actor activation based on triggers/events.

### Trigger
Primitive/activator volume generating enter/leave/activation events.

### Trigger volume
Invisible collision/primitive volume used for scripted or engine interaction.

## Navmesh

### NAVM
Plugin record containing a navmesh.

### Navmesh
Walkable navigation geometry used by actor pathfinding.

### Navmesh vertex
Point defining navigation triangles.

### Navmesh triangle
Walkable polygon connecting three vertices.

### Navmesh edge
Triangle boundary; edge connectivity determines traversable adjacency.

### Edge link
Connection from a triangle edge to an adjacent triangle.

### Cell-border link
Finalized connection between navmeshes across exterior/interior boundaries/doors.

### Door triangle
Navigation triangle associated with a teleport door/link for pathfinding through load doors.

### Finalization
Creation Kit process calculating cross-cell/door navmesh links and required navigation metadata after editing.

### Finalize Cell Navmeshes
Editor command finalizing navigation data for a cell and its boundary relationships.

### Pathing test
Creation Kit/debug test checking whether an actor can find a path between selected positions.

### Navmesh island
Disconnected navigable region.

### Navmesh cut / NAVCUT
Runtime collision layer/primitive used to remove/block navigation through part of an existing navmesh without directly editing NAVM triangles.

### L_NAVCUT
Collision layer applied to suitable primitives/statics so they dynamically cut navmesh at runtime.

### Navcut strategy
Compatibility technique placing a navigation-cutting collision primitive around small added obstacles instead of overriding vanilla navmesh.

### Preferred path
Navmesh data encouraging actors to choose selected routes.

### Cover edge
Navmesh edge marked/evaluated for combat cover behavior.

### Find Cover Edges
Creation Kit navmesh operation analyzing edges for cover metadata.

### Navmesh deletion
Deleting a NAVM override. High-risk because other records/cell links can reference the original mesh.

### Navmesh replacement
Create/new navmesh strategy sometimes used instead of destructively editing/deleting existing mesh; identity and connection implications must be validated.

### Navmesh conflict
Two mods override same NAVM or alter connected spaces incompatibly.

### Navmesh seam
Disconnected/badly finalized boundary between adjacent navmesh areas/cells.

### Stuck NPC
Symptom where actor cannot navigate; possible causes include navmesh connectivity, package target, collision, door links, AI state or disabled references.

## Interior optimization

### Room Bound
Volume dividing an interior into visibility rooms for portal-based occlusion.

### Portal
Plane connecting Room Bounds and controlling which rooms are considered visible through an opening.

### Portalized interior
Interior cell whose visibility is partitioned by Room Bounds and portals.

### Room marker
Editor representation of a Room Bound.

### Portal alignment
Requirement that portal geometry correctly overlaps/connects adjacent room bounds and openings.

### Occlusion
Avoiding rendering objects not visible to the camera.

### Occlusion plane
Manual visibility/occlusion helper plane used to stop rendering geometry hidden behind large blockers.

### Occlusion box
Box-shaped occlusion volume used for visibility culling.

### Multibound
Engine/editor bounding construct used in some optimization/culling contexts.

### Visibility cell
Conceptual set of objects visible within portal/room system.

### Overdraw
Rendering surfaces that are later hidden by nearer geometry; excessive overdraw wastes GPU work.

### Light count debug
Creation Kit Render Window mode showing number of lights affecting objects.

### Render pass count
Editor debug display indicating rendering passes affecting an object.

## Landscape/world compatibility

### Landscape conflict
Multiple plugins modify same LAND record/cell terrain data; ordinary last-wins behavior can erase other terrain edits.

### Landscape seam
Visible height/texture discontinuity along cell borders.

### Landscape texture limit
Practical engine/editor constraint on number of landscape texture layers per terrain quad/cell region; exceeding supported usage can produce missing/black texture artifacts.

### Worldspace conflict
Mods change WRLD/cell/land/reference data in overlapping geographic areas.

### Location overhaul
Mod substantially changing architecture, references, navmesh, markers and encounter logic for an existing place.

### City overhaul patch
Compatibility plugin/assets reconciling overlapping city-space references/navmesh/doors/AI markers.

### Persistent-cell edit
Change to a worldspace's persistent cell records/references. These have broader reach than one temporary exterior cell.

### Temporary children group
Plugin grouping for ordinary cell reference children, contrasted with persistent/reference groups.

## Editor/runtime testing

### COC
Console command loading/teleporting directly to a named cell.

### COW
Console command teleporting to exterior worldspace coordinates.

### TAI
Console toggle AI command useful for isolating movement/AI behavior, but not a production fix.

### TCAI
Console toggle combat AI.

### TFC
Toggle free camera for visual inspection.

### TCL
Toggle collision; useful to inspect geometry/pathing but can alter test conditions.

### PCB
Purge cell buffers to encourage unloading/reloading during tests.

### New-game world test
Test without pre-existing saved reference/cell state.

### Cell-reset test
Allow/force relevant reset conditions to determine whether state is persistent or from current plugin defaults.

## Creation Kit Platform Extended

### CKPE
**Expansion:** Creation Kit Platform Extended.  
Open-source editor-extension platform adding fixes, enhancements and reverse-engineered resources for Bethesda Creation Kit versions including Skyrim SE.

### CK loader
Executable/loader launching CreationKit.exe with editor patches/extensions.

### Editor patch
Modification to Creation Kit behavior, stability, UI or limits; it does not change game runtime behavior unless resulting plugin/assets differ.

### CK version compatibility
Editor extensions target specific Creation Kit executable versions; verify exact support independently of Skyrim runtime support.

## Diagnostic/design rules encoded for Agent OS

1. Prefer NAVCUT for small obstacle compatibility when it can avoid unnecessary vanilla NAVM overrides.
2. Finalize navmesh after topology/door/border changes and validate actual pathing.
3. Do not infer an AI-package bug until navigation and package target accessibility are separately tested.
4. City/location overhauls need reference, navmesh, door, marker and enable-state reconciliation—not just a plugin ordering rule.
5. Landscape conflicts are LAND-record conflicts; object-placement patches do not fix erased terrain.
6. Treat Room Bound/portal problems as visibility/culling issues, distinct from navmesh.
7. Preserve Location/LocRefType semantics when moving/replacing encounter objects because Story Manager and quests may query them.
8. Use a fresh/new save when testing worldspace authoring to distinguish persisted reference state.
9. Creation Kit editor bugs/extensions must be separated from in-game engine behavior.
10. Avoid destructive navmesh deletion; route uncertain cases to manual inspection.

## Sources

- Creation Kit Wiki Cell View: https://ck.uesp.net/wiki/Cell_View_Window
- Creation Kit Wiki File Menu/editor preferences: https://ck.uesp.net/wiki/File_menu
- Creation Kit Wiki tutorial index/navmesh/optimization coverage: https://ck.uesp.net/wiki/Video_Tutorials
- Creation Kit Wiki specialist notes (NAVCUT/worldspace): https://ck.uesp.net/wiki/User:DavidJCobb
- Creation Kit Platform Extended: https://github.com/Perchik71/Creation-Kit-Platform-Extended
