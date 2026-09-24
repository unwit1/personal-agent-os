# MCM Helper 1.6.3 — Config Schema, Value Sources, and Persistence

Imported: 2026-09-24
Pinned source commit: `a30334864ea46ab6ee9e74bca06187630b67c039`
Status: canonical MCM Helper persistence model

## Filesystem layout

### Declarative menu
`Data/MCM/Config/<ModName>/config.json`

Read by `ConfigStore`.

### Default Mod Settings
`Data/MCM/Config/<ModName>/settings.ini`

Read into the defaults store and current setting store.

### User Mod Settings
`Data/MCM/Settings/<ModName>.ini`

Loaded after defaults and written by ModSetting setters.

### Declarative keybind actions
`Data/MCM/Config/<ModName>/keybinds.json`

Defines what a named hotkey does.

### User key assignments
`Data/MCM/Settings/keybinds.json`

Stores registered key codes for mod/keybind IDs and writes the current MCM release code.

## Consequence

MCM Helper **ModSetting values are external filesystem state**. They can survive:
- new games;
- loading another character;
- ordinary save deletion;
- plugin reinstall if the settings files remain;
- save-cleaning operations.

They are not ordinary Papyrus VM variables merely because the MCM exposes them.

## Value source types

The current config schema defines these numeric value sources:

- `PropertyValueBool`
- `PropertyValueInt`
- `PropertyValueFloat`
- `ModSettingBool`
- `ModSettingInt`
- `ModSettingFloat`
- `GlobalValue`

### PropertyValueBool / Int / Float
Reads/writes an auto property on a script attached to the configured source Form.

This value can therefore be **save/VM state** depending on the owning script instance.

### ModSettingBool / Int / Float
Reads/writes MCM Helper's external INI setting store.

This is **cross-save filesystem state** unless profile/filesystem isolation makes it effectively profile-specific.

### GlobalValue
Reads/writes a Skyrim `GLOB` form.

Its current runtime value can be save-persistent and differ from the plugin's static default.

### Text values
String controls can bind to script properties or ModSetting strings depending current implementation/schema path. Verify the exact control definition; do not infer string persistence from the visible widget.

## Control types

Current schema control types:

- `empty`
- `header`
- `text`
- `toggle`
- `hiddenToggle`
- `slider`
- `stepper`
- `menu`
- `enum`
- `color`
- `keymap`
- `input`

Group conditions support nested:
- `OR`
- `AND`
- `ONLY`
- `NOT`

with behavior:
- `disable`
- `hide`
- `skip`

## Menu actions

Config controls support:
- `CallFunction`
- `CallGlobalFunction`

The action can call:
- a function on a script attached to a Form;
- a global Papyrus function.

Parameters may include the special `{value}` token.

## Keybind actions

The keybind schema supports:
- `CallFunction`
- `CallGlobalFunction`
- `SendEvent`
- `RunConsoleCommand`

So a configured key can:
- call a script-instance function;
- call a global function;
- dispatch a Papyrus event;
- execute a console command.

## Form references in JSON

The schema encodes forms as:
`PluginFile.esm|FormID`
(or .esp/.esl).

This makes the owning plugin explicit. Treat that string as a source identity, not as a current load-order-prefixed runtime FormID.

## Defaults and reset

`SettingStore` loads `settings.ini` under the mod's Config folder as defaults.

User settings override those defaults.

Reset/reload operations resolve against the default store and commit changed values back into the user settings file.

## Why settings can disagree

A visible control can point to one of several authorities:

1. external ModSetting INI;
2. Papyrus script property;
3. GlobalVariable;
4. derived runtime state updated by an action or `OnSettingChange`;
5. another game INI value changed by the mod itself.

For example, SkyUI's bundled config script reads MCM Helper ModSettings and then applies some values into SkyUI script state or game INI settings. The MCM value and the eventual consuming subsystem can therefore diverge if synchronization fails.

## Troubleshooting matrix

| Symptom | Likely authority to inspect |
|---|---|
| Setting survives every new game | `Data/MCM/Settings/<mod>.ini` |
| Reset restores unexpected value | `Data/MCM/Config/<mod>/settings.ini` default |
| Menu shows correct setting, feature unchanged | action / OnSettingChange / consuming subsystem |
| One save differs but INI is same | PropertyValue/Global/save-side consumer state |
| Hotkey returns after new game | `Data/MCM/Settings/keybinds.json` |
| Hotkey invokes wrong behavior | mod's `keybinds.json` action or conflicting registered key |
| Config appears as error page | config JSON parse/schema/provider requirement |
| Control hidden/disabled unexpectedly | groupCondition tree and source value |
| Wrong Form targeted | `Plugin|FormID` sourceForm identity |
| Removing save does not reset settings | expected for external ModSetting persistence |

## Profile/mod-manager implication

Whether these files are shared between MO2 profiles depends on how the mod manager/profile/deployment setup isolates the Data tree and generated files. Do not assume save separation also separates MCM Helper settings.

## Design guidance

- Use **ModSetting** for deliberately cross-save user preferences.
- Use **Papyrus properties / Globals** when state belongs to a save/game world.
- Keep one clear source of truth and derive runtime effects from it.
- Namespace setting IDs/sections.
- Ship defaults in Config; never overwrite user Settings during mod updates unless migration is intentional.
- Version config/keybind schemas and migrations.
