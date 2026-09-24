# Skyrim Plugin Record Schema — Worldspaces, Cells, Landscape, Navmesh, and Environment

Imported: 2026-09-24
Status: field-level schema deepening

## WRLD — Worldspace

Key data:
- EDID/FULL;
- parent worldspace;
- climate;
- water;
- map data;
- world bounds;
- LOD/worldspace settings;
- flags;
- child CELL groups.

Patch semantics:
- Parent-world inheritance can make apparent missing values intentional.
- Water/LOD/map edits are often orthogonal and need field-level forwarding.

## CELL

Key data:
- flags/interior/exterior;
- grid coordinates for exterior;
- lighting template;
- direct lighting/fog values;
- ImageSpace;
- water;
- acoustic space;
- encounter zone;
- ownership;
- location;
- SE water-flow data;
- child reference groups;
- LAND/NAVM.

Patch semantics:
- CELL is one of Skyrim's most conflict-dense records.
- Lighting, water, ownership and location mods can all edit the same CELL for unrelated reasons.
- Do not copy whole CELL from one overhaul when another only needs one subsystem field.

## LAND

Contains:
- terrain vertex heights;
- vertex normals;
- vertex colors;
- texture layers/alpha;
- grass-related data.

Patch semantics:
- Landscape edits are spatial, not semantically mergeable by ordinary last-wins logic.
- Two mods editing same quadrant/vertex region require deliberate landscape patching.

## NAVM

Contains:
- vertices;
- triangles;
- edge adjacency;
- cover/flags;
- door/reference links;
- island/connectivity information.

Patch semantics:
- Deleted NAVM is high risk.
- Navmesh edits cannot be safely “merged” as generic arrays.
- New architecture usually requires re-authoring/finalizing navmesh.

## REGN — Region

Can include:
- region polygons/areas;
- weather;
- sounds;
- grass;
- object generation;
- map data.

Patch semantics:
- Region mods may conflict on one subdomain while preserving others.

## WTHR — Weather

Fields include:
- cloud textures/layers;
- time-of-day colors;
- fog;
- precipitation;
- lightning/thunder;
- wind;
- visual data;
- ambient/sound data.

Patch semantics:
- Weather appearance and Climate selection are separate.

## CLMT — Climate

Fields:
- weather list/weights;
- sunrise/sunset timing;
- moon phase/visibility;
- related climate timing data.

Patch semantics:
- Adding a new WTHR does nothing unless climate/region/system selects it.

## LGTM — Lighting Template

Fields:
- ambient/directional colors;
- fog near/far/color/power;
- specular;
- directional rotation/fade.

Patch semantics:
- CELL inheritance flags determine whether LGTM value is actually used.

## IMGS — ImageSpace

Fields:
- HDR/exposure-like parameters;
- bloom;
- adaptation;
- tint/contrast/saturation;
- other image-processing inputs.

## IMAD — ImageSpaceModifier

Transient effect record:
- blur;
- tint;
- double vision;
- radial effects;
- timing curves.

## ECZN — EncounterZone

Fields:
- owner;
- location;
- minimum/max encounter level;
- flags such as Never Resets;
- encounter behavior.

## LCTN — Location

Fields:
- parent;
- keywords;
- encounter zone;
- special data;
- LocationRefType associations through placed references.

Patch semantics:
- Location hierarchy/keywords drive Story Manager and radiant quests.

## REFR / PGRE / PMIS / PHZD / PARW / PBAR / PBEA

Placed-reference families for:
- ordinary objects;
- grenades/projectiles/missiles;
- hazards;
- arrows/beams/barriers depending engine record family.

Patch semantics:
- reference position, enable parent, linked refs and ExtraData can matter more than base object.

## World patch checklist

For a city/worldspace patch:
1. placements;
2. LAND;
3. NAVM;
4. CELL lighting/water/acoustics;
5. Room Bounds/Portals for interiors;
6. Location/LocRefTypes;
7. encounter zones;
8. persistent/reference groups;
9. LOD regeneration;
10. grass cache;
11. water flow;
12. runtime swaps/Seasons.

## Sources

- xEdit record schemas
- Creation Kit World Data and Navmesh documentation
- TES5Edit/xEdit current CELL/WRLD handling notes
