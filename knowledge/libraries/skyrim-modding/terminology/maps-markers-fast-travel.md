# Skyrim Modding Terminology — Maps, Markers, Compass, and Fast Travel

Imported: 2026-09-24
Status: sourced deep-ingestion pass 11

## Map markers

### MapMarker
Placed reference/base marker used by Skyrim's world/local-map discovery and fast-travel systems.

### Map marker reference
Placed REFR containing map-marker data.

### Marker type
Icon/category shown on world map/compass, such as city, cave, camp, fort or other vanilla marker classes.

### Marker name
Localized display name shown on map.

### Visible marker
Marker currently allowed to appear on map/compass.

### Discovered marker
Marker state indicating player has discovered it.

### AddToMap
Papyrus/ObjectReference function adding/revealing marker, optionally as fast-travel target.

### CanFastTravelToMarker
API testing whether fast travel to marker is currently allowed.

### FastTravel
Game function traveling player to reference/marker when allowed.

### EnableFastTravel
Game-level control globally enabling/disabling fast travel.

### IsFastTravelEnabled
Tests global fast-travel enabled state.

### Map marker state persistence
Visibility/discovery can be stored in save/reference state; plugin changes do not necessarily reset an established save's marker discovery.

## Compass and quest targets

### Compass marker
HUD representation of nearby map marker/quest target.

### Quest target
Objective/alias/reference chosen for compass/map guidance.

### Objective target
Specific target reference/location attached to a displayed quest objective.

### Quest-target path
Navigation path engine computes toward target for compass guidance.

### Minimal Use door
Door flag reducing/preventing use by quest-target path selection/NPC routing when alternatives exist.

### Door teleport
Linked door connection between cells/worldspaces.

### Door marker
Teleport destination/orientation marker associated with load door.

### Hidden door
Door record flag suppressing map representation according to door behavior.

### Local map
Interior/local representation generated from cell geometry rather than world map terrain.

### World map
Exterior map presentation derived from worldspace map/terrain data and markers.

## Worldspace map data

### Map data
WRLD settings controlling world-map camera/usable bounds/scale/offset.

### World map height
Map-camera/elevation mapping settings.

### World map bounds
Worldspace coordinate range used by map display.

### MapMenu
Scaleform menu implementing Skyrim world/local map UI.

### Map camera
Camera controller used while world map is open.

### Paper map
UI/mesh replacement approach presenting a pre-rendered flat map rather than vanilla 3D terrain map.

### Flat world map
Map mod style flattening/replacing vanilla topographic world-space presentation.

### Map texture
Texture asset representing paper/flat map imagery.

### Map mesh
World-map geometry used by map mods to align the visual map.

### Map marker offset
Marker coordinate adjustment needed when custom flat-map projection/mesh differs from vanilla.

## Fast travel restrictions

### Fast-travel-disabled worldspace
Worldspace/conditions in which travel is restricted.

### Interior fast travel
Normally unavailable unless specialized engine/mod behavior permits it.

### Combat restriction
Fast travel denied while in combat.

### Trespass/restricted state
Some game states can block travel.

### Scripted fast travel
Mod invokes game travel APIs/teleports directly rather than relying solely on world map click.

### Teleport vs FastTravel
MoveTo/COC/door teleport changes location directly; FastTravel uses map/travel rules and time/world processing.

### Fast-travel arrival marker
Reference/marker determining exact arrival position for location.

## Map mods and compatibility

### Atlas-style marker mod
Mod adding/changing marker data/icons/locations.

### Marker conflict
Multiple plugins alter same marker reference/name/type/visibility.

### Map UI conflict
Multiple mods replace MapMenu SWF/interface assets.

### Flat-map conflict
Paper-map mesh/texture/INI/worldspace config must match; mixing components from different map projection mods can misplace markers.

### Compass overhaul
HUD mod altering marker filtering, distance, icons or compass presentation.

### Marker icon resource
Interface texture/SWF asset containing marker symbols.

### Worldspace support patch
Map mod patch adding proper mesh/texture/marker handling for custom worldspace.

## Debugging

### ShowMapMarkers
Console/debug command family toggling/revealing markers depending on engine command usage; avoid on production saves unless intentional.

### Marker FormID
Reference ID useful for inspecting visibility/discovery state in console/xEdit.

### Marker owner plugin
Plugin defining/last overriding marker reference.

### Incorrect marker position
May be wrong REFR coordinates or custom-map projection/offset mismatch.

### Marker visible but no fast travel
Discovery/visibility and fast-travel eligibility are separate state/flags.

## Diagnostic rules

1. Treat marker visibility, discovery and fast-travel eligibility as separate concepts.
2. Flat-map marker misalignment can be map projection/mesh/config, not marker coordinates.
3. Quest compass targets rely on quest objectives/aliases/pathing, not ordinary map marker discovery alone.
4. Direct teleport commands are not equivalent tests of fast-travel rules.
5. Established saves preserve marker discovery/state; compare fresh save when authoring marker changes.
6. Custom worldspaces need explicit map-data/map-mod support.

## Sources

- Creation Kit Wiki Door record: https://ck.uesp.net/wiki/Door
- Creation Kit Wiki Papyrus API index (AddToMap, FastTravel, CanFastTravelToMarker, EnableFastTravel): https://ck.uesp.net/wiki/Category:Scripting
- Creation Kit Wiki WorldSpace/Cell tools: https://ck.uesp.net/wiki/Category:WorldData
