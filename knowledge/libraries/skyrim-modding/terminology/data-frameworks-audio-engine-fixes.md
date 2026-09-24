# Skyrim Modding Terminology — Data Frameworks, Audio/Voice, Engine Fixes, and Utilities

Imported: 2026-09-24
Status: sourced deep-ingestion pass 3

## Papyrus/native data frameworks

### JContainers
SKSE plugin/framework extending Papyrus with richer data structures and JSON-backed import/export capabilities.

### JMap
JContainers associative map/dictionary structure.

### JArray
JContainers dynamic array-like structure.

### JFormMap
JContainers map keyed by forms where supported.

### JObject
Generic JContainers object handle/reference used by the framework's container API.

### JDB
JContainers database/root-access patterns for sharing structured data between scripts.

### JContainers JSON import/export
Ability to load/save framework data through JSON files, allowing configuration/state exchange beyond ordinary Papyrus arrays/properties.

### JContainers garbage collector
Framework-owned memory/lifetime management for container objects implemented outside the vanilla Papyrus VM.

### PapyrusUtil
SKSE/Papyrus utility framework exposing additional array, string, file, JSON/storage and utility functions to Papyrus mods.

### StorageUtil
PapyrusUtil persistent/shared key-value storage API frequently used by scripts to associate data with forms or global keys.

### JsonUtil
PapyrusUtil JSON-file access API.

### Utility framework dependency
Shared native/Papyrus library mod that provides APIs used by many other mods. Updating/removing it can affect multiple dependent systems even if it has little visible content itself.

### Framework overwrite hazard
Installing an older bundled copy of PapyrusUtil/JContainers/etc. over a newer standalone version can silently downgrade runtime scripts/DLLs. Asset/file priority therefore matters for framework libraries.

### FISS
**Expansion:** FileAccess Interface for Skyrim Script. Framework historically used for saving/loading mod settings to external files so configuration could be transferred across saves.

### External configuration persistence
State stored in files outside the ESS/SKSE co-save, allowing settings to survive new saves but creating its own file-path/version/schema concerns.

## Engine Fixes

### SSE Engine Fixes
SKSE/native patch framework that modifies/fixes numerous Skyrim SE/AE engine behaviors at runtime.

### Engine Fixes Part 1 / Part 2
Common packaging split in which SKSE plugin files and root/preloader components are installed separately according to release instructions.

### SKSE plugin preloader
Root-level loader/injection component used by Engine Fixes to load required native code early in process startup.

### Preload hook
Hook running before normal SKSE plugin initialization for fixes requiring earlier engine/process access.

### Root-level mod
Mod placing files beside SkyrimSE.exe rather than only under Data. Ordinary Data-only mod managers may need special root-deployment support.

### Engine patch
Native binary/runtime modification correcting or changing engine behavior. It can be version-specific even when its config file stays identical.

### Memory manager patch
Engine Fixes functionality related to allocation/memory behavior. Exact options/version semantics must be checked against installed Engine Fixes documentation.

### Save-game fix
Engine Fixes family of patches affecting save behavior/limits/serialization edge cases. Do not enable/disable blindly without version-specific docs.

### Form cache / engine cache
Runtime engine caching behavior that some fixes alter to address limits or incorrect behavior.

### Plugin-limit mitigation
Engine/runtime fixes relating to traditional engine limits. Distinguish full plugin slots, light plugins, and separate engine data limits.

### OS/environment interaction
Native loaders can fail because of Windows filesystem paths, OneDrive/Documents redirection, antivirus, overlays, permissions, or other environment conditions unrelated to ESP load order.

## Audio and voice

### Sound Descriptor / SNDR
Game record defining a sound and how it is played, including references to sound files/output models/categories and related parameters.

### Sound Marker
Placed/world sound-emitter reference/object.

### Sound Category
Routing/category structure controlling groups such as music, dialogue, interface, effects, volume/muting behavior, etc.

