# Skyrim Modding Terminology — NPC Appearance, FaceGen, RaceMenu, Morphs, and Character Generation

Imported: 2026-09-24
Status: sourced encyclopedia pass 3

This module separates NPC base-record appearance, generated FaceGen assets, player character-generation systems, RaceMenu runtime extensions, BodyMorph/BodyGen, tint assets, head parts, and skeleton/node transforms.

## NPC appearance foundations

### NPC_ record
Actor base record containing NPC identity, stats, race, class, factions, inventory, AI data, face/appearance parameters, head parts, tint layers, weight, and related base information.

### Actor base
The NPC_ definition shared by references of that NPC. Appearance data stored here is distinct from the generated FaceGen mesh/texture assets used by the renderer.

### Actor reference
Placed/runtime instance of an NPC base. Some appearance/state changes can exist per-reference or through runtime overlays/morph systems.

### Race
Form defining allowable head parts, body data, skeleton/model relationships, morph behavior and other actor-characterization settings.

### Sex
Male/female actor-base flag affecting body/head assets, voice/race selections and many appearance systems.

### Weight
NPC/player body-weight value used by compatible _0/_1 meshes and other systems. It is not the same thing as arbitrary BodyMorph sliders.

### Height
Race/actor scale-related value distinct from body weight and mesh morphing.

## Head parts and face data

### HeadPart
Base form representing one component of a character head, such as hair, eyes, brows, facial hair, scars or other configured head-part types.

### Head-part type
Engine classification identifying the functional category of a HeadPart.

### Extra head part
HeadPart associated as an additional dependent/linked part of another head part.

### Valid-races list
FormList constraining which races can use a head part.

### Hair
HeadPart category for hairstyle meshes/data.

### Eyes
HeadPart category selecting eye assets/data.

### Brow
HeadPart category selecting eyebrow assets.

### Facial hair
HeadPart category for beards/moustaches and related assets.

### Scar
HeadPart category for scar geometry/assets.

### Face morph
Set of facial-shape parameters used by character generation to produce final face geometry.

### Morph slider
Character-generation control changing one or more morph parameters.

### Head mesh
NIF representing the character's head geometry.

### FaceGen
Bethesda character-head generation pipeline and generated assets produced for NPCs.

### FaceGeom
Generated FaceGen head mesh path convention beneath `Meshes/actors/Character/FaceGenData/FaceGeom/<PluginName>/`.

### FaceTint
Generated NPC face/tint texture path convention beneath `textures/actors/Character/FaceGenData/FaceTint/<PluginName>/`.

### FaceGen mesh
Per-NPC generated NIF corresponding to the NPC's FormID in the plugin namespace/path.

### FaceGen tint
Per-NPC generated DDS containing baked tint/complexion/makeup-related appearance.

### FaceGen export
Creation Kit operation generating FaceGeom and FaceTint assets for selected NPCs.

### Ctrl+F4
Traditional Creation Kit shortcut associated with exporting selected NPC FaceGen data.

### Dark face / black face bug
Appearance mismatch where the loaded NPC record/head parameters and the winning/generated FaceGen assets do not agree, often producing dark/incorrect head coloration or mismatched face shape.

### FaceGen conflict
Different mods provide NPC_ overrides and/or FaceGen files for the same NPC but the winning record and winning assets come from different sources.

### FaceGen consistency
Desired state where the effective NPC_ appearance data and corresponding FaceGeom/FaceTint assets were generated for the same intended appearance.

### Plugin-name FaceGen path
FaceGen folder includes the source plugin filename. Renaming/merging/compacting plugins can therefore require careful regeneration/migration of appearance assets.

### NPC FormID FaceGen filename
Generated face files are named using the NPC's form identity. Changes to local FormIDs can invalidate previously generated files.

### Tint layer
NPC/player appearance layer describing color/makeup/complexion/warpaint/etc. inputs.

### Tint mask
Texture/mask used by the character-generation/tint system to define regions/effects.

### Complexion
Appearance layer/detail affecting skin/face texture presentation.

### Warpaint
Tint/overlay-style character-generation face marking.

### Makeup
Tint-layer category for cosmetic face coloration/details.

## RaceMenu and skee

### RaceMenu
SKSE-based replacement/extension of Skyrim character creation by Expired, adding sliders, presets, overlays, sculpting, BodyMorph and extensibility APIs.

### skee64.dll
RaceMenu's native SKSE plugin binary for Skyrim SE/AE.

