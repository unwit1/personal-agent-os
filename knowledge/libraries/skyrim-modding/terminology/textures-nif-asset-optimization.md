# Skyrim Modding Knowledge — Textures, NIF Materials, Asset Optimization, and LE-to-SE Conversion

Imported: 2026-09-24
Status: sourced encyclopedia pass 4

This module deepens mesh/texture knowledge with compression, mipmaps, alpha, shaders, NIF conversion and asset optimization.

## DDS and texture fundamentals

### DDS
DirectDraw Surface container used by Skyrim for GPU-ready texture data and mipmaps.

### Diffuse/albedo texture
Base surface color texture. Traditional Skyrim uses diffuse-centric material workflows; modern shader ecosystems may reinterpret/add physically based data.

### Normal map
Tangent-space surface-normal detail used for lighting.

### Specular
Surface reflection intensity/highlight contribution, stored/configured differently by shader/material setup.

### Glossiness
Controls sharpness/spread of specular reflections in traditional shader models.

### Environment mask
Texture/channel controlling cubemap/environment reflection contribution.

### Glow/emissive map
Texture controlling self-illuminated surface regions.

### Height/parallax map
Texture encoding surface-height information for parallax displacement techniques.

### Subsurface/tint texture
Texture channels/assets used by skin/foliage/special shader systems for color/translucency behavior.

### Alpha channel
Fourth texture channel commonly used for transparency, masks or material-specific data.

### Mipmap
Precomputed lower-resolution version of a texture used at distance/smaller screen size.

### Mip chain
Complete sequence from full resolution down to small levels.

### Missing mipmaps
Texture has no lower-resolution levels, often causing shimmering/cache/performance issues at distance.

### Alpha coverage
Preserving apparent coverage of cutout textures across mip levels so leaves/grass/fences do not vanish or thicken unpredictably.

### Texture dimensions
Width/height; powers of two remain common and often optimal/required by specific tooling/material paths.

## Compression formats

### BC1 / DXT1
Block compression suitable for RGB textures and simple 1-bit alpha, relatively small.

### BC2 / DXT3
Legacy block compression with explicit alpha; uncommon modern choice.

### BC3 / DXT5
Block compression with interpolated alpha, common for diffuse/alpha and historic normal-map workflows.

### BC4
Single-channel block compression useful for grayscale mask/data textures.

### BC5
Two-channel high-quality compression well suited to tangent-space normal X/Y channels; blue/Z can be reconstructed by shader/tool. SE/DX11 supports it.

### BC7
Higher-quality block compression available to Skyrim SE's DX11 renderer, useful especially for high-quality diffuse/color textures.

### Uncompressed RGBA
No block compression; largest memory/disk footprint and usually unnecessary for ordinary game textures.

### sRGB
Gamma-encoded color interpretation appropriate for color/albedo content.

### Linear data
Non-color texture data such as normals/masks should generally be interpreted without sRGB gamma transforms.

### Compression artifact
Visible block/ringing/banding error introduced by lossy texture compression.

## NIF material and shader properties

### BSLightingShaderProperty
Bethesda NIF property controlling Skyrim lighting shader behavior for a mesh shape.

### BSEffectShaderProperty
Shader property used for effect/emissive/particle-like material paths.

### Shader Type
BSLightingShaderProperty mode selecting specialized behavior such as environment mapping, skin tint, hair tint, parallax or other engine-defined variants.

### Shader Flags 1 / SLSF1
Bitfield enabling rendering/material behaviors.

### Shader Flags 2 / SLSF2
Second shader behavior bitfield.

### Texture Set
NIF-linked BSShaderTextureSet containing ordered texture slots for the shader.

### BSShaderTextureSet
NIF block storing texture paths consumed by Bethesda shader property.

### Texture slot
Position in the texture set with shader-specific meaning.

### Specular color
Material parameter tinting/intensifying specular reflection.

### Specular strength
Material parameter controlling reflection intensity.

### Glossiness
NIF material scalar controlling highlight tightness in traditional lighting shader.

### Emissive color
Self-light color used by supported shader paths.

### Emissive multiple
Multiplier for emissive brightness.

### UV scale
Multiplier applied to mesh texture coordinates.

### UV offset
Translation applied to texture coordinates.

### NiAlphaProperty
NIF property controlling alpha blending/testing and threshold behavior.

### Alpha test
Discard pixel based on alpha threshold, common for foliage/cutout surfaces.

### Alpha blend
Blend partially transparent pixels with background.

### Alpha threshold
Cutoff value for alpha-tested pixels.

### Double sided
Shader/shape state rendering both face orientations rather than culling backfaces.

### Vertex Colors flag
Shader uses per-vertex color/alpha data.

