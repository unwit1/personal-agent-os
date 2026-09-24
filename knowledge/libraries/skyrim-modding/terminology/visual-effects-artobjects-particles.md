# Skyrim Modding Terminology — Visual Effects, Art Objects, Effect Shaders, and Particles

Imported: 2026-09-24
Status: sourced deep-ingestion pass 21

## Magic-effect visual chain

### MagicEffect / MGEF
Functional magic-effect record with references to visual/audio resources.

### Casting Art
ArtObject displayed on caster/hand while preparing or sustaining effect.

### Casting Light
Light emitted during casting.

### Hit Effect Art
ArtObject attached/spawned on target at impact.

### Hit Shader
EffectShader applied to target at impact.

### Enchant Art
ArtObject displayed on enchanted object/equipment.

### Enchant Shader
EffectShader applied to enchanted object.

### Projectile
PROJ carrying spell effect through world.

### Impact Data Set
IPDS determining impact art/sound/decal based on struck material.

### Explosion
EXPL spawned when projectile/effect resolves.

### ImageSpaceModifier
IMAD screen-space visual applied to caster/target/player.

### Menu Display Object
Visual representation used by magic menu.

## ArtObject

### ArtObject / ARTO
Game form referencing a NIF used as attached/spawned visual art for magic, enchantments and effects.

### Art model
NIF linked by ArtObject.

### Attached art
ArtObject bound to target/caster node for duration.

### Temporary art
Visual created during effect and removed after effect ends.

### Persistent art
Art kept while effect/enchantment/state remains active.

### Art node
Skeleton/NIF node where effect attaches.

### Model path
ARTO resource path to NIF.

### ArtObject reuse
Same ARTO can be referenced by many MGEFs; changing it can affect spells, armor enchantments and mod-added effects broadly.

## EffectShader

### EffectShader / EFSH
Game form defining animated overlay/shader effects on target geometry and/or particles.

### Membrane shader
Surface effect applied to target mesh.

### Particle shader
Particle component associated with EffectShader.

### Fill color
Shader color applied across target.

### Rim light
Edge-emphasis shader component.

### Edge effect
View-angle-dependent effect.

### Alpha
Transparency of shader.

### Falloff
How effect strength varies with view angle/distance/time.

### UV animation
Scrolling/animated texture coordinates.

### Texture
DDS used by effect shader.

### Grayscale color
Shader using grayscale texture recolored by record values.

### Persistent Effect
EFSH behavior remaining while effect active.

### Full particle birth ratio
Particle emission behavior/flags.

### Ambient sound
SoundDescriptor referenced by EffectShader.

### EffectShader reuse
One EFSH can be shared by many MagicEffects; visual patch to EFSH can intentionally propagate broadly.

## VisualEffect

### VisualEffect
Papyrus-visible effect form/object used to play a configured visual on references.

### Play
Papyrus function starting VisualEffect on reference.

### Stop
Function ending VisualEffect.

### Effect duration
Time effect remains when played.

### Root reference
Target ObjectReference/Actor whose node tree hosts effect.

### Node name
Specific attachment node.

### Facing
Orientation of spawned effect relative to target.

## ShaderParticleGeometry

### ShaderParticleGeometry
Papyrus-visible form/type associated with particle-geometry effects.

### Particle system
Emitter/update/render system producing many sprites/meshes.

### Emitter
Source spawning particles.

### Particle lifetime
Duration each particle persists.

### Birth rate
Particles created per interval.

### Particle velocity
Initial/modeled movement speed.

### Gravity
Acceleration affecting particle motion.

### Particle size
Sprite/mesh scale.

### Particle color
Tint over life.

### Particle alpha
Transparency over life.

### Billboard particle
Camera-facing sprite.

### Mesh particle
Particle represented by geometry.

### Particle atlas
Texture sheet containing multiple particle frames.

### Flipbook
Animating particle by cycling atlas frames.

## Impacts

### ImpactData / IPCT
Record defining visual/audio response for one material impact.

### ImpactDataSet / IPDS
Maps material types to ImpactData entries.

### MaterialType / MATT
Surface material classification used by impact, sound, physics systems.

### Decal
Projected texture/mark such as scorch/blood/bullet mark.

### Impact art
Particle/ArtObject spawned at collision.

### Impact sound
Sound played on collision.

### Impact hazard
Hazard spawned by impact.

### PlayImpactEffect
Papyrus/ObjectReference API triggering configured impact effect.

## Enchantment visuals

### Weapon enchant shader
Shader/art attached to weapon while enchanted/equipped.

### Enchantment visual conflict
Magic overhaul changes MGEF while visual overhaul changes EFSH/ARTO linkage.

### Visual-only patch
Patch changes EFSH/ARTO references but leaves gameplay MGEF archetype/magnitude/cost alone.

### Shared effect visual patch
Editing one vanilla EFSH/ARTO changes every magic effect that references it; can provide broad compatibility with fewer MGEF conflicts.

### Unique visual effect
New custom EFSH/ARTO used only for one enchantment/spell.

### VAER
Visual Animated Enchants Reborn ecosystem illustrating separation between enchantment gameplay records and reusable effect visual records.

## Runtime visual manipulation

### Effect shader distributor
Runtime framework such as SRD can replace EffectShader ambient sound; other runtime patchers can alter MGEF/EFSH properties.

### SkyPatcher visual field
Runtime patch modifies visual references after static load.

### Seasonal VisualEffect swap
Seasons of Skyrim supports VisualEffects form swaps in current lineage.

### Runtime-generated visual state
Final visual can differ from xEdit record due runtime swaps/patchers.

## Failure patterns

### Invisible effect
Missing ARTO NIF, bad node, shader alpha/texture, condition/effect not actually active.

### Pink/purple particle
Missing DDS/resource path.

### Effect stuck on actor
Magic effect ended but attached art/shader not stopped/cleaned because script/framework lifecycle failed.

### Wrong enchant glow
Winning MGEF points to another EFSH/ARTO or runtime patch replaced it.

### Visual patch changes unrelated spells
Shared EFSH/ARTO reused across multiple MagicEffects.

### Shader Z-fighting
Effect membrane competes with underlying geometry/depth.

### Overbright effect
HDR/ENB/CS/bloom interacting with emissive shader.

### Missing impact effect
Projectile lacks IPDS or struck material lacks mapped IPCT.

## Diagnostic rules

1. Trace MagicEffect -> ARTO/EFSH -> NIF/DDS separately.
2. A shared EFSH/ARTO edit can intentionally affect many magic effects without MGEF conflicts.
3. If gameplay works but visual fails, don't immediately patch spell archetype/cost data.
4. Missing impact visuals require material/IPDS mapping check.
5. Runtime visual swaps can make xEdit static view incomplete.
6. ENB/Community Shaders/ReShade can change final appearance of otherwise correct EFSH.
7. When authoring a visual-only compatibility patch, avoid copying unrelated MGEF gameplay fields.

## Sources

- Creation Kit Wiki Magic Effect: https://ck.uesp.net/wiki/Magic_Effect
- Creation Kit Wiki Papyrus scripting types/functions including EffectShader/VisualEffect/ShaderParticleGeometry: https://ck.uesp.net/wiki/Category:Scripting
- Visual Animated Enchants Reborn patch examples: https://www.nexusmods.com/skyrimspecialedition/mods/149925
- Sound Record Distributor EffectShader sound support: https://www.nexusmods.com/skyrimspecialedition/mods/77815
