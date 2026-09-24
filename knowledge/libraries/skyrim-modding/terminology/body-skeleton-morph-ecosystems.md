# Skyrim Modding Terminology — Body, Skeleton, Morph, and NPC Distribution Ecosystems

Imported: 2026-09-24
Status: sourced deep-ingestion pass 12

## Body replacer architecture

### Body replacer
Mesh/texture ecosystem replacing vanilla actor body geometry and often providing BodySlide projects for matching outfits.

### CBBE
**Expansion:** Caliente's Beautiful Bodies Enhancer. Female body ecosystem designed for BodySlide customization and compatible outfit conversions.

### CBBE SFW
Safe-for-work CBBE package retaining BodySlide/body/outfit architecture without nude assets.

### 3BA / 3BBB
CBBE-derived body/rigging ecosystem adding expanded weighted bones/physics support and BodySlide sliders beyond base CBBE.

### BHUNP
BodySlide-capable female body ecosystem in the UNP lineage with its own topology/sliders/outfit requirements.

### HIMBO
**Expansion:** Highly Improved Male Body Overhaul. Male BodySlide ecosystem with compatible slider/outfit projects.

### Body family
Set of meshes, TRI sliders, textures and outfit projects sharing topology/UV/slider conventions.

### Body topology
Vertex structure of the base body. Presets/morphs/outfit conversion data are only meaningful for compatible topology.

### Skin texture layout
UV/layout conventions expected by one body family. A mesh can load while using visibly wrong skin if texture family/UV expectations differ.

### Naked body mesh
Body geometry used when no body-slot outfit replaces it.

### Outfit body
Body geometry embedded inside armor/clothing NIF. Skyrim outfits generally replace covered body geometry rather than layering over an independently rendered naked body.

### First-person body mesh
Separate first-person arm/body assets used for player view by vanilla/special frameworks.

## BodySlide ecosystem

### Zeroed Sliders
BodySlide preset state with all shape sliders at zero, commonly used as neutral build base for RaceMenu BodyMorph/OBody-style runtime morphing.

### Built preset
Mesh output already shaped to chosen preset.

### Morph-enabled build
BodySlide output generated with Build Morphs so TRI slider data exists for runtime RaceMenu/SKEE morphing.

### Outfit conversion
Adapting outfit geometry/weights/sliders from one body family/reference to another.

### Conversion reference
Outfit Studio reference shape/sliders used to project one body standard to another.

### BodySlide group
Named set grouping body/outfit projects for batch selection.

### SliderGroup
XML group definition controlling which projects appear together.

### Preset compatibility
A preset only makes sense for slider names available on target project; missing sliders are ignored/unsupported.

### Outfit morph parity
Outfit must include corresponding morph sliders/TRI support or runtime body morph can cause body/outfit mismatch/clipping.

### Zeroed prebuilt mesh
Neutral body/outfit mesh distributed for users of OBody/BodyGen so runtime morph system supplies individual shape.

## Skeleton ecosystem

### XPMSSE
XP32 Maximum Skeleton Special Extended, broad compatibility skeleton adding nodes/bones used by weapon placement, physics and animation ecosystems.

### XPMSSE Light
Modern reduced package retaining required skeleton/compatibility components while omitting legacy script/style systems now replaceable by newer tools.

### Physics-and-skeleton-only package
Minimal XPMSSE variant containing skeleton/physics assets but no plugin/scripts for users whose modern stack handles placement/animation elsewhere.

### Skeleton winner
Actual `skeleton.nif`/female skeleton asset winning mod-manager conflict. Installing XPMSSE does not matter if another skeleton overwrites it afterward.

### Extra bone
Non-vanilla bone added to support body physics, equipment positioning or animation.

### Weapon node
Skeleton attachment node for sheathed/equipped weapon display.

### Physics bone
Bone driven by CBPC/SMP or related physics.

### First-person skeleton
Separate skeleton used in first-person representation.

### Skeleton overwrite conflict
Two mods provide skeleton files; later file can silently remove bones/nodes required by earlier mods.

## CBPC

### CBPC
**Expansion:** Collision Body Physics Config / community usage “Physics with Collisions.” Native body/equipment physics framework for SSE/VR with configurable collision and spring-style simulation.

### CBPC config
Text configuration defining physics coefficients, affected nodes/bones and collision shapes.

### Collider
Shape attached to bone/node used for collision response.

### Collision pair
Configured interaction between one collider/node group and another.

### Spring coefficient
Parameter controlling restoring force of simulated bone movement.

### Damping
Parameter reducing oscillation over time.

### Gravity bias
Downward force contribution.

### Max offset
Limit on allowed physics displacement.

### CBPC equipment physics
Using CBPC on equipment/accessory nodes, not only body bones.

### CBPC VR collision
VR build can use player hand/weapon collision against configured body colliders.

