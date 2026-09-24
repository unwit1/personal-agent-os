# Skyrim Modding Knowledge — Weather, Climate, Region, Light, Projectile, Explosion, Hazard, and Impact Systems

Imported: 2026-09-24
Status: encyclopedia pass 6

This module fills smaller but frequently interconnected CK systems used by environmental, combat and magic mods.

## Weather and climate

### Weather / WTHR
Outdoor atmospheric record defining sky colors, cloud layers, fog distances/colors, precipitation, lighting colors, wind/sun/glare and related state.

### Climate / CLMT
Worldspace climate record selecting allowed weathers and sunrise/sunset timing.

### Weather chance
Relative weighting determining which weather may be selected within a climate/region system.

### Weather transition
Runtime interpolation from outgoing to incoming Weather.

### Current Weather
Weather fully/currently active.

### Outgoing Weather
Weather being transitioned away from.

### ForceActive / ForceWeather
Papyrus weather API overriding normal climate/weather selection.

### ReleaseOverride
Return weather control from forced override to ordinary climate/system behavior.

### Sky mode
Engine state controlling exterior/interior sky handling.

### Precipitation
Rain/snow particle behavior configured through weather/assets.

### Cloud layer
Weather-configured texture/color/speed layer.

### Fog near/far
Distance parameters controlling atmospheric fog.

### Volumetric lighting
Weather/render settings contributing to god-ray/scattering presentation.

### Weather lighting colors
Directional/ambient/specular/fog colors across day phases.

### Time-of-day color
Weather contains multiple color sets for sunrise/day/sunset/night transitions.

## Regions

### Region / REGN
Worldspace spatial region with region areas and entries controlling weather, objects, grass, map data, sounds and other procedural/regional content.

### Region area
Polygonal/geographic boundary defining where region entries apply.

### Region weather
Weather list/weights applied within region context.

### Region object
Procedural object placement definitions within a region.

### Region grass
Grass distribution associated with region data.

### Region sound
Ambient sound entries tied to region.

### Region map
Map-label/color/data related to a region.

### Region overlap
Multiple region areas overlap; engine resolves/combines entry categories according to type/priority rules, requiring testing.

## Lighting

### Light / LIGH
Base light source record.

### Placed light
REFR whose base is a Light.

### Radius
Light's range.

### Color
RGB light color.

### Fade
Light attenuation/intensity parameter.

### Shadow light
Light that casts dynamic shadows.

### Hemispherical light
Special lighting behavior depending on light type/flags.

### Flicker
Light animation flag causing intensity variation.

### Pulse
Alternative animated intensity behavior.

### Portal-straddling light
Interior light affects geometry across Room Bound portals, influencing performance/pass counts.

### Light limit
Renderer limitations on how many lights affect geometry simultaneously.

## Projectiles

### Projectile / PROJ
Flight/impact record for arrows, missiles, beams, flames/cones and barriers.

### Missile projectile
Discrete moving projectile with speed/gravity/collision.

### Lobber
Ballistic projectile with arc/gravity behavior.

### Beam projectile
Beam-style continuous/line projectile.

### Flame projectile
Cone/stream-like projectile used for flame effects.

### Cone projectile
Area cone behavior; some usages differ from ordinary ammunition/projectile hit semantics.

### Barrier projectile
Persistent barrier-style projectile behavior.

### Projectile speed
Initial/travel speed.

### Projectile gravity
Ballistic drop factor.

### Range
Maximum projectile travel/effect range where applicable.

### Tracer
Visual tracer/model behavior.

### Muzzle flash
Art/light effect spawned at firing point.

### Explosion link
Projectile can spawn an Explosion on impact/end.

### Impact force
Physics impulse contribution at collision.

### Collision layer
Controls which objects projectile collides with.

### Projectile lifetime
Time before projectile expires/despawns.

## Explosions

### Explosion / EXPL
Area event/effect spawned from projectiles, traps, activators or magic.

### Explosion radius
Area of effect.

### Explosion force
Havok impulse applied within explosion.

### Damage
Direct explosion damage where configured.

### Enchantment/spell
Explosion can apply associated effects.

### ImageSpaceModifier
Visual post-effect triggered by explosion.

### Light
Temporary light associated with explosion.

### Sound
Explosion audio.

### Placed object
Explosion can spawn/associate objects according to supported fields.

## Hazards

### Hazard / HAZD
Persistent area effect object with model/radius/lifetime/spell/impact characteristics.

### Hazard spell
Spell applied by actors/references inside hazard area.

### Hazard lifetime
Duration hazard remains.

### Hazard radius
Area within which effect applies.

### Hazard interval
Tick/application interval where configured.

### Hazard owner
Caster/owner relationship can determine hostility/friendly filtering.

### Spawn Hazard archetype
MagicEffect archetype creating a Hazard at target.

### PlaceAtMe hazard
Script-created hazard can differ in ownership/scaling semantics from archetype-spawned hazard.

## Impacts

### ImpactData / IPCT
One material-specific impact response: decal, sound, art object, hazard, duration and orientation behavior.

### ImpactDataSet / IPDS
Set mapping physical material types to corresponding ImpactData.

### MaterialType / MATT
Physical material classification used by collision/impact/sound systems.

### Decal
Projected impact texture such as blood/scorch/arrow mark.

### Decal lifetime
Duration decal remains.

### Impact sound
Sound played for hit/material combination.

### Impact art
ArtObject/model effect spawned at collision.

### Impact hazard
Hazard spawned by an impact.

### PlayImpactEffect
Papyrus method requesting an impact effect on a reference/model at a node/material context.

## Integrated diagnostic rules

1. Weather record and ENB/Community Shaders rendering are separate layers.
2. Region weather selection and worldspace climate selection can interact; inspect both before assuming WTHR itself is broken.
3. Light placement/count/shadow settings can create performance artifacts unrelated to texture quality.
4. Projectile, Explosion, Hazard and MagicEffect form a chain; debug each link separately.
5. The visible impact depends on projectile/weapon/spell plus target MaterialType/IPDS/IPCT.
6. Script-spawned hazards can have different ownership behavior from MagicEffect Spawn Hazard.
7. Missing projectile art can be asset-path failure even when PROJ record is correct.
8. Collision layers and mesh collision can determine whether projectile ever reaches its impact logic.
9. Interior light optimization includes Room Bounds/portals and per-object light counts.
10. Environment mods should be tested across time-of-day, weather transition and interior/exterior boundaries.

## Sources
- Creation Kit Wiki Magic Effect: https://ck.uesp.net/wiki/Magic_Effect
- Creation Kit Wiki scripting/object references: https://ck.uesp.net/wiki/Category:Scripting
- xEdit current schemas: https://github.com/TES5Edit/TES5Edit
