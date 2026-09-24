# Skyrim Modding Terminology — Rendering, Shaders, Lighting, ENB, and Community Shaders

Imported: 2026-09-24
Status: sourced encyclopedia pass 3

This module separates renderer-level modification from textures, meshes, weather records, image spaces, lighting templates, post-processing, and native shader frameworks.

## Rendering pipeline concepts

### Renderer
Game subsystem that turns scene/world data into image frames through geometry, materials, lighting, shadows, post-processing and display presentation.

### Render target
GPU texture/buffer used as an intermediate or final destination for rendering passes.

### Depth buffer
Buffer storing scene depth used by visibility, post-processing, screen-space effects and other techniques.

### G-buffer
Collection of intermediate buffers used by deferred rendering techniques to store surface properties for later lighting passes.

### Shader
GPU program controlling vertex/pixel/compute processing.

### Vertex shader
Shader stage primarily processing vertices/transforms.

### Pixel shader
Shader stage calculating per-pixel output/material/lighting behavior.

### Compute shader
General GPU compute stage used for effects and rendering algorithms outside the classic vertex/pixel pipeline.

### HLSL
Microsoft shader language used for DirectX shader development and by Community Shaders source/build tooling.

### Shader cache
Precompiled/cached shader variants used to avoid compiling every shader path during live gameplay.

### Shader permutation
Specific compiled variant chosen from feature/material/lighting flags.

### Draw call
CPU/GPU submission to render geometry with a particular state/material.

### Render pass
One stage/submission phase in the frame's rendering sequence.

### Deferred lighting
Lighting method that applies light calculations using scene buffers after geometry information is rendered.

### Forward rendering
Rendering path applying lighting while rendering geometry rather than through a deferred buffer stage.

### Screen-space effect
Effect derived from already-rendered frame/depth/normal data, such as SSAO/SSR/screenspace shadows.

### SSAO
**Expansion:** Screen-Space Ambient Occlusion.  
Approximation of contact/crevice occlusion derived from screen-space depth/normals.

### SSIL
**Expansion:** Screen-Space Indirect Lighting.  
Screen-space approximation of indirect bounced light.

### SSR
**Expansion:** Screen-Space Reflections.  
Reflections reconstructed from visible screen-space scene information.

### TAA
**Expansion:** Temporal Anti-Aliasing.  
Anti-aliasing/reconstruction using information from multiple frames.

### Upscaling
Rendering internally at a lower resolution and reconstructing a higher-resolution output.

### Frame generation
Technology synthesizing intermediate display frames. It is distinct from ordinary game simulation/render FPS.

### Swap chain
DirectX presentation object managing rendered back buffers shown to the display.

### Flip model
Modern Windows presentation mode using flip-style swap effects, relevant to borderless/windowed performance and display tweaks.

## Skyrim lighting/data layers

### Light record
Game form representing a light source's color/radius/falloff/shadow and related settings.

### Placed light
Reference placing a light record in a cell/worldspace.

### Shadow-casting light
Light configured to render dynamic shadows.

### Light limit
Engine/rendering limit on simultaneous lights affecting geometry/passes; violating practical limits can cause visual/performance issues.

### Lighting template
Reusable interior-cell lighting configuration.

### Cell lighting
Interior-cell properties controlling ambient/fog/directional/environment lighting.

### Weather
Record controlling sky/cloud/precipitation/colors/fog/lighting and other outdoor atmospheric state.

### Climate
Record controlling weather selection and daylight timing for a worldspace.

### ImageSpace
Record defining post-processing/color/contrast/bloom/DOF-related parameters.

### ImageSpaceModifier
Temporary/dynamic modifier applied on top of image-space state.

### Volumetric lighting
Light/scattering effect in fog/atmosphere, often called god rays.

### Cubemap
Texture representing surrounding environment directions, used for reflections/environment mapping.

### Dynamic cubemap
Environment reflection texture generated/updated from runtime scene information.

### Parallax
Technique creating apparent depth from textures/material data without equivalent geometric depth.

### Terrain parallax
Parallax applied to terrain materials.

### Complex parallax
Advanced parallax/material path supported by modern shader frameworks/presets.

### PBR
**Expansion:** Physically Based Rendering.  
Material/lighting workflow using physical-ish parameters such as roughness/metalness and energy-conserving shading models.

### Wetness
Shader/material system simulating water-darkening/specular/reflective changes on surfaces.

### Subsurface scattering
Approximation of light traveling through translucent material such as skin.

### Contact shadow
Short-range shadow detail computed from local/screen information near contact points.

### Cascaded shadow maps
Multiple shadow-map regions/resolutions covering different distances around the camera.

## ENBSeries

### ENBSeries
External/native graphics modification framework by Boris Vorontsov that hooks the game's DirectX rendering pipeline and provides extensive post-processing and renderer effects.

### ENB binary
Runtime DLL component loaded into/alongside the game process to intercept graphics calls.

### ENB preset
Configuration and shader files tuned by a preset author for a particular visual result.

### enbseries.ini
Primary ENB configuration file controlling effect/render settings.

### enblocal.ini
Local machine/performance/input/proxy-related ENB configuration separated from preset visual settings in modern ENB workflows.

### enbeffect.fx
ENB shader file implementing configurable post-processing/effect behavior.

### d3d proxy
DLL proxy/hook technique where a graphics DLL loads before/around the game's normal DirectX path.