### Config hot reload/tuning
Some CBPC workflows permit runtime tuning/reload; exact commands/settings are version-specific.

### CBPC vs SMP
CBPC is lightweight spring/collision physics tied to bone configs; SMP/FSMP uses more general Bullet/Jolt-style cloth/constraint simulation. Mods can use one or both for different assets.

## Runtime body distribution

### BodyGen
RaceMenu system assigning BodyMorph templates to actors according to config.

### OBody
Runtime preset distribution system applying BodySlide slider presets through RaceMenu/SKEE BodyMorph interface.

### OBody NG
Modern native/CommonLib-based OBody lineage with per-actor preset assignment, BodyMorph keys and APIs/events.

### OBody preset
BodySlide XML preset loaded as actor morph values.

### OBody morph key
SKEE morph namespace such as `OBody` used to isolate morph ownership.

### OClothe
OBody/ORefit morph key used for clothing-refit adjustments.

### ORefit
Runtime algorithm adding clothing-specific morph compensation so outfits follow assigned body shape more closely.

### Preset assignment
Persistent/runtime relationship between actor and chosen BodySlide preset.

### Actor preset registry
Native data tracking selected preset per actor.

### Respectful morph application
Behavior clearing only OBody-owned morph keys instead of all RaceMenu morphs, allowing multiple morph-producing mods to coexist.

### OBody API
Native plugin interface allowing other mods to query assigned presets, actor naked state and listen/react to body changes.

### OBody event
SKSE ModCallback/native API event emitted after actor body/preset changes.

### AutoBody
Alternative runtime body distribution framework selecting BodySlide/RaceMenu morph presets using config/race/faction rules.

### SynthEBD
Synthesis-based NPC distribution patcher for appearance assets/body/height and consistency assignments; can coordinate with BodyGen/OBody/AutoBody.

### Consistent assignment
Patcher/runtime system remembers previous actor assignment across reruns when it remains valid.

### Procedural morph generation
Generating slider values algorithmically per actor rather than choosing from a fixed preset list.

### Body weight simulation
Using actor weight or a simulated weight input when interpolating low/high BodySlide preset values.

### Runtime refit
Applying additional morph keys based on currently worn armor rather than requiring every outfit to have one baked fixed body shape.

## Appearance-distribution conflicts

### Double body distributor
Two systems automatically assign RaceMenu morphs to same actor, causing one to clear/overwrite/compound the other's keys.

### Morph ownership
Convention using unique SKEE key for each system's contributions.

### ClearMorphs
RaceMenu API behavior clearing all morphs; aggressive and potentially destructive to other systems.

### ClearBodyMorphKeys
More targeted clearing by morph key/owner.

### Reapply morphs
Recompute/apply stored morph values after actor 3D loads, equipment changes or race/skeleton reset.

### 3D-loaded requirement
RaceMenu morph application often requires actor's 3D to exist; distant/unloaded NPCs may defer visual update.

### Morph queue
Deferred actor morph updates spread over time to reduce hitching when many NPCs load.

### Body distribution stutter
Frame hitching when many actor meshes/TRIs are rebuilt simultaneously.

## Diagnostic rules

1. Identify active body family, skeleton winner, BodySlide output, TRI availability and runtime distributor separately.
2. An outfit replaces body geometry; rebuilding only the naked body does not reshape outfits.
3. OBody/BodyGen requires morph-enabled meshes built with appropriate slider topology.
4. Skeleton conflicts can break physics/equipment nodes without obvious plugin conflicts.
5. CBPC and FSMP are different physics engines; diagnose their configs/logs separately.
6. Do not run multiple automatic body distributors on same actors unless their morph ownership/integration is explicitly compatible.
7. Preserve SKEE morph keys from unrelated mods when clearing/reassigning body state.
8. Custom followers/races can use standalone mesh/texture paths and ignore global body replacer outputs.

## Sources

- CBBE current SFW documentation: https://www.nexusmods.com/skyrimspecialedition/mods/74257
- BodySlide/Outfit Studio upstream: https://github.com/ousnius/BodySlide-and-Outfit-Studio
- XPMSSE source/archive: https://github.com/acepleiades/XP32-Maximum-Skeleton-Special-Extended
- OBody NG implementation: https://github.com/Aietos/OBody-NG
- OBody Standalone NG lineage: https://github.com/Aietos/OBody-Standalone-NG
- AutoBody AE: https://github.com/RocketBun-OG/autoBodyAE
- SynthEBD: https://github.com/Synthesis-Collective/SynthEBD

## Dated notes

CBPC's Nexus listing was observed updated 2026-08-30. XPMSSE Light's current public GitHub release describes modern stacks as using IED for weapon transforms and OAR for animation-style randomization, allowing many users to avoid legacy XPMSSE script features. Treat that guidance as package/version-specific.