### skee
RaceMenu's native/runtime subsystem name used in logs, console commands and configuration.

### skee64.ini
RaceMenu native configuration file controlling features/performance/compatibility options.

### RaceMenuPlugin.esp
Plugin component used by RaceMenu for game data required by some features.

### CharGen
RaceMenu subsystem/path naming associated with presets, morphs, sculpt data and character-generation resources.

### .jslot preset
RaceMenu preset file storing character appearance selections/parameters for later loading.

### Preset
Saved RaceMenu character-generation configuration. A preset is not automatically a full NPC replacer and may depend on installed head parts/morph assets.

### Sculpt
RaceMenu feature storing direct vertex-level head sculpt changes.

### Sculpt data
Per-head-part vertex deltas used to reproduce manually sculpted head shapes.

### Overlay
RaceMenu feature rendering additional body/hand/feet/face paint/tattoo-like layers.

### Overlay template
Mesh/material arrangement onto which RaceMenu overlays are applied.

### Overlay slot
One configurable overlay layer/channel.

### BodyMorph
RaceMenu/NiOverride-compatible system applying TRI-defined body morphs dynamically at runtime.

### BodyMorph key
Named morph channel/value associated with an actor.

### Morph cache
RaceMenu runtime cache of body TRI/morph data used to accelerate application.

### BodyMorph rebind
Runtime process applying/reapplying body morphs to loaded geometry.

### GPU copy morph path
RaceMenu optimization path for body morph processing referenced by modern skee64 options.

### BodyGen
RaceMenu system that distributes BodyMorph presets/values to NPCs using configuration templates/mappings.

### BodyGen template
Named collection of body morph sliders/values used as a candidate preset.

### BodyGen morphs.ini
Configuration file defining BodyGen morph templates.

### BodyGen templates.ini
Common naming used by BodyGen configuration packages for reusable templates/mappings depending on version/convention.

### BodyGen mapping
Rule associating actors/NPCs/forms with one or more BodyGen templates.

### Deterministic BodyGen assignment
Assignment designed to remain stable for an actor rather than randomly changing every load, depending on configured system behavior.

### NiOverride
RaceMenu native feature/API lineage for modifying NetImmerse scene nodes, transforms, overlays and morph-related data at runtime.

### NetImmerse override
Runtime alteration applied to a NIF scene node/property without permanently editing the source NIF.

### Node transform
Translation/rotation/scale applied to a named skeleton/scene node.

### Transform key
Namespace/key allowing multiple mods/systems to add independent node transforms.

### Transform priority
Resolution/combination behavior when multiple transforms affect the same node.

### ItemData
RaceMenu system for unique item-bound appearance data such as dyes/transforms.

### Dye
RaceMenu feature allowing color data to affect supported item materials/overlays.

### Interface exchange
Native plugin API handoff used by RaceMenu so other SKSE plugins can query RaceMenu interfaces after relevant SKSE lifecycle messages.

### Early registration
Compatibility option allowing RaceMenu interface availability earlier than its standard lifecycle point for mods that require it.

## TRI and morph data

### TRI file
Vertex morph data file used by Skyrim/RaceMenu/BodySlide-related systems.

### Facial TRI
Morph data associated with facial character-generation shapes.

### Body TRI
Morph data generated for BodyMorph-compatible body/outfit meshes.

### Morph target
Named target vertex positions/deltas defining a shape transformation.

### Vertex delta
Per-vertex positional difference from base geometry for a morph.

### Topology dependency
Morph data assumes compatible vertex count/order/topology. Applying TRI data to an incompatible mesh can fail or deform incorrectly.

### Build Morphs
BodySlide build mode that outputs morph data suitable for RaceMenu BodyMorph in addition to final NIF meshes.

### Zeroed sliders
BodySlide authoring convention where a reference/project base is kept at zero morph values so runtime BodyMorph can apply a wide range without baked preset distortion.

### Baked body
Mesh generated with a preset already applied statically by BodySlide.

### Runtime body
Visual result after RaceMenu BodyMorph values are applied to the built base/output mesh at runtime.

## Appearance conflict patterns

### NPC replacer
Mod changing an NPC's face/body/head parts and usually providing matching FaceGen assets.

### Appearance patch
Plugin/asset combination reconciling NPC appearance with gameplay changes from another mod.

### Forward NPC appearance
Copy intended face/head/weight/tint fields into a conflict-resolution plugin while preserving unrelated gameplay changes from other mods.

