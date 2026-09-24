# Skyrim Modding Terminology — CoMAP and Custom Map Marker Frameworks

Imported: 2026-09-24
Status: sourced deep-ingestion pass 18

## CoMAP

### CoMAP
**Expansion:** Common Marker Addon Project. SKSE/SkyUI map-marker framework expanding available world-map/compass marker icons and allowing marker assignment/music/config customization with reduced need for dedicated ESP edits.

### Custom marker
Additional icon type beyond vanilla marker set.

### Marker config
Framework file assigning marker icon/type/behavior to references/forms/mod content.

### Marker assignment
Rule mapping a location/reference to desired custom marker graphic/type.

### Marker art
SWF/texture/vector resource defining custom icon visual.

### Marker Dev Kit
CoMAP resources/tutorial/template for authors creating new marker types/configs.

### Resource SWF
Scaleform asset containing marker icon resources.

### Config pack
Predefined CoMAP mappings for supported mods/locations.

### Obscured undiscovered marker
Display style showing an undiscovered location as generic/hidden/outline rather than revealing exact type.

### Hidden Until Discovered
Marker policy suppressing marker until player discovers it.

### Discovery music
Audio triggered on location discovery; CoMAP can alter marker discovery music behavior according to current feature set.

### Jorrvaskr/closed-city marker choice
Example framework config distinguishing semantic map marker type without needing arbitrary new plugin marker record.

### Marker reassignment
Changing existing marker's icon classification at runtime/config layer.

### ESP-less marker patch
Config/resources adding/reassigning marker icon without static plugin override when framework can identify target.

### CoMAP Local
2026 optional example applying custom marker functions to local-map contexts.

### Custom worldspace marker support
Framework/addon providing custom marker art/config for new-land worldspaces.

### CoMAP addon
Mod-specific config/art package mapping that mod's locations to CoMAP marker types.

## Marker resource pipeline

### Map marker icon atlas
Scaleform/resource collection containing marker graphics.

### Marker ID
Framework-specific identifier selecting icon.

### Marker texture/vector
Visual resource embedded/referenced by SWF.

### UI reskin
Replacement visual styling of CoMAP marker resources without changing semantic assignments.

### Marker localization
Display name remains normal map-marker/location text; icon semantics can be separate from localized names.

### Compass integration
Custom marker icon rendered on compass as well as world map where supported.

### MapMenu integration
Scaleform/native hook injecting custom marker visuals into world map.

## Discovery semantics

### Undiscovered marker
Marker exists but player has not visited/discovered location.

### Known but undiscovered
Engine/mod may reveal marker silhouette/name before actual discovery.

### Discovered marker
Fast-travel/map state after discovery where allowed.

### Marker visibility mode
CoMAP configuration controlling how undiscovered markers are drawn/hidden.

### Fast-travel independence
Custom icon/type does not itself guarantee or disable fast travel; marker travel flags/state remain separate.

## Compatibility

### Marker framework conflict
Two mods replace map marker resources/SWF or assign icon type differently.

### Reskin compatibility
Visual reskin must include all custom CoMAP marker IDs or missing/incorrect icons can appear.

### CoMAP version mismatch
Addon targets marker IDs/config syntax absent/changed in installed framework.

### Custom-map compatibility
Paper/flat map replacement can change marker positioning/appearance while CoMAP changes marker icon semantics.

### Marker addon load order
Config/resource priority determines which assignment/art override wins; distinguish from plugin load order.

### 1.5.97 port
Separate CoMAP 4 port exists for Skyrim 1.5.97 while current main build follows modern runtime support.

## Diagnostic rules

1. Separate marker reference position/state from CoMAP icon assignment.
2. A custom marker appearing at wrong map coordinates is likely world-map projection/reference position issue, not icon artwork.
3. Missing icon may be outdated reskin/resource SWF lacking current marker ID.
4. Config-only addon will not appear as an xEdit conflict.
5. CoMAP icon type and fast-travel availability are distinct.
6. Custom worldspace mods may require both map-data support and CoMAP marker config.
7. Record CoMAP and reskin version because the marker catalog grows over time.

## Sources

- CoMAP current Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/56123
- CoMAP 1.5.97 port: https://www.nexusmods.com/skyrimspecialedition/mods/101421
- CoMAP addon examples (VIGILANT/UNSLAAD) on Nexus

## Dated snapshot

CoMAP 4.5.0 was current on 2026-09-24, updated 2026-08-27. Its Nexus files include a Marker Dev Kit and 2026 CoMAP Local example.
