# Skyrim Mod Packaging, Localization, and Release Workflow

Imported: 2026-09-24
Status: sourced authoring knowledge

## Release artifact model

A distributable Skyrim mod can contain several independent layers:

- plugin data: ESP/ESM/ESL;
- archives: BSA;
- loose assets: meshes, textures, scripts, interface, sound/voice;
- native DLLs and configs;
- Papyrus source and compiled PEX;
- localization string tables;
- FOMOD installer metadata;
- generated FaceGen/BodySlide/behavior/LOD outputs where intentionally shipped;
- documentation, changelog, license/credits and source links.

A release is incomplete if any runtime-required layer is omitted.

## Directory validation

### Data-relative layout
Archive root should normally mirror paths beneath Skyrim's Data directory rather than nesting an extra arbitrary folder.

### Plugin root placement
ESP/ESM/ESL belongs at Data root.

### Scripts path
Compiled Papyrus typically under `Data\Scripts`; source under the appropriate source tree when distributed.

### SKSE plugin path
Native DLLs generally under `Data\SKSE\Plugins`, while some preloaders/root components must live beside the executable.

### Interface path
SWF and related UI assets under `Data\Interface`.

### FaceGen paths
Meshes under `meshes\actors\character\FaceGenData\FaceGeom\<plugin>\`; tint textures under corresponding `textures\...\FaceTint\<plugin>\`.

### Voice path
Dialogue voice assets under `Sound\Voice\<PluginName.ext>\<VoiceType>\...`.

### Strings path
Localized tables under `Data\Strings\` with plugin/language-correct names.

## Packaging pitfalls

### CK packaging omission
Creation Kit packaging historically fails to include some external assets reliably, particularly FaceGen and voice folders and potentially scripts. Always compare final archive against an explicit manifest.

### Case/path mismatch
Windows is mostly case-insensitive, but tools/archive/listing pipelines can preserve inconsistent paths. Normalize paths for reproducibility and cross-platform/Proton environments.

### Accidental development files
Exclude logs, dumps, temp outputs, editor backups, private test scripts, source control metadata and machine-specific configs unless intentionally distributed.

### Stale generated output
Do not package BodySlide/Pandora/DynDOLOD/Synthesis output generated against an obsolete dependency set.

### Bundled dependency downgrade
Avoid shipping older copies of shared frameworks such as PapyrusUtil/JContainers unless the mod explicitly owns and versions them. Prefer documented external dependencies.

### Root files
DLL proxies/preloaders such as graphics injectors or Engine Fixes components may require game-root placement. FOMOD/manager instructions must make this explicit.

## FOMOD design

### Required option
Component necessary for the mod to work.

### Optional component
Feature that may be selected independently.

### Mutually exclusive options
Choices where only one target runtime/body/patch can be installed.

### Conditional dependency
Installer rule selecting files based on another installed plugin/file or prior choice.

### Runtime selector
Option choosing SE/AE/GOG/VR-compatible DLLs where one universal binary is not provided.

### Patch selector
Compatibility option installed only when the corresponding target mod is present.

### Installer validation
Test every meaningful FOMOD branch in an empty staging directory, not merely the author's usual option path.

## Localization release

### Source language
Canonical authored text language.

### String extraction
Moving localizable fields from plugin into external tables while retaining stable IDs.

### Translation update
Applying changed/new source strings without remapping unrelated IDs.

### String-table completeness
Every referenced ID resolves in every language advertised by the release.

### Fallback behavior
Do not assume Skyrim automatically falls back to English for every missing localized string.

### Localized plugin versioning
If string IDs change between releases, translations based on the prior plugin can silently map text incorrectly.

## Versioning

### Semantic version
Project version such as major.minor.patch. Useful when changes can be classified by compatibility impact.

### Runtime compatibility matrix
Table of Skyrim runtime, SKSE, Address Library and DLL build compatibility.

### Save compatibility
Explicit statement whether users can update on an existing save, need migration steps, or require a new game.

### Config migration
Instructions/code updating INI/JSON/SkyPatcher/SPID/OAR/etc. config semantics between releases.

### Breaking change
Change requiring user action, new save, regenerated output, updated dependency or incompatible API/config.

### Changelog
Human-readable record of user-impacting changes. Separate technical commit history from release migration instructions.

## Reproducible release checklist

- clean repository/worktree;
- exact version/tag recorded;
- dependencies pinned/documented;
- plugin masters checked;
- xEdit errors reviewed;
- plugin clean/dirty status intentional;
- scripts rebuilt from matching source;
- native DLL built against declared runtime targets;
- symbol/PDB retained privately or shipped as appropriate for diagnostics;
- assets converted for target;
- FaceGen regenerated where needed;
- localized tables regenerated/validated;
- FOMOD branches tested;
- BSA contents and naming verified;
- loose-vs-archive priority tested;
- new-game smoke test;
- existing-save migration test if supported;
- mod-manager install/uninstall test;
- logs reviewed;
- archive hash recorded;
- release notes include runtime/save requirements.

## Source and license hygiene

Preserve author permissions/licenses for third-party assets and code. “Modder's resource” does not imply unrestricted redistribution. Record source URL, author, version, license/permission and modifications for every incorporated external asset.

## Sources

- Creation Kit Wiki File Menu / packaging caveats: https://ck.uesp.net/wiki/File_menu
- Cathedral Assets Optimizer: https://github.com/Guekka/cathedral-assets-optimizer
- Wabbajack reproducibility concepts: https://github.com/wabbajack-tools/wabbajack
- CommonLibSSE-NG runtime targeting: https://github.com/alandtse/CommonLibSSE-NG
- xEdit localization/ONAM notes: https://tes5edit.github.io/whatsnew.html
