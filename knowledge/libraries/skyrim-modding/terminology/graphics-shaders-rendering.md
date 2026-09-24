# Skyrim Modding Terminology — Graphics, Shaders, Rendering, ENB, and Community Shaders

Imported: 2026-09-24
Status: sourced deep-ingestion pass 3

## Rendering fundamentals

### Renderer
Engine subsystem that turns world/scene data into frames through geometry, lighting, shadow, material, post-processing, and presentation stages.

### Draw call
CPU/GPU command to render geometry with a particular state/material. Excessive draw calls can become CPU-bound even when GPU utilization is not saturated.

### Shader
GPU program used for vertex/geometry/pixel/compute processing. Skyrim's material/rendering behavior is heavily shader-driven.

### Vertex shader
Shader stage transforming vertices and preparing per-vertex attributes.

### Pixel shader
Shader stage computing final per-pixel output such as material lighting, color, transparency, fog, or other effects.

### Compute shader
General GPU compute stage used by modern rendering mods for effects that do not fit classic draw stages.

### HLSL
Microsoft High-Level Shader Language used for DirectX shaders.

### Render target
Texture/buffer used as an intermediate or final rendering destination.

### Depth buffer
Buffer storing per-pixel depth used for visibility, depth testing, screen-space effects, and reconstruction.

### Normal buffer
Screen/geometry data encoding surface normal direction, used by many lighting and screen-space effects.

### G-buffer
Set of render targets storing geometry/material attributes for later lighting/effect passes in deferred-style rendering.

### Post-processing
Image effects performed after primary scene rendering, such as tonemapping, color grading, sharpening, blur, ambient effects, or upscaling.

### HDR
High Dynamic Range rendering/display pipeline with luminance/color range beyond standard SDR.

### Tonemapping
Mapping high-range scene luminance/color into a display/output range while controlling contrast and highlight rolloff.

### Exposure
Brightness mapping control used in HDR/tonemapping pipelines.

### Gamma
Nonlinear mapping relationship used in display/color pipelines. Incorrect assumptions can produce washed-out or overly dark output.

### Linear lighting
Lighting calculations performed in linear color space rather than directly in gamma-encoded values.

### PBR
**Expansion:** Physically Based Rendering. Material/lighting approach based on physically motivated properties such as roughness, metallic response, normal data, and energy-consistent lighting.

### Parallax
Technique that uses height/depth data to create perceived geometric depth without adding equivalent mesh geometry.

### Complex parallax
More advanced parallax/material workflow used by Skyrim graphics ecosystems for greater apparent surface depth.

### Terrain blending
Technique reducing visible seams/transitions between terrain and placed geometry/materials.

### Subsurface scattering
Lighting approximation for light traveling through translucent materials such as skin.

### Screen-space effect
Effect calculated from already-rendered buffers visible to the camera. Screen-space techniques cannot directly account for all off-screen geometry.

### SSAO
Screen-Space Ambient Occlusion approximation of local ambient shadowing.

### SSGI
Screen-Space Global Illumination approximation using visible screen buffers.

### SSR
Screen-Space Reflections based on data present in rendered screen/depth buffers.

### Volumetric lighting
Lighting/fog effect representing scattering through participating media such as haze or fog volumes.

### Screen-space shadow
Shadowing derived in screen space rather than solely through vanilla shadow maps.

### Shadow map
Texture/rendered depth representation from a light used to determine shadowed regions.

### Cascaded shadow maps
Multiple shadow-map regions/resolutions across camera distance to improve directional-light shadow quality.

### Upscaling
Rendering at reduced/internal resolution then reconstructing a higher-resolution output.

### Frame generation
Technique synthesizing intermediate frames to increase presentation frame rate. It changes presentation characteristics and can introduce compatibility/latency issues independent of simulation FPS.

### TAA
Temporal Anti-Aliasing combining data across frames to reduce aliasing.

### DLAA
Deep-learning anti-aliasing variant oriented around native-resolution reconstruction rather than resolution upscaling.

### DLSS / FSR / XeSS
Vendor/ecosystem upscaling technologies with different runtime dependencies and integration paths.

## Community Shaders

### Community Shaders
SKSE native rendering framework providing community-driven advanced graphics modifications for Skyrim SE/AE/VR.

### Feature shader
Community Shaders modular rendering feature implemented through the core framework's hooks/render pipeline.

### AIO package
Community Shaders all-in-one packaging of the current supported feature set.

### Native graphics menu
Current Community Shaders feature exposing rendering settings through an injected/native UI surface rather than only external INI editing.

### Light Limit Fix
Community Shaders feature addressing Skyrim's traditional per-object/light limitations and related rendering behavior.

### Skylighting
Ambient/sky lighting enhancement feature.

### Screen-Space Shadows
Community Shaders feature adding screen-space shadowing.

### Volumetric Shadows
Shadowing integrated with volumetric lighting/fog.

### Wetness Effects
Material/screen rendering feature adding wet-surface responses.

### Terrain Blending
Feature improving visual integration of terrain and placed meshes.

### TruePBR
Community Shaders PBR material/rendering feature.

### Grass Optimizations
Community Shaders rendering/performance feature targeting grass behavior.

### HDR Display
Feature enabling an HDR display/output path in supported environments.

