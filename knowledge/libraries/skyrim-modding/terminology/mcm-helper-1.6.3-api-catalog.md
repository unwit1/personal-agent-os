# MCM Helper 1.6.3 — Public Papyrus API Catalog

Imported: 2026-09-24
Pinned source commit: `a30334864ea46ab6ee9e74bca06187630b67c039`
Status: finite source-derived public API

## Counts

| Script | Declarations |
|---|---:|
| MCM | 10 |
| MCM_ConfigBase | 15 |
| SKI_ConfigBase | 10 |
| SKI_ConfigMenu | 17 |
| SKI_QuestBase | 6 |

Total indexed function/event declarations: **58**

## MCM

Source: `scripts/public/MCM.psc` — blob `da22ff3d5114101017302201149b44ee44ba07f1`

| Line | Kind | Name | Declaration |
|---:|---|---|---|
| 4 | function | `IsInstalled` | `bool Function IsInstalled() native global` |
| 7 | function | `GetVersionCode` | `int Function GetVersionCode() native global` |
| 14 | function | `GetModSettingInt` | `int Function GetModSettingInt(string a_modName, string a_settingName) native global` |
| 15 | function | `GetModSettingBool` | `bool Function GetModSettingBool(string a_modName, string a_settingName) native global` |
| 16 | function | `GetModSettingFloat` | `float Function GetModSettingFloat(string a_modName, string a_settingName) native global` |
| 17 | function | `GetModSettingString` | `string Function GetModSettingString(string a_modName, string a_settingName) native global` |
| 20 | function | `SetModSettingInt` | `Function SetModSettingInt(string a_modName, string a_settingName, int a_value) native global` |
| 21 | function | `SetModSettingBool` | `Function SetModSettingBool(string a_modName, string a_settingName, bool a_value) native global` |
| 22 | function | `SetModSettingFloat` | `Function SetModSettingFloat(string a_modName, string a_settingName, float a_value) native global` |
| 23 | function | `SetModSettingString` | `Function SetModSettingString(string a_modName, string a_settingName, string a_value) native global` |

## MCM_ConfigBase

Source: `scripts/public/MCM_ConfigBase.psc` — blob `5cd277f23729a2229ee67a21d14691eaa4ceaa33`

| Line | Kind | Name | Declaration |
|---:|---|---|---|
| 8 | event | `OnSettingChange` | `Event OnSettingChange(string a_ID)` |
| 12 | event | `OnPageSelect` | `Event OnPageSelect(string a_page)` |
| 16 | event | `OnConfigInit` | `Event OnConfigInit()` |
| 20 | event | `OnConfigOpen` | `Event OnConfigOpen()` |
| 24 | event | `OnConfigClose` | `Event OnConfigClose()` |
| 33 | function | `RefreshMenu` | `Function RefreshMenu() native` |
| 37 | function | `SetMenuOptions` | `Function SetMenuOptions(string a_ID, string[] a_options, string[] a_shortNames = None) native` |
| 44 | function | `GetModSettingInt` | `int Function GetModSettingInt(string a_settingName) native` |
| 45 | function | `GetModSettingBool` | `bool Function GetModSettingBool(string a_settingName) native` |
| 46 | function | `GetModSettingFloat` | `float Function GetModSettingFloat(string a_settingName) native` |
| 47 | function | `GetModSettingString` | `string Function GetModSettingString(string a_settingName) native` |
| 50 | function | `SetModSettingInt` | `Function SetModSettingInt(string a_settingName, int a_value) native` |
| 51 | function | `SetModSettingBool` | `Function SetModSettingBool(string a_settingName, bool a_value) native` |
| 52 | function | `SetModSettingFloat` | `Function SetModSettingFloat(string a_settingName, float a_value) native` |
| 53 | function | `SetModSettingString` | `Function SetModSettingString(string a_settingName, string a_value) native` |

## SKI_ConfigBase

Source: `scripts/public/SKI_ConfigBase.psc` — blob `87f2f211cee2458ba40ddcbb85a4342c97af2553`

