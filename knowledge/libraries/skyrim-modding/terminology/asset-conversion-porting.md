# Skyrim Modding Terminology — Asset Conversion and LE/SE/AE Porting

Imported: 2026-09-24
Status: sourced deep-ingestion pass 5

## Edition/runtime layers

### Skyrim LE
Original 32-bit Skyrim (“Legendary Edition” community shorthand) based on the older executable/render/asset ecosystem.

### Skyrim SE
64-bit Skyrim Special Edition runtime family.

### Skyrim AE
Community shorthand for later Skyrim SE 1.6+ runtime family and/or Anniversary content. Always distinguish runtime build from content ownership when discussing compatibility.

### Port
Adapting a mod or asset from one game/runtime generation to another.

### Backport
Adapting newer-format content to an older target such as SE assets back to LE where technically possible.

### Plugin conversion
Updating plugin record serialization/headers using the target Creation Kit/tooling where needed.

### Asset conversion
Transforming NIF, HKX, texture, archive, shader/material or other external data to formats accepted by the target runtime.

### Native-code port
Recompiling/reimplementing an SKSE DLL for a different runtime/ABI. Asset conversion tools cannot port native DLLs.

## NIF conversion

### LE NIF
Mesh using Skyrim LE-era NIF stream/version/block conventions.

### SE NIF
Mesh using Skyrim SE-compatible NIF conventions, frequently including BSTriShape-style optimized geometry.

### NiTriShape
Common older NIF geometry block used heavily by LE assets.

### BSTriShape
Bethesda-optimized triangle shape used by Skyrim SE assets.

### SSE NIF Optimizer
Tool by ousnius for optimizing/converting LE/SE NIF files and checking some texture compatibility issues.

### NIF optimization
Conversion/restructuring of mesh blocks for target-runtime compatibility/performance. It is not equivalent to artistic optimization or guaranteed reduction of polygon count.

### HeadPart mode
Special handling required by NIF conversion tools for head-part meshes because face/head geometry follows additional engine expectations.

### Skin partition conversion
Updating skinned mesh partition/vertex data to the target format.

### Collision conversion
Handling Havok/NIF collision data whose binary/version details may differ between LE and SE.

### NIF round trip
Converting SE→LE→SE or repeated optimization. Repeated conversions can lose/alter information; always retain originals.

## Cathedral Assets Optimizer

### CAO
**Expansion:** Cathedral Assets Optimizer. Tool designed to automate Bethesda asset conversion/optimization, including Skyrim LE↔SE workflows, BSA creation/extraction, NIF processing and texture operations.

### CAO profile
Saved collection of conversion/optimization options for a particular task/game.

### CAO porting profile
Configuration intended to process an LE mod's assets for SE compatibility.

### CAO BSA profile
Configuration for unpacking/repacking assets using the target game's archive format.

### Texture optimization
Resizing/recompressing/fixing texture properties. “Optimize” should not mean indiscriminate quality reduction.

### Mipmap generation
Creating lower-resolution levels required for correct texture sampling at distance.

### Texture resizing
Reducing dimensions to lower disk/VRAM cost. Preserve aspect ratio and texture-role constraints.

### Texture compression conversion
Re-encoding DDS into another block-compression format suitable for content and target renderer.

### BC1 / DXT1
Block compression suitable for many opaque/simple-alpha color textures.

### BC3 / DXT5
Block compression supporting fuller alpha channels.

### BC4
Single-channel compression useful for grayscale masks/data.

### BC5
Two-channel compression often suitable for tangent-space normal XY data.

### BC7
Higher-quality block compression available in DirectX 11-era pipelines and widely used in SE texture workflows.

### Uncompressed DDS
Texture stored without block compression. Can be appropriate for special data but much larger in VRAM/disk footprint.

## Animation conversion

### LE HKX
Havok animation/behavior serialized for the LE-era environment.

### SE HKX
Havok animation/behavior serialized in a form accepted by Skyrim SE.