### Community Shaders version coupling
Feature versions and the core CS build evolve together. A feature DLL/config from one generation should not be assumed compatible with a different core release.

## ENB

### ENBSeries
External graphics injection/post-processing framework by Boris Vorontsov used by Skyrim for shader replacement/enhancement and extensive post-processing.

### ENB binary
Runtime DLL components loaded into/alongside Skyrim to intercept/render through DirectX.

### ENB preset
Collection of configuration and shader files defining the visual behavior of an ENB setup.

### enbseries.ini
Primary ENB configuration file.

### enblocal.ini
Environment/local configuration traditionally used for machine-specific or loader-related ENB settings.

### ENB shader file
Editable shader code/config used by ENB effects.

### ENB Helper
Mod/helper layer used by many weather-aware ENB setups to expose additional game/weather parameters to ENB.

### ENB weather
Weather-specific ENB configuration allowing visual parameters to vary by Skyrim weather.

### ENB vs Community Shaders
Two distinct advanced-rendering ecosystems. They can target overlapping visual features and should not be assumed mutually compatible merely because individual effects have similar names.

## Materials and textures

### Albedo / diffuse texture
Base surface color information before lighting.

### Normal map
Surface-normal perturbation data.

### Specular
Reflective highlight response.

### Roughness
PBR property controlling spread/sharpness of reflections.

### Metallic
PBR property describing metal-like light response.

### Emissive
Material output that appears self-lit/glowing.

### Environment map
Texture/cubemap used for reflection/environment response.

### Cubemap
Texture representing surrounding directions used for environmental reflection/lighting.

### Parallax height map
Texture/channel encoding surface height/depth for parallax rendering.

### BC compression
Block-compressed DDS texture formats used to reduce texture memory/storage. Exact format should match data type/alpha requirements.

### Mipmap
Precomputed lower-resolution texture levels used at distance/minification.

### VRAM
GPU video memory storing textures, geometry, render targets, shaders, and other graphics resources.

### Texture streaming pressure
Performance/stability pressure when active resources exceed efficient memory/bandwidth behavior.

## Lighting/environment records

### Weather
Game record controlling sky, lighting colors, fog, cloud and environmental presentation for a weather state.

### Climate
Record controlling weather selection and broader regional/day-cycle behavior.

### ImageSpace
Record controlling image-processing/environment visual properties.

### ImageSpaceModifier
Temporary/conditional visual modifier used for effects such as damage, menus, magic, transitions, and other presentation changes.

### Lighting template
Reusable interior-lighting configuration.

### Cell lighting
Interior cell-specific lighting/fog/ambient parameters.

### Directional ambient lighting
Directional ambient contribution used in Skyrim environment/interior lighting.

## Performance diagnosis

### CPU-bound
Frame rate limited primarily by main-thread/render-thread/script/AI/draw-call work rather than GPU shading capacity.

### GPU-bound
Frame time dominated by GPU rendering workload.

### Frametime
Time to produce/present one frame. Stable frametime matters independently of average FPS.

### Stutter
Irregular frametime spikes. Potential causes include shader/resource compilation, streaming, disk I/O, scripting, physics, VFS hooks, background processes, or render feature behavior.

### Shader compilation stutter
Frame delay caused by compiling/building shader/pipeline state at runtime.

### RenderDoc
Graphics debugging/capture tool sometimes used by graphics developers for frame analysis. Hooking tools can conflict with other injectors.

### Overlay/injector conflict
Compatibility issue caused by multiple programs intercepting DirectX/input/presentation, such as graphics frameworks, monitoring overlays, capture tools, RTSS, or driver overlays.

## Diagnostic rules

1. Separate plugin lighting records, mesh/material data, texture assets, and native rendering frameworks before blaming "ENB" or "shaders" generically.
2. Determine CPU-bound versus GPU-bound behavior using frametime evidence, not GPU percentage alone.
3. Rendering-framework updates are runtime-sensitive native changes; preserve exact Skyrim, SKSE, framework, GPU driver, and feature versions.
4. Similar effects in ENB and Community Shaders can overlap conceptually but use different implementation paths.
5. Screen-space artifacts should be evaluated with the limitations of visible depth/normal buffers in mind.
6. Texture problems can be format/mipmap/path/material issues even when the mesh is correct.
7. Injectors/overlays can cause crashes or input/render interference independent of mod plugin load order.

## Sources

- Community Shaders upstream: https://github.com/community-shaders/skyrim-community-shaders
- Community Shaders releases: https://github.com/community-shaders/skyrim-community-shaders/releases
- Creation Kit Wiki Retexture Tutorial: https://ck.uesp.net/wiki/Retexture_Tutorial
- Creation Kit Wiki ImageSpace/lighting references: https://ck.uesp.net/wiki/Category:WorldData
- ENBSeries official site/documentation should be treated as the primary ENB source when available; community presets are preset-specific evidence.

## Dated snapshot

On 2026-09-24, Community Shaders v1.9.1 was the current GitHub release observed during ingestion. Its release metadata listed active feature families including Light Limit Fix, Skylighting, Screen-Space Shadows, Volumetric Shadows, Terrain Blending, TruePBR, HDR Display, Wetness Effects, Grass Optimizations, SSGI-related work and other modules. Treat this as a dated snapshot, not timeless capability metadata.
