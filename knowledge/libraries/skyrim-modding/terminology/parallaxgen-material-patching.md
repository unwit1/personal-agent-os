# Skyrim Modding Terminology — ParallaxGen/PGPatcher and Material Patch Generation

Imported: 2026-09-24
Status: sourced deep-ingestion pass 16

## ParallaxGen / PGPatcher

### ParallaxGen
Load-order-aware mesh/material patch generator designed to enable appropriate parallax/PBR shader data on Skyrim meshes according to installed textures/assets.

### PGPatcher
Current public project/mod name for modern ParallaxGen lineage.

### Mesh patch
Generated NIF modification changing shader properties/texture slots/flags according to detected parallax/material assets.

### Plugin patch
Generated `ParallaxGen.esp` containing TXST/record changes needed for some material relationships.

### Texture discovery
Tool scans NIF/texture paths rather than relying only on filename convention to determine available material maps.

### Mod-manager hook
ParallaxGen can use mod-manager conflict/order information to resolve which source mesh/texture wins.

### MO2 loose-file order
Current tool can use MO2 left-pane/effective loose-file priority to derive PG source ordering.

### GUI
Modern ParallaxGen releases moved primary configuration from CLI arguments to graphical interface.

### Allowlist
Explicit paths/mods allowed for patching.

### Blocklist
Paths/mods excluded from patching.

### Vanilla BSA list
Configured archives recognized as vanilla/source data during conflict/material resolution.

### Texture map
Configuration mapping texture patterns/roles for patching.

### Diff JSON
Generated metadata recording differences/patch results for downstream use/troubleshooting.

### ParallaxGen output
Generated mod containing patched meshes/plugin/config metadata; should be managed separately and regenerated when relevant inputs change.

## Shader modes

### Vanilla parallax
Classic Skyrim parallax shader mode using height map and corresponding mesh shader settings.

### Complex Material / CM
Community Shaders material model extending parallax/material features beyond classic vanilla mode.

### PBR
Physically based rendering material path supported by modern Community Shaders/ParallaxGen ecosystem.

### TruePBR
Community Shaders PBR feature/material workflow.

### MultiLayer Parallax
Bethesda shader type used for some specialized materials; incorrect assignment can cause broken/dark/exploding-looking output.

### Shader_Type 11
Technical/community reference for MultiLayer_Parallax type; current community fixes document bad automatic assignment as a possible mesh problem.

### Shader upgrade
ParallaxGen option/path converting eligible older shader setup toward newer complex-material/PBR-compatible behavior.

### --upgrade-shaders
Historical CLI option; modern GUI exposes equivalent feature selection as implementation evolves.

### PBR glint
Material feature supported in newer ParallaxGen lineage.

## Supporting tools/assets

### Parallax height map
Texture encoding surface height/displacement used by parallax.

### _p.dds
Common filename suffix for parallax height maps in Skyrim texture ecosystems.

### Auto Parallax
Runtime framework protecting/enabling parallax handling so meshes without expected matching textures do not produce blue/broken appearance, depending on current workflow.

### Terrain Parallax Blending Fix
Framework/assets correcting landscape-to-mesh/terrain blending issues in parallax setups.

### ParallaxR
Tool generating parallax/height textures for installed assets; complementary to ParallaxGen, which patches meshes/material relationships.

### BENDr
Related rendering/texture processing workflow referenced by modern parallax ecosystems.

## Load-order relationship

### Source mesh winner
Effective NIF before ParallaxGen patching, determined by mod manager priority.

### Source texture winner
Effective DDS/material maps before generation.

### Generated mesh winner
Patched NIF should normally win after original source meshes while preserving intended upstream asset priority.

### ParallaxGen.esp order
Generated plugin placed late enough to win relevant TXST/material record edits but before downstream generators such as DynDOLOD when DynDOLOD must observe the patched records/assets.

### DynDOLOD dependency
Distant LOD generation may need to run after ParallaxGen so generated LOD uses final material/mesh information.

### Regeneration trigger
Add/remove/update mesh, texture, parallax/PBR material mod, shader framework or relevant load-order priority -> rerun ParallaxGen.

## Failure patterns

### Blue mesh
Material expects texture/resource absent or incompatible.

### Dark object
Incorrect material/shader assignment, missing map, environment scale or lighting interaction.

### Exploding mesh
Severe malformed shader/mesh/topology/result symptom; can result from patching an asset not authored for selected shader mode.

### Missing parallax
Mesh shader not enabled, height map absent/wrong slot, renderer feature absent, source output overwritten or tool blocklist.

### Wrong material winner
Generator saw a different source mesh/texture priority than actual game runtime.

### Stale generated mesh
Output predates current texture/mesh stack.

### Bad source mesh
Generator reveals/crashes on malformed source NIF; fixing source is preferable to blindly suppressing all validation.

### Environment Map Scale issue
Material parameter causing dark/incorrect complex material behavior on some assets; blocklist/manual fix may be appropriate for known exceptions.

## Performance/generation

### Multithreaded mesh patching
ParallaxGen parallelizes mesh processing to improve generation speed.

### High-memory mode
Historical generation option trading memory use for throughput/caching.

### Mesh optimization
Optional generator process altering mesh beyond shader patch; use cautiously because optimization can change compatibility.

### Output cache
Reusing analyzed/generated state to reduce rerun cost where current version supports it.

## Diagnostic rules

1. Treat ParallaxGen as generated output tied to exact asset priority.
2. Regenerate before debugging old output after changing texture/mesh stack.
3. Renderer support (Community Shaders/ENB path), mesh shader state and height/PBR textures must all agree.
4. Do not patch every mesh into parallax/PBR if source asset/material lacks valid maps.
5. Generated TXST/plugin output and generated NIF output are separate layers.
6. DynDOLOD should see the final desired source/material state when generating LOD.
7. If only one object is broken, compare original and patched NIF rather than disabling parallax globally.

## Sources

- PGPatcher/ParallaxGen current Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/120946
- Modern parallax texture workflow example: https://www.nexusmods.com/skyrimspecialedition/mods/125527
- Community Shaders upstream: https://github.com/community-shaders/skyrim-community-shaders

## Dated snapshot

PGPatcher/ParallaxGen 2.1.1 was current on Nexus on 2026-09-24, updated 2026-09-18. Older guides referring only to CLI switches can be stale because modern releases added a GUI and mod-manager-based conflict ordering.
