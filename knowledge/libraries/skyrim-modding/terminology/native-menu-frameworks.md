# Skyrim Modding Terminology — Native SKSE Menu Frameworks

Imported: 2026-09-24
Status: sourced deep-ingestion pass 19

## Configuration UI families

### SkyUI MCM
Papyrus/Scaleform configuration interface hosted by SkyUI's Mod Configuration Menu.

### Native menu
SKSE C++ plugin-rendered UI, often Dear ImGui based, not dependent on Papyrus MCM page lifecycle.

### Overlay menu
Separate rendered window layered over Skyrim viewport.

### System-menu injection
Framework adds settings/pages directly into Skyrim's own Escape/System settings screens.

### In-game settings framework
Reusable API allowing many mods to expose options without each implementing a full UI stack.

## SKSE Menu Framework

### SKSE Menu Framework
Shared native menu framework by SkyrimThiago allowing SKSE plugins/addons to expose in-game configuration/debug pages.

### Menu addon
Mod registering a page/content with framework.

### Header API
C++ developer header used by native plugins to integrate.

### Old-header compatibility
Current framework documentation states older header-built addons remain compatible while newer headers improve developer experience.

### VR support
2026 current main build includes VR support contribution.

### Framework theme
Optional style/theme data.

### Menu registration
Plugin publishes page/name/callback into framework.

### Page callback
Code invoked while framework renders plugin settings.

### Immediate apply
Native menu option changes plugin state immediately without Papyrus/MCM reload when implementation supports it.

### INI persistence
Addon can write current settings back to its configuration file.

### Menu dependency
Plugin may use framework only for optional settings UI while core feature can remain operational without it—or may require it; implementation-specific.

## dMenu

### dMenu
Dear ImGui-based native menu by dTry used as configuration hub and utility window for multiple modern SKSE mods.

### dMenu page
Plugin/tool-specific configuration panel rendered inside dMenu.

### dMenu NG
2025-2026 unofficial update modernizing dMenu for current runtimes, controller/text input and expanded page capabilities.

### ImGui configuration hub
One immediate-mode interface hosts many plugin configuration controls.

### Native EditorID display
dMenu features/tools can require Native EditorID fixes/data so weather/forms show human-readable names.

### Save
Apply/persist UI edits.

### Cancel
Discard pending edits where page implementation buffers values.

### Controller navigation
Native menu receives gamepad input and focus.

### Text-input mode
Special state suppressing global gameplay hotkeys while user types into native menu field.

## Native System Menu Framework

### Native System Menu Framework
2026 framework injecting settings, controls entries, custom tabs/pages and changelog/read-only pages into Skyrim's own System menu.

### Vanilla widget reuse
Uses Bethesda System menu ScrollBar/OptionStepper/CheckBox style rather than independent overlay window.

### Gameplay/Display/Audio injection
Addon can place custom settings alongside related vanilla setting page.

### Controls injection
Addon exposes custom key binding through native Controls screen.

### System-menu entry
Addon adds entry to Escape/System menu opening custom page/tab.

### Read-only page
Native page used for changelog/help/info.

### Separate custom key storage
Framework stores mod-added controls separately so vanilla binding storage isn't overwritten.

### Settings export/import
Framework supports configuration portability/persistence according to current feature set.

## UI ownership

### Focus
Which menu receives input.

### Input capture
Native overlay/framework prevents gameplay actions while menu uses keyboard/mouse/gamepad.

### Menu stack
Order of open Scaleform/native menus and focus ownership.

### Pause flag
Whether game simulation stops while UI open.

### Skyrim Souls compatibility
Unpaused-menu frameworks alter expectations of mods that assume menus pause game.

### Typing Mode
Utility pattern preventing hotkeys from firing while text controls are active.

### Overlay z-order
Which native overlay draws on top when several ImGui frameworks are open.

### Cursor ownership
Which framework enables/disables OS/virtual cursor.

## MCM vs native menu

### MCM advantage
Deep integration with SkyUI, Papyrus authorship, established user expectations and save/config frameworks.

### Native-menu advantage
C++ direct state access, immediate settings, lower Papyrus dependency, rich debugging widgets.

### System-menu advantage
Looks/behaves like vanilla settings and centralizes options.

### Dual configuration
Mod exposes both INI and native/MCM UI. Need one canonical setting store to avoid divergence.

### Settings source of truth
Authoritative value store—INI/TOML/JSON/Papyrus/native state—from which UI reads/writes.

### Stale UI value
Menu shows cached value differing from actual plugin config after external edit.

## Diagnostic rules

1. Identify which menu framework owns a config screen before treating it as MCM.
2. Menu drawing, setting persistence and plugin feature logic are separate layers.
3. Framework version/header/API compatibility matters for native addon UI.
4. Input conflict while menu open is usually focus/capture/hotkey logic, not gameplay record conflict.
5. If UI edits disappear on restart, inspect persistence/save path, not render code.
6. Multiple ImGui overlays can coexist but cursor/input ownership must be coordinated.
7. Never assume dMenu/SMF/native System Menu use the same configuration backend.

## Sources

- SKSE Menu Framework current Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/120352
- dMenu: https://www.nexusmods.com/skyrimspecialedition/mods/97221
- dMenu NG: https://www.nexusmods.com/skyrimspecialedition/mods/166751
- Native System Menu Framework: https://www.nexusmods.com/skyrimspecialedition/mods/190636
- Dear ImGui: https://github.com/ocornut/imgui

## Dated snapshot

SKSE Menu Framework 3.12-Hotfix was current on 2026-09-24, updated 2026-08-28 with VR support. dMenu NG 1.3.2 was current, updated 2026-09-15. Native System Menu Framework 1.1.1 was released/updated 2026-09-17.
