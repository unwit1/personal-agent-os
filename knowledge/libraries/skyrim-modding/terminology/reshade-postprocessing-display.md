# Skyrim Modding Terminology — ReShade, Post-Processing, Display, and Presentation

Imported: 2026-09-24
Status: sourced deep-ingestion pass 12

## ReShade

### ReShade
Generic post-processing injector framework that hooks graphics presentation and executes user-selected shader effects on rendered game buffers.

### ReShade addon support
Build mode/API allowing ReShade add-ons deeper access/integration than ordinary post-process shaders. Community Shaders documentation requires full add-on support for current compatibility.

### ReShade preset
INI/config selecting effect shaders and parameters.

### ReShade shader
FX/HLSL-like post-processing effect executed by ReShade.

### ReShade technique
Named pass/effect enabled in preset.

### ReShade overlay
In-game configuration UI for shader selection/order/parameters.

### Depth buffer access
ReShade's ability to sample game depth for depth-aware post effects.

### Generic depth
Screen-space depth representation; unlike engine-native renderer hooks, ordinary ReShade does not necessarily have full material/G-buffer/game-lighting semantics.

### Preprocessor definition
Compile-time shader option selected through ReShade UI/config.

### Shader compile
ReShade compiles effect source into GPU shader program on load/change.

### Shader error
Effect fails compile due syntax/version/macro/resource mismatch.

### Effect order
Ordering among post-processing techniques affects output because one pass consumes prior pass output.

### Add-on
Native extension to ReShade with hooks/data beyond normal FX shaders.

## Post-processing concepts

### Color grading
Changing color balance/contrast/saturation to establish visual tone.

### LUT
Lookup table transforming input color into graded output.

### Sharpening
Post-process increasing local edge contrast/detail.

### Bloom
Glow/blur from bright image regions.

### Depth of field
Depth-aware blur simulating camera focus.

### Film grain
Synthetic noise overlay.

### Vignette
Edge darkening/brightening.

### Chromatic aberration
Color-channel offset toward screen edges.

### Motion blur
Blur based on temporal/camera/object motion.

### God rays
Screen-space/radial light-shaft approximation.

### Screen-space fog
Fog approximation derived from depth/final image rather than full engine volumetric data.

### Contact shadow approximation
Short-range screen-space shadow using depth buffer.

### SMAA
Morphological anti-aliasing post-process.

### FXAA
Fast approximate anti-aliasing.

### CAS
Contrast Adaptive Sharpening algorithm.

## Engine-level vs post-process

### Engine-level shader framework
Community Shaders/ENB-style system hooking engine renderer and accessing engine-specific data/stages.

### Post-process injector
ReShade-style framework primarily acting after/during final presentation with generic graphics buffers.

### G-buffer access
Engine-specific material/normal/light data unavailable to many generic ReShade shaders.

### Effect overlap
Running similar AO/bloom/tonemap/sharpen effects in multiple frameworks can double-apply visual processing.

### CS + ReShade
Supported configuration when using ReShade build with full add-on support according to current Community Shaders documentation.

### ENB + ReShade
Technically possible in many setups, but effect overlap/proxy/injector ordering must be deliberately configured.

### CS + ENB
Current Community Shaders documentation states core CS and ENBSeries are incompatible; CS disables itself when ENB is detected to prevent crashes.

### Effects 11
Current Community Shaders feature enabling many ENB preset/effect definitions to run on Community Shaders' rendering stack without ENBSeries itself; still requires version-specific compatibility.

## Injection/loading

### dxgi.dll
Common proxy DLL filename used by ReShade/graphics injectors in DirectX 11 games.

### d3d11.dll
Another proxy/injector filename used by graphics frameworks.

### Proxy DLL chain
One injector loads/forwards into another so multiple frameworks can coexist.

### DLL rename
Compatibility technique using alternate recognized proxy name so loaders chain correctly.

### Root injector
DLL installed beside SkyrimSE.exe rather than under Data.

### Injector load order
Order graphics proxy DLLs initialize; wrong order can produce black screen/crash/missing overlay.

### Steam overlay
Additional graphics overlay that can interact with injectors.

### RTSS
RivaTuner Statistics Server overlay/frame limiter that can hook presentation.

### Discord overlay
Third-party overlay that can interact with D3D hooks.

## Display pipeline

### Presentation
Submitting final backbuffer/frame to display via swap chain.

### Swap chain
DXGI object managing backbuffers/presentation.

### VSync
Synchronizing frame presentation to display refresh interval.

### Tearing
Visible discontinuity when presentation occurs mid-refresh.

### VRR
Variable Refresh Rate display technology allowing display refresh to track frame delivery.

### G-Sync / FreeSync
Vendor implementations/ecosystems of VRR.

### Frame limiter
Caps render/present rate below display maximum.

### SSE Display Tweaks
SKSE native display/presentation framework supporting borderless/fullscreen behavior, framerate unlock/limiter, Havok timing and display fixes.

### Borderless fullscreen
Window without borders sized to display, composited by desktop/window manager.

### Exclusive fullscreen
Traditional fullscreen presentation with game owning display mode more directly.

### Flip model
Modern DXGI presentation mode improving borderless latency/performance characteristics.

### Resolution scale
Internal render resolution relative to output/display resolution.

### Upscaling
Reconstructing output resolution from lower internal render resolution.

### Frame generation
Synthesizing interpolated/predicted frames between actual game-rendered frames.

### Input latency
Delay between input and visible response; frame generation can raise displayed FPS without proportionally reducing simulation/input latency.

## HDR

### SDR
Standard Dynamic Range output.

### HDR10
High Dynamic Range display pipeline using HDR metadata/color/luminance standards.

### Auto HDR
Windows/system conversion/enhancement of SDR applications for HDR displays.

### Native HDR
Game/framework outputs HDR directly.

### Paper white
HDR reference brightness for ordinary UI/content.

### Peak luminance
Maximum display/effect brightness target.

### HDR tonemapping
Mapping scene linear/high-range values to HDR output.

### UI compositing in HDR
HUD/menu brightness/color requires correct SDR↔HDR conversion.

## Diagnostic rules

1. Identify every injector/overlay DLL in game root before diagnosing graphics startup crashes.
2. Do not enable duplicate AO/tonemapping/sharpening blindly across ENB/CS/ReShade.
3. ReShade depth-dependent effects can fail if depth buffer access is unavailable/reversed/cleared.
4. Community Shaders currently requires full add-on ReShade for supported coexistence.
5. Frame generation FPS is not equal to engine simulation FPS.
6. Presentation stutter can come from VSync/VRR/frame limiter interactions independent of shader cost.
7. Shader compilation stutter should be distinguished from texture streaming/CPU stutter.
8. HDR UI/paper-white issues are display pipeline problems, not texture color errors.

## Sources

- ReShade project/site: https://reshade.me/
- Community Shaders current upstream: https://github.com/community-shaders/skyrim-community-shaders
- Community Shaders FAQ: https://github.com/community-shaders/skyrim-community-shaders/wiki/FAQ
- Effects 11 - Community Shaders current documentation: https://www.nexusmods.com/skyrimspecialedition/mods/179824
- SSE Display Tweaks configuration source examples: current mod documentation/source ecosystem

## Dated note

Current Community Shaders documentation observed 2026-09-24 says ENBSeries is incompatible with Community Shaders core, while ReShade is supported when the full add-on-support ReShade build is used. Effects 11, released in 2026, provides an alternate route for many ENB-style preset effects on the CS stack without ENBSeries.
