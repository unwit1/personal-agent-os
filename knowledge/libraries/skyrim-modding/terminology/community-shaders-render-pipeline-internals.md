# Skyrim Modding Terminology — Community Shaders Render Pipeline Internals

Imported: 2026-09-24
Status: sourced frontier-deepening pass

## Architecture

### Community Shaders / CS
SKSE-native renderer modification framework extending Skyrim SE/AE/VR graphics through Direct3D 11 hooks, shader replacement/augmentation and modular features.

### Shader cache
CS system caching/replacing compiled shader permutations.

### Feature
Modular render subsystem registered with Community Shaders core.

### Package shader
Shader source/package loaded by core.

### Feature shader
Shader code owned by one feature.

### Permutation
One compiled shader variant selected according to material/pass/features.

### Shader descriptor
Bitfield/key describing vanilla and CS feature state for one permutation.

### Extra shader descriptor
CS-added descriptor bits used to distinguish additional states such as reflections/in-world/feature modes.

## Forward and deferred rendering

### Forward renderer
Vanilla Skyrim primarily shades objects as they are rendered, combining material/light calculations directly into output targets.

### Deferred renderer
CS can introduce deferred-style passes storing material attributes into multiple render targets before later lighting/composite steps.

### G-buffer
Set of render targets storing per-pixel material/geometry attributes.

### Albedo target
Base color.

### Specular target
Specular contribution/data.

### Reflectance target
Reflectance/material response.

### NormalRoughness target
Encoded normal + roughness.

### Masks target
Feature/material masks.

### Masks2
Additional mask channel; current CS source uses it for data such as vertex ambient occlusion.

### Motion vector
Per-pixel movement used by temporal effects/upscaling.

### Depth buffer
Per-pixel scene depth.

### Deferred composite
Compute/render pass combining G-buffer, lighting/GI/reflections/etc. into final/main target.

## Passes

### Prepass
Render phase executed before main deferred shading for feature data preparation.

### EarlyPrepass
Earlier hook used by selected features.

### Deferred pass
Feature work after geometry attributes are available.

### PostDeferred
Feature work after deferred composite but before later presentation stages.

### Reflection prepass
Feature pass preparing data before cubemap/reflection rendering.

### First-person pass
Special rendering path for player hands/body requiring explicit state/permutation handling.

### Water pass
Distinct renderer section; CS source keeps separate water history/targets and restores targets before water rendering.

## D3D11 resources

### ID3D11Texture2D
GPU texture/render resource.

### Render Target View / RTV
Writable render-target binding.

### Shader Resource View / SRV
Readable shader texture binding.

### Unordered Access View / UAV
Writable compute-shader/resource binding.

### DepthStencilView
Depth/stencil binding.

### Constant buffer
GPU buffer containing per-frame/material/feature parameters.

### Sampler
Texture filtering/addressing state.

### Blend state
How new pixel output combines with existing target.

### Depth state
Depth-test/write configuration.

### Rasterizer state
Culling/fill/scissor state.

## Current feature families

Community Shaders source/release ecosystem includes or has included features such as:

### Dynamic Cubemaps
Runtime/environment reflections.

### Image Based Lighting / IBL
Lighting using environmental image/cubemap information.

### Screen Space GI / SSGI
Approximate indirect lighting from screen-visible geometry.

### Skylighting
Ambient/sky-driven lighting.

### Subsurface Scattering
Skin/material light transport approximation.

### Terrain Blending
Improved terrain/object material transitions.

### Effects11
Modern CS feature enabling many ENB-style effect/preset concepts on CS rendering stack.

### Upscaling
Integration with resolution reconstruction.

### PBR / TruePBR
Physically based material extensions.

### Complex Materials
Advanced parallax/material data path.

### Wetness Effects
Dynamic wet/surface response.

### Grass Lighting
Improved grass lighting/shadow/material behavior.

### Light Limit Fix
Extends/changes dynamic-light limitations.

### Screen-space Shadows
Additional shadowing.

### Volumetric Lighting
Enhanced atmospheric light scattering.

## Temporal systems

### Temporal AA / TAA
Uses frame history and motion/depth to reduce aliasing.

### History buffer
Prior-frame texture used by temporal effect.

### Reprojection
Map prior-frame pixels into current frame using motion/depth.

### Ghosting
History persists incorrectly around moving objects.

### Disocclusion
Previously hidden surface becomes visible and has no valid history.

### Jitter
Subpixel camera/projection offset used to collect additional temporal samples.

### Upscaler history
DLSS/FSR/XeSS-like algorithms need motion/depth/history data.

### Water history
Water uses specialized temporal buffers because coverage/transparency differs from opaque geometry.

## Shader compilation

### HLSL
Shader source language.

### Vertex shader
Transforms geometry/outputs per-vertex attributes.

### Pixel shader
Computes per-pixel material/color.

### Compute shader
General GPU compute pass used for deferred composite, GI and other effects.

### Shader macro
Compile-time feature/permutation definition.

### Shader compile cache
Cached bytecode reducing repeated compilation.

### Compile stutter
Frame hitch when shader permutation is first compiled/generated.

### Cache invalidation
Shader/core/feature update makes old cache stale.

## Material data

### Roughness
Micro-surface scattering parameter.

### Metallic
PBR material metalness.

### Reflectance
Base reflection response.

### Ambient occlusion
Local cavity shadowing.

### Normal
Surface orientation.

### Emissive
Self-light contribution.

### Height
Parallax/displacement input.

### Material mask
Packed texture/channel selecting material properties.

## Compatibility layers

### ENB incompatibility
Current Community Shaders core documentation states ENBSeries and CS core are incompatible; CS detects ENB and disables to avoid crashes.

### ReShade compatibility
Current CS supports ReShade when full add-on support build is used.

### Effect overlap
ReShade/CS both apply similar sharpening/AO/tonemap, causing doubled effect.

### Shader framework feature conflict
Two CS features or external plugins modify same pass/resource; current version docs decide supported combinations.

### VR path
CS supports VR with runtime-specific render/camera differences; feature parity can vary.

## Render debugging

### RenderDoc capture
Inspect D3D11 draw calls/resources/shaders.

### Shader debug view
Feature-provided visualization of normals, masks, GI, etc.

### G-buffer visualization
Display albedo/normal/roughness/masks to identify material-data errors.

### GPU timing
Measure each pass cost.

### Tracy
Current CS source includes Tracy instrumentation for CPU/GPU zones.

### Render target corruption
Feature binds/reuses resource incorrectly, causing black/flickering output.

### Resource hazard
Same resource simultaneously bound for incompatible read/write roles.

### State leak
Hook/feature fails to restore blend/depth/targets before vanilla renderer continues.

## Diagnostic rules

1. Record exact CS core + feature versions together.
2. Separate shader compilation stutter from ordinary CPU/streaming stutter.
3. Material bug can originate in NIF/texture data even when render pass is correct.
4. Temporal artifacts depend on motion vectors/history/disocclusion, not just static shader color.
5. ENB/CS incompatibility is renderer-core level, not plugin load-order conflict.
6. ReShade post-processing happens at a different layer from most CS engine features.
7. Use render-target/debug views before guessing which feature is wrong.
8. When a feature works in third person but not first person/reflections/water, inspect special render paths.

## Sources

- Community Shaders upstream: https://github.com/community-shaders/skyrim-community-shaders
- Deferred pipeline implementation: https://github.com/community-shaders/skyrim-community-shaders/blob/dev/src/Deferred.cpp
