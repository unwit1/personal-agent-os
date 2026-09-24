# Skyrim Modding Knowledge — SkyUI, Scaleform, MCM, Input, and Interface Assets

Imported: 2026-09-24
Status: sourced encyclopedia pass 4

This module deepens UI knowledge from file-level SWF conflicts through SkyUI MCM APIs and native MCM Helper settings.

## Scaleform and UI architecture

### Scaleform GFx
Flash-derived middleware Skyrim uses for menu rendering and ActionScript-driven UI.

### SWF
Compiled Flash movie file used by Skyrim menus/interface assets.

### ActionScript
Programming language embedded in/used by SWF UI movies.

### GFxMovieView
Native Scaleform movie instance/interface exposed inside Skyrim runtime.

### UI menu
Runtime menu object such as InventoryMenu, MagicMenu, MapMenu, HUD Menu or custom mod menu.

### Menu registration
Native/UI manager association allowing a named menu to be created/opened.

### Menu stack
Set/order of active UI menus controlling input/pause/render behavior.

### Menu flags
Native behavior flags determining pause/input/cursor/render properties for a menu.

### Interface asset
Data/Interface path containing SWFs, translations, fonts and UI configuration.

### Interface conflict
Two mods provide same SWF/font/config path; asset winner decides actual UI code loaded.

### Flash injection
Modifying/replacing a menu SWF to insert additional ActionScript/components.

### Scaleform callback
ActionScript-to-native or native-to-ActionScript bridge invoked through SKSE/UI integration.

### RegisterForModEvent UI bridge
Pattern where UI/Papyrus/native layers communicate through SKSE mod events or callbacks.

## SkyUI

### SkyUI
UI overhaul/framework replacing major inventory/menu SWFs and providing common scripting/UI infrastructure.

### SKI_QuestBase
SkyUI Papyrus base class used by framework quests.

### SKI_ConfigBase
SkyUI public Papyrus base class for custom Mod Configuration Menus.

### MCM API version
SKI_ConfigBase exposes versioned API behavior; current script/header compatibility should be checked rather than assuming every historic example matches installed SkyUI.

### Mod Configuration Menu / MCM
SkyUI menu where mods expose settings through pages and option controls.

### MCM registration
Config script/quest becomes registered with SkyUI's Config Manager so it appears in the menu.

### OnConfigInit
MCM lifecycle event for initial menu configuration.

### OnConfigOpen
MCM event when the menu opens.

### OnConfigClose
MCM event when menu closes.

### OnPageReset
Event used to build/redraw one MCM page's controls.

### OnOptionSelect
Callback for selectable/toggle/action menu option.

### OnOptionSliderOpen
Callback preparing slider dialog/range/current value.

### OnOptionSliderAccept
Callback receiving accepted slider value.

### OnOptionMenuOpen
Callback preparing list/menu choices.

### OnOptionMenuAccept
Callback receiving menu selection.

### OnOptionKeyMapChange
Callback for keymap remapping.

### Option ID
Integer handle returned when adding an MCM option, later used to identify callbacks/update display.

### Option flags
Flags such as disabled/hidden/unmap-related behaviors exposed by SKI_ConfigBase.

### Page
Named MCM page selected through menu navigation.

### Header option
Noninteractive section-heading control.

### Text option
Label plus displayed value.

### Toggle option
Boolean menu control.

### Slider option
Numeric menu control with min/max/interval.

### Menu option
Choice/list menu control.

### Color option
Color picker/control.

### Keymap option
Keyboard/controller binding control.

### Input option
Text-input control where supported by helper/framework.

### State option
SkyUI convention using Papyrus states to handle option callbacks for a selected control.

### ForcePageReset
Request menu rebuild to reflect changed state.

## MCM Helper

### MCM Helper
Native/SKSE + Papyrus framework that simplifies SkyUI MCM creation and provides structured persistent settings.

### config.json
MCM Helper declarative menu layout/control description.

### settings.ini
Default mod settings file shipped under an MCM configuration path.

### MCM/Config
Data path containing mod-provided MCM Helper configuration definitions/defaults.

### MCM/Settings
Data path used for user-overridden/persistent settings INIs.