### Forward gameplay data
Copy AI/stats/factions/packages/inventory/etc. from gameplay mods into the winning NPC record without discarding the intended appearance fields.

### FaceGen regeneration
Re-export FaceGen for the final patched NPC record when an appearance patch creates a new effective combination requiring matching assets.

### EasyNPC
Community tool/workflow for selecting/merging NPC appearances from multiple replacers and generating a consolidated appearance result. Treat generated plugin/assets as a patch layer.

### Head-part dependency
NPC/preset depends on a modded hair/eyes/brow/scar/etc. HeadPart. Missing dependencies can produce missing or substituted appearance.

### High-poly head
Replacement/custom head mesh topology with its own compatible morphs/head parts. Presets/sculpts may depend on its topology.

### Vanilla head
Bethesda default head geometry/morph topology.

### Neck seam
Visible mismatch where head and body geometry/normal/texture/weight data do not align at the neck boundary.

### Skin texture mismatch
Head/body textures or normal/specular maps from different skin packages produce visible color/material discontinuity.

### Head/body normal mismatch
Different normal-map sets create lighting discontinuity even when diffuse colors appear similar.

### Headpart mesh conflict
Asset-priority conflict changes the mesh used by a HeadPart without changing its plugin record.

## Diagnostic rules encoded for Agent OS

1. For dark-face/mismatched NPC reports, inspect **both** winning NPC_ record and winning FaceGeom/FaceTint assets.
2. Do not fix an NPC gameplay conflict by simply loading the appearance plugin last if that discards needed AI/stats/faction changes; create/choose a proper patch.
3. Renaming or compacting an NPC-defining plugin can invalidate FaceGen path/FormID assumptions.
4. Player RaceMenu presets and NPC FaceGen are separate systems.
5. BodySlide preset output and RaceMenu BodyMorph are separate layers; determine whether the shape is baked, runtime, or both.
6. A missing hair/eye/headpart dependency can mimic preset corruption.
7. Sculpt/TRI data is topology-sensitive.
8. RaceMenu is a native SKSE dependency: exact runtime/SKSE compatibility matters independently of its ESP.
9. Diagnose neck seams across mesh topology, weights, diffuse/normal/specular textures and runtime morphs, not only the NPC record.
10. Preserve matching FaceGen when forwarding unrelated NPC gameplay fields.

## Sources

- RaceMenu Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/19080
- RaceMenu/SKSE source lineage: https://github.com/expired6978/skse64
- Creation Kit Wiki HeadPart Script: https://ck.uesp.net/wiki/HeadPart_Script
- Creation Kit Wiki Dark Face Bug: https://ck.uesp.net/wiki/Dark_Face_Bug
- BodySlide/Outfit Studio: https://github.com/ousnius/BodySlide-and-Outfit-Studio
## Native sex and HeadPart enums — CommonLibSSE-NG

Sources:
- `include/RE/S/Sexes.h` blob `d9a2cef91a97668725b4cdde565977a6d541079f`
- `include/RE/B/BGSHeadPart.h` blob `f7db3c9f23de9bc6b7dd7b47718a6040dce864f6`

### Sex

| Value | Native enum |
|---:|---|
| -1 | `None` |
| 0 | `Male` |
| 1 | `Female` |

The native enum's total is 2. Treat this as the engine sex enum represented by current CommonLib, not as a general statement about gender identity.

### HeadPart type

| ID | Type |
|---:|---|
| 0 | Misc |
| 1 | Face |
| 2 | Eyes |
| 3 | Hair |
| 4 | Facial Hair |
| 5 | Scar |
| 6 | Eyebrows |

### HeadPart flags

- `Playable = 1 << 0`
- `Male = 1 << 1`
- `Female = 1 << 2`
- `IsExtraPart = 1 << 3`
- `UseSolidTint = 1 << 4`

### HeadPart morph indices

- `RaceMorph = 0`
- `DefaultMorph = 1`
- `ChargenMorph = 2`

### Diagnostic implications

1. A HeadPart's **type**, sex flags, valid-races list, extra-part relationships and TRI assets are separate compatibility dimensions.
2. A hair/eye/brow HeadPart can exist and load correctly while being excluded from a race or sex by record data.
3. `IsExtraPart` represents a dependent/additional head-part relationship; it is not equivalent to a separate RaceMenu overlay.
4. FaceGen consistency still requires the final NPC_ record and generated FaceGeom/FaceTint to agree after HeadPart changes.

