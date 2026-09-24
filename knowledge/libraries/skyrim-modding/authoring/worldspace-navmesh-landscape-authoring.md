# Skyrim Worldspace, Landscape, and Navmesh Authoring

Imported: 2026-09-24
Status: sourced authoring knowledge

## Worldspace structure

### Worldspace
Exterior-world container divided into coordinate cells and associated with climate, water, map, parent/child settings, terrain/LAND, references and LOD systems.

### Parent worldspace
Worldspace whose land/world data can be inherited or visually reused by a child worldspace.

### Child worldspace
Worldspace related to a parent, commonly used by walled cities or specialized exterior spaces. Parent/child relationships can create special LOD/reference behaviors.

### LAND record
Exterior-cell terrain record storing height/texture/landscape-related information.

### Landscape height
Vertex terrain elevations defining physical ground shape.

### Landscape texture
Layered terrain material/texture painting data associated with LAND.

### Cell border
Boundary between adjacent exterior cells. Landscape/navmesh editing must preserve continuity across cell borders.

### Worldspace origin/grid
Exterior coordinates relative to the worldspace coordinate system.

### Region
World-design data used to procedurally place/configure landscape objects, weather, map data or encounters depending on region type.

### Border region
Region used to limit player travel at world boundaries.

## Navmesh authoring

### NAVM
Navmesh record type.

### Navmesh triangle
Traversable polygon.

### Vertex
Point defining triangle corners.

### Edge
Triangle boundary potentially connected to another triangle.

### Portal / external edge link
Connection allowing navigation across cell/navmesh boundaries.

### Finalization
Editor operation that updates required navmesh connectivity/metadata, especially border/external links. Saving hand edits without required finalization can leave broken pathing.

### Border triangle
Triangle touching a cell boundary and participating in cross-cell navigation connections.

### Island
Disconnected navmesh component. Can be intentional for isolated actors but accidental islands break pathfinding.

### Preferred path
Navmesh/pathing metadata biasing route choice.

### Cover edge
Navigation metadata used by combat/AI cover behavior where supported.

### Navcut
Runtime/navigation modifier that blocks/cuts traversability without permanently editing the underlying navmesh geometry. CK community technical notes specifically recommend L_NAVCUT collision primitives for some small additions to avoid direct vanilla navmesh conflicts.

### L_NAVCUT
Collision/material flag used on primitives/objects so runtime navigation treats the shape as a navmesh cutter.

### Navmesh door link
Navigation relationship around load doors/teleports/door markers enabling pathing between connected spaces.

### Navmesh conflict
Two mods overriding the same NAVM or adjacent connectivity. Load order cannot combine two independent triangle edits.

### Deleted navmesh
Hard-deleted NAVM override. High-risk; replacing/repairing deleted navmesh requires record-aware procedure rather than ordinary UDR assumptions.

### Navmesh patch
Compatibility plugin that reconstructs a desired merged navigation layout, potentially by copying one NAVM and reapplying required edits from another.

### Edge-link regeneration
Re-finalization/reconnection required after merged navmesh edits so adjacent-cell navigation links are coherent.

## Safer design patterns

### Avoid editing vanilla NAVM when possible
For small obstacles/additions, consider runtime navcut/collision solutions if they accurately express the desired blocked space.

### Dedicated new interior
New cells/navmeshes avoid many direct conflicts with heavily modded vanilla interiors.

### Minimal footprint
Change only the triangles/regions actually required and avoid broad auto-generation across an existing cell.

### Compatibility-first placement
Before editing navmesh in popular settlement/city cells, inspect common overhaul conflicts and design for patchability.

### Keep source backups
Navmesh edits are difficult to reconstruct from memory. Keep pre-edit plugins and incremental commits.

### Validate border navigation
Test followers/NPCs crossing edited cell borders and door transitions.

## Landscape authoring

### Landscape editor
CK tool for raising/lowering terrain and painting landscape textures.

### Landscape vertex
Terrain grid point whose height is edited.

### Flatten tool
CK landscape operation for flattening terrain. Community technical notes warn that its minimum radius and undo behavior can be destructive; use cautiously.

### Texture layer limit
Landscape cells/quad regions have engine/editor limits on simultaneously usable texture layers. Exceeding practical limits can cause missing/black terrain textures.

### Seam
Visible mismatch at cell/terrain borders due to height, normal, texture or LOD disagreement.

### Heightmap
Large-scale elevation dataset that can be imported/generated for a worldspace.

### Terrain LOD regeneration
Landscape changes generally require updated terrain LOD if they must appear correctly at distance.

## Testing checklist

- NPC can traverse every intended route.
- Followers cross cell borders.
- Doors can be reached from both sides.
- No accidental isolated triangles.
- Combat/search actors can navigate.
- Landscape has no holes/seams.
- Water/terrain transitions are valid.
- New references have sensible persistent/temporary state.
- LOD regenerated after landscape/world changes.
- Parent/child worldspace behavior tested where applicable.
- xEdit checked for NAVM/LAND/cell conflicts.
- Established save and new game compared if changes are being tested mid-development.

## Diagnostic rules

1. An actor refusing to move can be AI/package, navmesh connectivity, door-link, collision, or state—test these separately.
2. Load order cannot merge triangle geometry from two NAVM overrides.
3. Use navcut for appropriate small obstacle cases to reduce navmesh compatibility surface.
4. Landscape and LOD are separate representations; correct nearby terrain does not imply correct distant terrain.
5. Parent/child worldspaces have engine-specific inheritance/LOD edge cases.
6. Do not automate deleted-navmesh repair without a dedicated validated procedure.

## Sources

- Creation Kit Wiki Cell View: https://ck.uesp.net/wiki/Cell_View_Window
- Creation Kit Wiki community technical notes (navcut and landscape warnings): https://ck.uesp.net/wiki/User:DavidJCobb
- DynDOLOD child/parent worldspace copies: https://dyndolod.info/Help/Child-Parent-Worldspace-Copies
- DynDOLOD large references: https://dyndolod.info/Help/Large-References
- Creation Kit Platform Extended: https://github.com/Perchik71/Creation-Kit-Platform-Extended