| Line | Kind | Name | Declaration |
|---:|---|---|---|
| 23 | function | `get` | `string function get()` |
| 32 | event | `OnConfigInit` | `event OnConfigInit()` |
| 37 | event | `OnConfigOpen` | `event OnConfigOpen()` |
| 42 | event | `OnConfigClose` | `event OnConfigClose()` |
| 47 | event | `OnVersionUpdate` | `event OnVersionUpdate(int aVersion)` |
| 55 | function | `GetVersion` | `int function GetVersion()` |
| 60 | function | `ForcePageReset` | `function ForcePageReset()` |
| 65 | function | `SetTitleText` | `function SetTitleText(string a_text)` |
| 70 | function | `ShowMessage` | `bool function ShowMessage(string a_message, bool a_withCancel = true, string a_acceptLabel = "$Accept", string a_cancelLabel = "$Cancel")` |
| 77 | function | `Guard` | `function Guard()` |

## SKI_ConfigMenu

Source: `scripts/public/SKI_ConfigMenu.psc` — blob `80f8e681b8681778dcc72ec850ec37679e2a2cca`

| Line | Kind | Name | Declaration |
|---:|---|---|---|
| 5 | function | `GetVersion` | `int function GetVersion()` |
| 88 | event | `OnConfigInit` | `event OnConfigInit()` |
| 141 | event | `OnGameReload` | `event OnGameReload()` |
| 147 | event | `OnVersionUpdate` | `event OnVersionUpdate(int a_version)` |
| 153 | event | `OnConfigOpen` | `event OnConfigOpen()` |
| 164 | event | `OnSettingChange` | `event OnSettingChange(string a_ID)` |
| 280 | function | `ApplyItemListFontSize` | `function ApplyItemListFontSize(int a_value)` |
| 311 | function | `Apply3DItemXOffset` | `function Apply3DItemXOffset(float a_value)` |
| 326 | function | `Apply3DItemYOffset` | `function Apply3DItemYOffset(float a_value)` |
| 341 | function | `Apply3DItemScale` | `function Apply3DItemScale(float a_value)` |
| 355 | function | `ChooseFavoriteGroup` | `function ChooseFavoriteGroup(int a_value)` |
| 365 | function | `ToggleUnequipArmor` | `function ToggleUnequipArmor(bool a_value)` |
| 371 | function | `ToggleUnequipHands` | `function ToggleUnequipHands(bool a_value)` |
| 381 | function | `get` | `bool function get()` |
| 386 | function | `LoadSettings` | `function LoadSettings()` |
| 475 | function | `ApplySettings` | `function ApplySettings()` |
| 526 | function | `CheckGamepad` | `function CheckGamepad()` |

## SKI_QuestBase

Source: `scripts/public/SKI_QuestBase.psc` — blob `bb57000176bd59f9ecc2ce1f36242e5f79a54de7`

| Line | Kind | Name | Declaration |
|---:|---|---|---|
| 16 | event | `OnInit` | `event OnInit()` |
| 29 | function | `CheckVersion` | `function CheckVersion()` |
| 33 | function | `GetVersion` | `int function GetVersion()` |
| 37 | event | `OnVersionUpdate` | `event OnVersionUpdate(int a_version)` |
| 50 | event | `OnGameReload` | `event OnGameReload()` |
| 53 | function | `Guard` | `function Guard()` |


## Primary public MCM Helper additions

### MCM
Global native surface:
- installation/version detection;
- Get/Set ModSetting Int/Bool/Float/String.

### MCM_ConfigBase
Adds:
- `OnSettingChange`;
- page/config lifecycle events;
- `RefreshMenu`;
- dynamic `SetMenuOptions`;
- instance-scoped ModSetting getters/setters whose mod identity is inferred from the owning config quest/plugin.

### SkyUI compatibility classes
The repository ships public SkyUI base-script interfaces so dependent mods can compile against known API shapes without modifying/recompiling those base scripts.

## No-delay native registration

MCM Helper registers many simple setting accessors as no-delay native functions. Treat that as native implementation detail; scripts still require the DLL/provider to load.

## Diagnostic rules

1. `MCM.IsInstalled()` verifies native provider availability, not the correctness of one mod's config JSON.
2. A valid `MCM_ConfigBase` script can still display an error page if `config.json` fails schema/parse processing.
3. `OnSettingChange` is emitted after MCM Helper changes a control and is the correct place for a script to synchronize derived runtime state.
4. If a mod changes a ModSetting outside the menu, call `RefreshMenu()` when the open menu must reflect it.
5. ModSetting APIs address filesystem-backed MCM settings; they are not generic Papyrus variable accessors.