### Soft Lighting
Shader flag/parameter influencing lighting response in applicable materials.

### Rim Lighting
Edge-light effect used by some Skyrim material paths.

### Back Lighting
Light contribution from opposite side used by foliage/skin-like materials.

### Environment Mapping
Cubemap-based reflection shader behavior.

### Eye Environment Mapping
Special eye shader path.

### Parallax
Vanilla parallax shader mode using height data; compatibility differs among SE shader mods and mesh flags.

## NIF optimization and conversion

### Skyrim LE NIF
Model serialized/flagged for 32-bit/old Skyrim's NIF conventions.

### Skyrim SE NIF
Model converted to SE-compatible geometry/block/version conventions.

### SSE NIF Optimizer
Historic/community tool converting many LE meshes to Skyrim SE format and performing optimization.

### Cathedral Assets Optimizer / CAO
Batch tool automating mesh/texture/archive conversion and optimization between Bethesda game targets including Skyrim LE and SE.

### NIF version
Header/user-version values identifying game-era NIF serialization.

### BSTriShape conversion
Common SE optimization replacing older geometry block representations with Bethesda SE-appropriate BSTriShape forms where valid.

### Skinned mesh
Mesh with bones/weights. Conversion must preserve skin partitions/weights/skeleton compatibility.

### Static mesh
Non-skinned world/object model; generally simpler to optimize/convert.

### Particle mesh
Effect mesh/controllers whose conversion can be more fragile than static geometry.

### Havok collision conversion
Physics/collision blocks can require game-version-specific conversion; blindly changing NIF header/version is not sufficient.

### LE-to-SE port
Process of converting plugin form versions/assets/animations/textures as needed for SE; it is not merely opening/saving the ESP.

### SE-to-LE backport
Harder reverse conversion because newer asset/record/runtime features may not exist in LE.

### HKX conversion
Animation/behavior assets may require Skyrim-version-specific Havok conversion when moving between LE/SE.

### Form 43
Community shorthand for older Skyrim/Creation Kit plugin form version commonly seen in LE-authored plugins.

### Form 44
Community shorthand for Skyrim SE Creation Kit plugin form version.

### Resave in SE Creation Kit
Workflow updating plugin serialization/form version. It does not automatically repair incompatible meshes/animations/scripts.

## Optimization

### Downscale
Reduce texture resolution.

### Resize filter
Algorithm used to resample textures while preserving quality/alpha/normal characteristics.

### Normal-map renormalization
After resizing/compressing normal data, vectors should remain normalized/valid.

### Texture optimization
Choosing suitable dimensions/compression/mipmaps rather than simply making every texture smaller.

### Mesh optimization
Reduce/convert geometry/data while preserving appearance/collision/skinning.

### Triangle count
Number of geometry triangles; one performance factor but not sufficient alone to predict runtime cost.

### Vertex count
Number of vertices; affected by UV seams/hard normals/skin partitions and can exceed visually obvious geometry points.

### Draw-call split
Multiple shapes/materials can require separate draw calls even if one NIF has modest triangle count.

### Material count
Number of separate shader/material states contributing to draw-call cost.

### Texture memory footprint
GPU memory usage depends on resolution, compression format, mip chain and array/cubemap dimensions.

### 4K texture
4096×4096 texture. Appropriate resolution depends on object screen coverage/UV density, not marketing labels.

### Texel density
Texture pixels allocated per unit of model surface; helps choose rational resolution.

## Asset-conversion rules encoded for Agent OS

1. Never treat changing a NIF header version as complete LE→SE conversion.
2. Validate collision, skinning, controllers and shader properties after conversion.
3. Preserve/build mipmaps for ordinary world textures.
4. Use color compression and data/normal compression according to channel semantics.
5. BC7/BC5 are SE/DX11-era options and should not be recommended for LE compatibility.
6. A visually green/yellow BC5 normal in a generic image viewer can be correct two-channel data, not corruption.
7. Large texture resolution should be justified by texel density/screen coverage.
8. Alpha-tested foliage needs careful mipmap alpha coverage.
9. Optimize source assets in a copy/output mod and compare before/after in game.
10. Generated LOD textures have their own constraints; don't apply full-model texture assumptions blindly.

## Sources

- Cathedral Assets Optimizer: https://github.com/Guekka/Cathedral-Assets-Optimizer
- NifSkope: https://github.com/niftools/nifskope
- NifSkope architecture: https://github.com/niftools/nifskope/blob/develop/DOXYGEN.md
- BethesdaLibrary texture/material technical notes: https://github.com/BadDogSkyrim/BethesdaLibrary/blob/main/docs/file-formats/textures-materials.md
- DynDOLOD texture-resolution documentation: https://dyndolod.info/Help/Texture-Resolution