### ModSetting
MCM Helper setting bound to a named INI-backed value rather than only a script variable.

### Setting type prefix
MCM Helper/SkyUI-derived setting naming convention representing booleans, integers, floats, strings and other supported types.

### GlobalValue source
MCM Helper control setting whose value is stored in a Skyrim GlobalVariable form.

### Papyrus source
Menu option backed by Papyrus callbacks/variables rather than native ModSetting persistence.

### Persistent setting
Value preserved through MCM Helper's setting files/framework across save/menu lifecycles.

### Reset to default
Restore setting to mod-provided default rather than current save value.

### MCM Helper version code
Framework/API version number that dependent mods may check for feature compatibility.

### MCM Helper DLL
Native component whose successful SKSE load is required for its enhanced configuration behavior.

### Blank MCM
Symptom where menu name exists but controls are absent; can occur when framework DLL/API/config failed even though legacy registration data remains visible.

## Input and key mapping

### DirectInput scan code
Numeric keyboard key code used by Skyrim/SKSE key APIs rather than Unicode character identity.

### Keymap
MCM control selecting a keyboard/mouse/controller input code.

### Key conflict
Multiple mod/game actions share same input binding.

### Hotkey registration
Papyrus/SKSE/native registration for key events.

### RegisterForKey
SKSE Papyrus API subscribing script to key-down/up events.

### UnregisterForKey
Remove key registration.

### Control map
Game's action-to-device binding system distinct from raw key registration.

### Gamepad key
Controller button/axis code recognized by Skyrim input APIs.

### Input context
Menu/game state determines whether input is captured/consumed/propagated.

## UI translations and fonts

### Interface/Translations
Path containing SkyUI/UI translation text files.

### $translation key
UI string token resolved through translation resources.

### Missing translation
Raw $KEY displayed because matching language translation entry is absent.

### FontConfig
Configuration defining fonts used by Scaleform menus.

### fontconfig.txt
Skyrim interface font mapping/config asset.

### Font library SWF
SWF containing embedded font glyphs for UI use.

### Font replacement
Mod replacing font assets/config; can conflict with languages/glyph coverage/UI scale.

### Missing glyph
Font lacks required character, producing blank boxes/incorrect display.

## HUD widgets

### HUD
Heads-up display menu showing health/magicka/stamina/crosshair/compass/status and mod widgets.

### SkyUI widget
ActionScript/Papyrus-driven HUD element managed through SkyUI widget framework.

### Widget root
ActionScript movie clip/container for one widget instance.

### Widget registration
Papyrus/framework process registering HUD widget instance for updates.

### Widget update
Papyrus/native data pushed to ActionScript for visual refresh.

### HUD conflict
Mods replace HUD SWF or incompatible widget infrastructure.

## UI debugging rules

1. If MCM appears but is blank, check native framework DLL/config load before rebuilding the quest.
2. SWF file priority is independent from ESP load order.
3. SkyUI MCM quest/script registration and native MCM Helper persistence are separate layers.
4. A missing translation key is usually an Interface/Translations asset issue, not a plugin string-table issue.
5. Keymap conflicts can exist even when every individual mod's registration succeeds.
6. Updating a setting file outside the game may not update current script/native cache until the framework reloads it.
7. Do not recompile SkyUI public base scripts to customize a mod; extend/use the API.
8. Record exact SkyUI, SKSE and MCM Helper versions when troubleshooting menu lifecycle issues.
9. Font replacements need language glyph coverage as well as correct asset priority.
10. Custom UI crashes should be isolated by SWF/native callback layer, not treated as generic Papyrus errors.

## Sources

- SkyUI source: https://github.com/schlangster/skyui
- SKI_ConfigBase public header: https://github.com/schlangster/skyui/blob/master/dist/Data/Scripts/Headers/SKI_ConfigBase.psc
- SkyUI MCM API reference: https://github.com/schlangster/skyui/wiki/MCM-API-Reference
- MCM Helper: https://github.com/Exit-9B/MCM-Helper
- MCM Helper install layout: https://github.com/Exit-9B/MCM-Helper/blob/main/install_files.cmake