### Animation conversion
Converting animation assets between target Havok/runtime formats. Do not assume copying LE HKX directly into SE is safe.

### Behavior conversion
More complex than individual animation conversion because behavior graphs contain structures/references that patchers/frameworks may also alter.

### hkxcmd lineage
Historical Havok conversion tooling used by Skyrim asset utilities; current workflows may wrap equivalent conversion code inside CAO or newer tools.

## Texture compatibility

### DDS header
Metadata describing dimensions, format, mipmaps and data layout.

### DX10 DDS header
Extended DDS header used for newer DXGI formats such as BC7.

### Normal-map format
Compression/channel layout should preserve signed/tangent normal information appropriate for Skyrim's shader expectations.

### Cubemap format
Texture type requiring cube faces/layout metadata.

### Alpha channel
Transparency or mask/data channel whose purpose depends on the shader. Recompressing without understanding alpha use can break an asset.

### Mipmap chain
All progressively smaller levels. Missing/bad mipmaps can create shimmering, aliasing or incorrect distance appearance.

## Porting non-assets

### Papyrus compatibility
Many vanilla Papyrus scripts are source-compatible across LE/SE, but SKSE functions/framework APIs and compiled dependencies can differ.

### PEX compatibility
Compiled scripts can depend on native function availability and external framework versions; “PEX copied successfully” does not establish runtime compatibility.

### SKSE DLL incompatibility
LE SKSE DLLs are 32-bit/native binaries and cannot simply be converted into 64-bit SKSE64 plugins. Source-level porting/reimplementation is required.

### SKSE version dependency
SE/AE native plugins may still require rebuilds or multi-runtime relocation support for different executable versions.

### Form/version conversion
Resaving a plugin in target CK may update plugin records but does not validate scripts/assets/native binaries.

## Safe porting workflow

1. Preserve untouched source archive.
2. Inventory plugin files and every asset type.
3. Identify native DLLs/framework requirements first; a mod without source/native support may be fundamentally nonportable.
4. Load plugin in xEdit and check masters/errors.
5. Convert/resave plugin only when needed for target record compatibility.
6. Convert NIFs with head-part/special-case awareness.
7. Convert animations/behaviors appropriately.
8. Validate DDS formats/mipmaps rather than recompressing everything blindly.
9. Repack BSA for the target game if archives are used.
10. Validate Papyrus/framework dependencies.
11. Generate FaceGen again if NPC records/headparts require it.
12. Test clean/new game first, then migration/existing saves only if the port promises that support.
13. Inspect logs and xEdit after testing.
14. Keep a manifest of every conversion operation.

## Diagnostic rules

1. “Form 44” is not proof of a complete SE port.
2. A mod may work as loose files but fail after BSA packing because archive format/name/path is wrong.
3. Native DLLs are a hard stop unless a compatible build/source port exists.
4. Head meshes, skinned armor and collision deserve special NIF validation.
5. Do not run bulk destructive optimization over a full mod setup; process a copy or isolated mod folder.
6. Keep original assets for rollback/comparison.
7. Quality/performance texture choices depend on the texture's semantic role, not simply largest resolution.

## Sources

- Cathedral Assets Optimizer: https://github.com/Guekka/cathedral-assets-optimizer
- SSE NIF Optimizer: https://github.com/ousnius/SSE-NIF-Optimizer
- NIF optimization conversion example: https://github.com/opparco/nifopt
- Creation Kit Wiki packaging/asset paths: https://ck.uesp.net/wiki/File_menu
- xEdit documentation: https://tes5edit.github.io/docs/

## Dated tooling note

The SSE NIF Optimizer repository observed in September 2026 is still maintained/buildable with current Visual C++ tooling and explicitly describes itself as optimizing LE/SE NIFs and scanning textures for compatibility. CAO's upstream README describes automated Skyrim/Skyrim SE asset conversion but warns its development documentation may lag current behavior. Always pin the actual tool release used for a reproducible port.