### Output Model
Controls how sound is spatialized/routed, such as 2D/3D-style output behavior.

### VoiceType
Defines voice identity/category used to associate actors/talking activators with dialogue voice assets.

### Dialogue voice asset
Recorded voice file associated with a dialogue INFO response and VoiceType/plugin path conventions.

### Sound\Voice\<plugin>
Standard data path tree containing plugin-specific dialogue voice assets.

### FUZ
Bethesda voice archive/container format combining compressed voice audio and lip-sync data into one file.

### XWM
Compressed audio format used by Bethesda games, including dialogue/audio workflows.

### WAV
Uncompressed PCM audio used in authoring/conversion workflows and accepted by some CK pipelines.

### LIP
Lip-sync animation data associated with spoken dialogue.

### Lip generation
Creation Kit/dialogue tool process generating mouth/lip synchronization data from dialogue/audio/text. Tool/version behavior can vary.

### Silent voice
Audio asset containing silence but still providing timing/lip/voice-file presence needed by some dialogue systems.

### Fuz Ro D-oh
Common SKSE utility used by mod users/authors to provide subtitle timing/silent dialogue behavior when voiced assets are absent. Treat exact features/version as tool-specific.

### Dialogue subtitle
Text displayed for spoken/unvoiced dialogue depending on game settings and engine behavior.

### Voice asset mismatch
Correct INFO/VoiceType/plugin record exists but expected voice file path/name is absent or mismatched.

### Audio asset packaging hazard
Creation Kit packaging historically misses some `Sound\Voice\<plugin>` content, requiring manual validation of packaged files.

## Logging and diagnostics

### SKSE log
Log generated by SKSE itself describing loader/runtime/plugin operations.

### Native plugin log
Per-plugin log commonly written under Documents/My Games/Skyrim Special Edition/SKSE or another runtime-specific location.

### Preloader log
Early-loader diagnostic log useful when a DLL crashes/fails before standard SKSE plugin loading completes.

### Framework log
Runtime log emitted by frameworks such as SPID/KID/BOS/FLM/OAR/FSMP/JContainers, often the best evidence for parse/load/version errors.

### Environment-specific log path
Log/save/config locations can vary by Steam/GOG/VR/runtime and Windows Documents redirection; do not hard-code one path in troubleshooting.

## Diagnostic rules

1. Shared utility frameworks are transitive dependencies; inspect which version actually wins in the mod manager.
2. Data framework state may live outside ordinary Papyrus arrays and outside the main save; identify the storage layer before deleting/resetting data.
3. Engine Fixes is native/runtime code: exact runtime, build, preloader/root files and config version all matter.
4. If a native mod fails before the Bethesda logo, inspect loader/preloader/environment logs before changing ESP order.
5. Dialogue troubleshooting must check INFO/VoiceType plus actual Sound\Voice paths and FUZ/XWM/LIP assets.
6. CK packaging output should be audited manually for FaceGen, voice, scripts and other external assets.

## Sources

- JContainers upstream: https://github.com/ryobg/JContainers
- JContainers original project: https://github.com/SilverIce/JContainers
- PapyrusUtil Nexus/source lineage: original by meh321, maintained by exiledviper; validate current installed release documentation at implementation time.
- SSE Engine Fixes upstream: https://github.com/aers/EngineFixesSkyrim64
- Creation Kit Wiki File Menu / packaging notes: https://ck.uesp.net/wiki/File_menu
- Creation Kit Wiki Sound/voice-related record references: https://ck.uesp.net/wiki/Category:Sound
- Creation Kit Wiki TalkingActivator: https://ck.uesp.net/wiki/TalkingActivator

## Dated snapshot

JContainers v4.3.2 observed on 2026-09-24 explicitly lists compatibility with Skyrim 1.7.104 / SKSE 2.3.1, GOG 1.6.1179 / SKSE 2.2.6 and VR 1.4.15 / SKSE 2.0.12. Treat these as dated runtime compatibility facts, not permanent version guidance.
