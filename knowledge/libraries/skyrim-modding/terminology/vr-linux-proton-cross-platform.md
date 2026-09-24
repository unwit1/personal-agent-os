# Skyrim Modding Terminology — VR, Linux, Proton, and Cross-Platform Environments

Imported: 2026-09-24
Status: sourced deep-ingestion pass 7

## Skyrim VR

### Skyrim VR
Separate Skyrim runtime/executable with VR-specific engine layouts, UI/input/rendering and gameplay behavior. It is not merely SE with a headset flag.

### SKSEVR
Skyrim Script Extender build/runtime for Skyrim VR.

### VR Address Library
Community address database mapping known Skyrim SE Address Library IDs/addresses to corresponding Skyrim VR addresses where reverse engineering has identified them.

### VR address confidence
VR Address Library data includes confidence/status information for mappings. A numeric mapping should not be treated as equally validated merely because it exists.

### CommonLibVR
CommonLib branch/fork family exposing reverse-engineered VR types/functions to native-plugin developers.

### CommonLibSSE-NG VR target
NG builds can target VR as well as SE/AE, but only functionality/structures actually supported across selected runtimes are safe to use without runtime-specific handling.

### VR-specific ABI
Structures/functions present or laid out differently in VR. Multi-runtime C++ code must avoid assuming flat-screen SE/AE layouts.

### VR-only feature
Engine/input/rendering behavior existing only in VR and requiring runtime feature detection.

### HMD
Head-mounted display; source of camera/head pose and VR-specific presentation behavior.

### VR controller
Tracked input device replacing/augmenting keyboard/mouse/gamepad assumptions.

### VR input mapping
Control binding semantics differ from flat-screen Skyrim; UI/hotkey mods may need explicit VR support.

### VR camera
Camera/player-body relationship differs significantly from flat-screen Skyrim and can invalidate camera/body mods that assume SE behavior.

### VR UI
Menus/Scaleform interaction can require VR-specific positioning/input handling.

### VR physics/performance
Stereo rendering and headset refresh targets make rendering/physics costs different from flat-screen performance expectations.

## Cross-runtime native development

### Flat-rim
Community shorthand for non-VR Skyrim SE/AE builds.

### Multi-target DLL
Native plugin compiled to support several executable families from one binary.

### Runtime probe
Code checking current executable/runtime before selecting offsets, structure access or feature behavior.

### Runtime-specific branch
Code path compiled or chosen specifically for SE, AE, GOG or VR.

### ABI abstraction
CommonLib layer hiding known runtime-specific struct-layout/function differences.

### Incomplete abstraction
Engine area not fully reverse-engineered or normalized across runtimes. Plugin must avoid it or provide runtime-specific implementation.

### VR Address Tools
Tooling used to compare/generate VR address mappings from SSE/Address Library data.

### Cross-runtime test matrix
Native project should test actual supported executables, not just compile successfully for them.

## Linux / Proton

### Proton
Valve Wine-based compatibility environment for running Windows games on Linux/SteamOS.

### Wine prefix
Per-application Windows-like filesystem/registry environment used by Wine/Proton.

### Proton prefix / compatdata
Steam-managed prefix/data for a game under its AppID.

### Proton version
Specific Proton runtime release. Native injectors/renderers/tools can work on one Proton release and fail on another.

### Proton-GE
Community Proton distribution containing additional patches/codecs/workarounds. Behavior should not be assumed identical to Valve Proton.

### Steam Deck
SteamOS/Linux handheld platform; Skyrim can be heavily modded but tool installation, filesystem paths, performance and UI differ from desktop Windows.

### protontricks
Utility for installing/configuring Windows components inside a Proton prefix.

### protontricks-launcher
Integration used by some Linux MO2 installers to route Windows executables/NXM handling into the correct Proton environment.

### Proton Shunt
Technique/tooling used by Linux mod-manager installers so launching Skyrim through Steam routes through MO2/modded launcher first.

### DXVK
Direct3D-to-Vulkan translation layer commonly used by Proton for D3D11 Skyrim rendering.

### Vulkan
Graphics API used underneath DXVK on Linux.

### Wine path
Windows-style path exposed inside a Wine/Proton prefix, mapped to Linux filesystem locations.

### Case-sensitive filesystem
Linux filesystems generally distinguish filename case. Mods created/tested only on Windows may contain path-case inconsistencies that become visible under Proton/tooling.

### Symlink
Linux/filesystem symbolic link. Behavior and Windows-tool visibility can differ from NTFS junction/hardlink assumptions.

### Proton environment variable
Launch-time variables controlling Wine/DXVK/Proton behavior.

