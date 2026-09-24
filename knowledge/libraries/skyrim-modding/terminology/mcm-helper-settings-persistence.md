# Skyrim Modding Terminology — MCM Helper, Settings Persistence, and Declarative Configuration

Imported: 2026-09-24
Status: sourced deep-ingestion pass 26

## SkyUI MCM baseline

### MCM
SkyUI Mod Configuration Menu.

### SKI_ConfigBase
Traditional SkyUI Papyrus base class for mod configuration pages.

### OnConfigInit
MCM initialization lifecycle event.

### OnPageReset
Rebuild current MCM page controls.

### State option
Traditional MCM option backed by Papyrus script/save variables.

### Save-local MCM
Traditional menu whose settings live primarily inside Papyrus variables serialized into ESS.

### Preset
External copy of user settings that can be reloaded on another save/profile.

## MCM Helper

### MCM Helper
SKSE framework and Papyrus/UI support library designed to simplify MCM implementation and move many settings into external INI-backed configuration.

### MCM_ConfigBase
MCM Helper script base class used by supported menus.

### Config JSON
Declarative MCM layout/config data under `Data/MCM/Config/<mod-or-menu>/config.json` style paths.

### Settings INI
External INI file containing user setting values.

### Data/MCM/Settings
MCM Helper data/settings directory used by framework conventions.

### Declarative menu
Menu structure described by JSON/data instead of building every control imperatively in Papyrus.

### Setting path
Named INI section/key or framework identifier bound to one control.

### Binding
Connection between UI widget and persistent setting.

### Immediate persistence
Changing menu writes/updates external setting according to framework behavior rather than relying only on save serialization.

### Cross-save persistence
INI-backed value remains when user starts another save, unless profile/files differ.

### Settings Loader
Addon pattern using MCM Helper to expose an existing mod's INI values in MCM without rewriting core feature logic.

### MCM Settings Loader
Common naming convention for mods that add MCM Helper menus for INI-configured SKSE plugins.

### Native INI setting
Value read directly by SKSE DLL.

### MCM façade
UI changes same INI consumed by native plugin, keeping one source of truth.

### Save-game setting
Value intentionally unique per character and therefore not appropriate for a global INI unless keyed/profile-scoped.

## Config structure

### Page
Logical MCM page.

### Group
Visual grouping/header.

### Setting
UI control tied to stored value.

### Checkbox
Boolean setting.

### Slider
Numeric setting.

### Dropdown/menu
Enumerated option.

### Keymap
Input/control binding field.

### Text
Display-only or editable text where supported.

### Dependency/visibility rule
Show/enable option according to another setting/state.

### Translation key
Localized text token for labels/descriptions.

### Default value
Value used when settings file/key absent or reset requested.

### Reset to defaults
Framework/menu action restoring configured defaults.

## Persistence layers

### External INI
Configuration survives new game and often survives save deletion.

### MCM JSON
Author-defined layout/schema, not user state.

### Papyrus state
Quest/menu script variables still serialize when used.

### Native plugin state
DLL can maintain runtime cache derived from INI.

### Reload settings
Native/Papyrus code re-reads external config after change.

### Stale runtime cache
INI changed but DLL continues using previous value until reload/restart.

### Profile-specific settings
MO2 profile-local copies when mod manager/profile layout explicitly isolates them.

### Shared settings
Files in common mod/Data path affect every character/profile using same deployed file.

## Migration

### Renamed setting key
Old INI key no longer read; migration should copy/translate old value.

### Moved section
Key remains but section path changes.

### Type migration
Boolean/int/float/string representation changes.

### Default migration
Changing default must not silently overwrite an explicit user choice.

### Config version
Version in INI/JSON used to drive one-time migration.

### Removed setting
Old value can remain harmlessly on disk unless cleanup desired.

### Unknown setting
Newer/older version encounters key it does not understand; should fail safely.

## MergeMapper support

### MergeMapper-aware MCM
Modern MCM Helper supports mappings needed by merged-plugin scenarios in relevant form-reference APIs.

### Form setting
MCM/preset references a game Form and must resolve identity safely if plugin merge/load mapping changes.

## Traditional MCM vs MCM Helper

Traditional:
- menu script often stores values in save;
- new game can reset menu values;
- explicit preset support needed for portability.

MCM Helper:
- many settings live in INI externally;
- same settings can naturally carry across saves;
- native DLL and UI can share one setting store.

Neither model is universally better; save-specific state should remain save-specific.

## Failure modes

### MCM present but values reset
Writing to save variables instead of intended INI, wrong path/permissions, loader not writing, or another settings loader overwrites.

### MCM values persist across new games unexpectedly
Expected behavior when using shared external INI.

### Value changes in menu but behavior unchanged
Native plugin cached setting and needs explicit reload/restart.

### Duplicate settings loaders
Two addons manipulate same INI/menu values.

### Missing labels
Translation file/key missing.

### Blank MCM
JSON parse error, missing framework resources/scripts, version mismatch.

### Wrong defaults
Author changed config schema without migrating existing INI.

## Design rules

1. Decide whether each setting is global/profile-wide or save-specific.
2. Keep one canonical setting store.
3. Version external settings schema.
4. Preserve user values when defaults change.
5. Expose reload behavior clearly if DLL does not hot-reload.
6. Keep user settings separate from author config/menu layout.
7. Use mod-manager profile isolation deliberately rather than assuming it.

## Sources

- MCM Helper upstream: https://github.com/Exit-9B/MCM-Helper
- MCM Helper current file layout includes MCM/Config and MCM/Settings data.
- Declarative MCM Helper comparison: https://github.com/NYKevin/declarative-mcm-helper