### ENB helper/plugin
Additional component exposing weather/location/time/game information to ENB presets.

### ENB weather
Preset-specific per-weather configuration overriding/tuning effects for different weather states.

### ENB particle lights
ENB feature/emergent ecosystem allowing specially configured meshes/effects to emit apparent light through ENB shader processing.

### ENB complex particle lights
Extended particle-light path with richer surface/light response, preset/framework dependent.

### ENBSeries conflict
Another graphics injector/hook modifies the same DirectX chain. Compatibility must be verified rather than stacking DLL proxies blindly.

## Community Shaders

### Community Shaders / CS
Open-source SKSE core plugin/framework for advanced community-driven graphics modifications to Skyrim's renderer.

### CS core
Main native rendering framework that optional features integrate with.

### CS feature
Modular rendering effect implemented on top of Community Shaders.

### Shader cache compilation
Community Shaders compiles/caches shader variants; startup compilation failures are renderer/framework evidence, not ordinary plugin-record conflicts.

### Developer mode
CS configuration exposing debugging/recompilation tools for shader development.

### Shader hot reload
Development behavior recompiling/reloading shader code when source changes, where supported.

### RenderDoc
Graphics debugger/capture tool used by Community Shaders development docs to inspect frame rendering.

### Global Illumination
Rendering approximation of indirect/bounced light. Current CS development includes GI-related systems/features.

### Light Limit Fix
Community Shaders ecosystem feature expanding/changing how Skyrim handles dynamic lights in rendering.

### Screen-space shadows
CS feature/path adding additional shadow detail from screen-space information.

### Dynamic Cubemaps
CS ecosystem feature producing runtime reflective environment cubemaps.

### Grass lighting
Shader changes affecting how grass receives scene lighting.

### Terrain blending
Renderer/material changes controlling landscape layer transitions.

### Water shader
Rendering code controlling Skyrim water appearance, reflection/refraction, caustics and related effects.

### Unified Water
Current CS ecosystem water-rendering work integrating previously separate improvements under a shared system.

## SSE Display Tweaks

### SSE Display Tweaks
SKSE plugin modifying presentation/timing/display behavior for smoother gameplay and modern display configurations.

### Framerate unlocking
Removing/reworking assumptions tying display FPS to historical Skyrim limits.

### Havok timestep
Physics simulation timestep relationship to frame timing. Incorrect changes can destabilize physics.

### Physics step cap
Limit on number of physics simulation steps allowed per update.

### Borderless fullscreen
Windowed presentation without visible borders, distinct from exclusive fullscreen.

### Exclusive fullscreen
Display mode where the game owns the fullscreen swap chain/display context more directly.

### Borderless upscale
Display Tweaks ability to render at selected internal/window resolution and scale to the desktop output under supported presentation modes.

### FPS limiter
Frame-rate limiting within display/runtime tooling.

### Present interval / VSync
Controls synchronization between frame presentation and display refresh.

## Rendering diagnostics

### Z-fighting
Flickering where surfaces are at nearly identical depth and the depth buffer cannot consistently determine which is in front.

### Shadow acne
Self-shadow artifacts from shadow-map precision/bias.

### Peter-panning
Detached-looking shadows caused by excessive shadow bias.

### Shimmering
Temporal high-frequency flicker from aliasing, LOD/texture/shadow instability or insufficient temporal filtering.

### TAA ghosting
Temporal history leaves trails/blur behind moving objects.

### Shader compilation failure
HLSL/shader build error preventing one or more renderer permutations/features from compiling.

### Device lost/device removed
DirectX/GPU failure class where graphics device becomes unavailable/reset; investigate driver/GPU/hook issues rather than plugin records first.

### VRAM pressure
GPU memory demand approaches/exceeds available budget, causing streaming/stutter or severe failures depending on driver/runtime behavior.

### CPU draw-call bottleneck
Performance limited by CPU submission/scene overhead rather than GPU shader cost.

### GPU bottleneck
Frame time dominated by GPU rendering workload.

## Diagnostic rules encoded for Agent OS

1. Separate weather/image-space records from renderer hooks and shader code.
2. A texture replacement cannot directly fix a failed native shader hook.
3. A visual bug that appears only with ENB/CS disabled or enabled is strong layer-isolation evidence.
4. Do not stack graphics injectors/proxies without explicit compatibility.
5. Record resolution, presentation mode, upscaler, frame generation, driver and GPU when diagnosing display/render crashes.
6. Community Shaders and ENB are alternative/overlapping renderer ecosystems in many configurations; compatibility is feature-specific, not assumed.
7. Diagnose light-limit artifacts separately from mesh normals, texture issues and plugin light placement.
8. Use frame/render captures and shader logs for renderer development; xEdit cannot inspect HLSL execution.
9. Physics instability at high FPS can be timing-related; verify Display Tweaks/Havok settings before blaming animations.
10. Treat shader framework versions as time-sensitive native dependencies.

## Sources

- Community Shaders upstream: https://github.com/community-shaders/skyrim-community-shaders
- Community Shaders Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/86492
- ENBSeries Skyrim documentation: https://enbdev.com/doc_skyrim_en.htm
- SSE Display Tweaks: https://github.com/SlavicPotato/SSEDisplayTweaks
- Creation Kit Wiki rendering/editor/lighting references: https://ck.uesp.net/wiki/File_menu