### WINEDLLOVERRIDES
Wine setting used to choose native vs built-in Windows DLL behavior. Root injectors/proxies can depend on correct override configuration.

### DLL proxy under Proton
Windows DLL such as d3d11/dinput proxy loaded through Wine/Proton. Injection behavior can differ from native Windows.

### Prefix contamination
Installing unrelated components/settings into a game prefix can change behavior; preserve reproducible prefix configuration.

## MO2 on Linux

### Linux MO2 installer
Community setup that installs/runs Windows MO2 inside Wine/Proton and configures Skyrim/Script Extender launch routing.

### Proton MO2 installer
Installer ecosystem configuring MO2, LOOT, SKSE and helper utilities within the game's Proton context.

### NXM association
Browser-to-mod-manager URL handler. Under Linux it requires desktop/protocol routing into the correct MO2 instance.

### Tool prefix consistency
BodySlide, DynDOLOD, Nemesis/Pandora and similar Windows tools should run in an environment that sees the same game/MO2 paths and virtual filesystem assumptions.

### Java patcher mapping
Linux MO2 installers may expose Java inside the Wine environment for Java-based/proc patchers.

### Flatpak Steam
Sandboxed Steam distribution whose filesystem/portal restrictions can break installers expecting ordinary host paths; support is tool-specific.

## Graphics/injector compatibility under Proton

### DXVK injector interaction
ENB, ReShade, Community Shaders, overlays and other DirectX hooks operate through/alongside DXVK rather than native D3D11 and can expose Proton-version-specific behavior.

### Proton rendering regression
Game/mod stack works under one Proton version but fails after a Proton update without any mod changes.

### Pin Proton version
Troubleshooting/reproducibility practice of testing/holding a known working Proton release rather than automatically assuming latest is best.

### Native Linux driver
Mesa/proprietary NVIDIA/AMD driver version is another variable in rendering crashes/performance.

### Shader cache
Proton/DXVK/driver shader cache can affect first-run stutter and behavior after upgrades.

### Overlay incompatibility
MangoHud, Gamescope, Steam overlay and other Linux presentation layers can interact with Windows injectors.

## Filesystem and tools

### NTFS vs Linux filesystem
Some Wine/Proton setups place games/mods on NTFS while the prefix lives on ext4/btrfs. Permissions, hardlinks, case behavior and mount options can affect mod-manager deployment.

### Same-filesystem hardlink requirement
Vortex hardlink deployment requires source/staging and destination support hardlinks on the same filesystem context; this can be awkward under Linux/Wine and should be validated.

### Path translation
Mapping between Linux host paths and Wine drive letters.

### Wine drive
Drive mapping such as C: or Z: visible to Windows tools.

### Long path / special character issue
Tool failure caused by translated paths, Unicode, spaces, shell escaping or Wine path behavior rather than Skyrim data itself.

### Executable bit
Linux host permission needed for native scripts/tools; unrelated to Windows EXE permissions inside Wine but can affect helper wrappers.

## Diagnostic rules

1. Treat Skyrim VR as its own runtime target; do not infer VR support from “works on SE/AE.”
2. Exact VR Address Library/CommonLib support must be checked for native DLL features.
3. Under Proton, add Proton version, Wine prefix, Linux distro/SteamOS and GPU driver to the environment fingerprint.
4. If a Windows-native graphics mod fails under Proton, test a known-good Proton version before changing the load order.
5. Path case and translated filesystem paths are real compatibility variables on Linux.
6. MO2/tools must operate in a consistent prefix/path environment.
7. Vortex hardlink assumptions need explicit verification on Linux filesystems/Wine.
8. A compile-time multi-runtime claim still requires real VR/SE/AE execution tests.

## Sources

- VR Address Library: https://github.com/alandtse/skyrim_vr_address_library
- CommonLibSSE-NG VR/multi-runtime ecosystem: https://github.com/alandtse/CommonLibSSE-NG
- Furglitch MO2 Linux installer: https://github.com/Furglitch/modorganizer2-linux-installer
- Proton MO2 installer: https://github.com/ralgar/proton-mo2-installer
- Valve Proton compatibility tracker: https://github.com/ValveSoftware/Proton

## Dated compatibility evidence

A June 2026 Valve Proton issue documented a Skyrim Special Edition setup with Community Shaders that froze before the main menu under Proton 11 while the same installation worked under Proton 10 and also worked under Proton 11 after disabling Community Shaders. This is evidence that Proton/runtime/injector version can be the discriminating variable; it is not a universal statement that Community Shaders is incompatible with Proton 11.
