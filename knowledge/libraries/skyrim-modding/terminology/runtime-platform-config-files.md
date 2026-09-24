# Skyrim Modding Knowledge — Runtime Families, Game Configuration, INIs, Plugin Lists, and Update Compatibility

Imported: 2026-09-24
Status: encyclopedia pass 6

## Runtime/edition vocabulary

### Skyrim Legendary Edition / LE
32-bit original Skyrim (2011) plus DLC ecosystem, using TESV.exe and 32-bit SKSE. Asset/plugin/runtime assumptions differ substantially from 64-bit Special Edition.

### Skyrim Special Edition / SSE / SE
64-bit Skyrim released in 2016. In technical native-modding discussion, “SE” is often overloaded to mean pre-1.6 runtime family, especially 1.5.97; exact executable version should be used instead.

### Anniversary Edition / AE
Commercial content bundle/branding introduced with the 10th-anniversary release. In native-mod community shorthand, “AE runtime” often means Skyrim 1.6+ executable family, even for users who did not purchase every Anniversary bundle item.

### Skyrim VR
Separate executable/runtime with VR-specific engine layouts/features and its own SKSEVR/Address Library ecosystem.

### GOG build
DRM-free GOG distribution with runtime build numbers/addresses that can differ from Steam.

### Steam build
Steam-distributed Skyrim executable/version.

### Epic build
Epic Games Store distribution; SKSE/native support must be checked explicitly.

### Microsoft Store/Game Pass build
Distribution/install sandbox/runtime constraints can differ from Steam/GOG; native mod support depends on current SKSE/platform support.

### Runtime version
Exact executable version, e.g. 1.5.97, 1.6.1170, 1.7.99, etc. This is the key compatibility identifier for native DLLs.

### Game version vs content version
Executable build is separate from which Creation Club/Creations content is installed.

### Downgrade
Replacing current game executable/files with an older runtime to retain native-plugin compatibility. Must preserve a coherent set of executable/data files; partial downgrades can create mismatch.

### Update freeze
Operational practice of preventing automatic game updates for a stable modlist; platform-specific and not permanent protection if the launcher/store updates files.

### Stock game copy
Controlled duplicate of game runtime/data used by modlists to isolate from storefront updates.

## Skyrim configuration files

### Skyrim.ini
Primary game/system INI with engine/game configuration.

### SkyrimPrefs.ini
User preference/render/display/gameplay settings generated/managed by launcher/game.

### SkyrimCustom.ini
Optional user override INI loaded after base INI settings for supported keys, useful for avoiding direct edits to generated files.

### SKSE.ini
Configuration read by SKSE itself where applicable.

### Plugin INI
Mod-specific configuration placed beside DLL/data or under SKSE plugin paths.

### TOML
Modern structured config format used by tools/plugins such as current Engine Fixes.

### JSON
Structured configuration/data format used by many frameworks and MCM/tool ecosystems.

### YAML
Human-readable structured format used by some tooling/build workflows; not a core Skyrim runtime format by itself.

### INI section
Bracketed configuration group.

### INI key
Setting name/value under a section.

### Game Setting / GMST
Plugin-record engine/game tuning value, distinct from an INI setting.

### INI setting cache
Some settings are read/cached at startup or subsystem initialization; changing file/runtime value does not guarantee immediate effect.

### BethINI / BethINI Pie
Community configuration tool ecosystem for safely managing Skyrim INI/display/performance presets. Treat exact recommendations as tool/version/hardware dependent rather than canonical game truth.

## Load-order state files

### plugins.txt
Bethesda launcher/game plugin activation list/order file for supported runtime/manager environment.

### loadorder.txt
Load-order representation used by some Bethesda modding tools/managers; relationship to plugins.txt is manager/game specific.

### active plugin
Plugin enabled for game load.

### inactive plugin
Installed plugin not enabled/loaded.

### loadorder library
Tool API layer used by managers/LOOT to read/write Bethesda load-order files consistently.

### timestamp ordering
Older Bethesda games historically used file timestamps for plugin order; modern Skyrim SE manager workflows rely on plugins/load-order state rather than using timestamp folklore as a generic fix.

### locked load order
Manager feature preserving user/plugin relative order against automatic sorting.

## Creation Club / Creations

### Creation Club
Bethesda curated paid/free content system historically delivered as plugin/archive content.

### Creation
Current Bethesda umbrella terminology for downloadable mod/official content distributed through in-game/Bethesda services.

### Verified Creator / Verified Creation
Bethesda marketplace program terminology that can change over time; treat packaging/platform policies as current-service information rather than timeless plugin-format facts.

### ESL Creation
Many official Creation Club/Creation plugins use light-plugin format to reduce full plugin-slot use.

### Official master/content
Bethesda-shipped ESM/ESL data that can become a dependency for mods.

### Missing Creation
Save/plugin references official optional content that is not installed.

### Creation update
Official content may update independently or alongside game runtime and can change records/assets even when user's mod list did not intentionally change.

### _ResourcePack.esl
Modern Bethesda resource plugin associated with newer Creation Kit/Creation ecosystem content. Mods relying on it should declare the dependency explicitly and version-scope assumptions.

## Data paths and user paths

### Game root
Directory containing SkyrimSE.exe/skse loader and root DLL/proxy files.

### Data
Game data root containing plugins, BSAs and loose assets.

### Documents/My Games
User configuration/save/log location for normal Windows installs.

### Local AppData plugins state
Bethesda/manager load-order state may live under user-local application data depending on game/tool environment.

### SKSE log directory
Typically under Documents/My Games/Skyrim Special Edition/SKSE for many current SKSE/plugin logs.

### MO2 profile INIs
Profile-specific copy of Skyrim.ini/SkyrimPrefs.ini when profile-local INIs are enabled.

## Version compatibility terms

### Runtime-independent mod
Pure plugin/asset mod that does not rely on runtime-specific native binary behavior. It can still break across game-data/CK format changes.

### Runtime-dependent mod
Contains native SKSE DLL or executable hook requiring compatible runtime.

### Address-Library plugin
Native plugin resolves engine addresses through Address Library mappings, reducing but not eliminating runtime compatibility work.

### NG plugin
Common shorthand for CommonLibSSE-NG multi-runtime native plugin.

### Version check
Plugin loader/framework verifies current executable against declared support.

### Incompatible DLL warning
SKSE reports plugin disabled/rejected because version/dependency requirements are not met.

### Silent incompatibility
DLL loads but uses wrong assumptions/layouts and crashes/misbehaves; more dangerous than explicit loader rejection.

### DLL metadata version
Version embedded/reported by native plugin. It can lag package marketing version, so package/file hash/changelog may be needed.

## Update-safe workflow

1. Record exact game runtime and hashes before update.
2. Archive current root executable/DLL dependencies or maintain a controlled stock-game copy where licensing/platform permits.
3. Check SKSE, Address Library, Engine Fixes and every native DLL for explicit new-runtime support.
4. Keep old mod profile/save backup.
5. Update native foundations first.
6. Launch to main menu/new test save before opening valuable save.
7. Regenerate code/data outputs only if their tool/runtime/source inputs changed.
8. Inspect logs for rejected DLLs.
9. Update production save only after smoke tests.
10. Record the resulting runtime stack in Agent OS.

## Sources
- Official SKSE: https://skse.silverlock.org/
- CommonLibSSE-NG: https://github.com/alandtse/CommonLibSSE-NG
- xEdit: https://github.com/TES5Edit/TES5Edit
- Bethesda Skyrim/Anniversary information: https://elderscrolls.bethesda.net/skyrim10
