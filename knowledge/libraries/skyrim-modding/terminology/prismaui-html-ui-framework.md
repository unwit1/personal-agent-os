# Skyrim Modding Terminology — PrismaUI and HTML-Based UI Frameworks

Imported: 2026-09-24
Status: sourced deep-ingestion pass 22

## PrismaUI concept

### PrismaUI
Modern Skyrim SKSE UI framework used by 2026-era mods to render HTML/CSS/JavaScript-style interfaces through an embedded web-view engine rather than traditional Scaleform/SWF menus.

### HTML UI
Interface authored with HTML document structure.

### CSS
Style/layout layer controlling visual presentation.

### JavaScript UI
Client-side UI logic executing inside embedded browser/view context.

### Web view
Embedded browser-like renderer used inside Skyrim for modern UI.

### Ultralight
Lightweight HTML renderer referenced by current PrismaUI-based mods; distinct from Chromium/CEF.

### View
One PrismaUI HTML UI instance/page.

### View directory
Data path such as `PrismaUI/views/<mod>/` containing HTML, scripts, styles and assets.

### index.html
Typical entry document for one view.

### Asset directory
Images/fonts/JS/CSS used by a view.

### JSON localization
External language files consumed by HTML UI.

### i18n manifest
Metadata listing available translations/localization resources.

### UI fallback
Mod detects PrismaUI absence and uses a different native/interface implementation when designed to do so.

## Integration models

### Required PrismaUI
Mod's only UI implementation depends on framework.

### Optional PrismaUI skin
Core mod logic works independently; PrismaUI provides alternative modern frontend.

### Native backend + web frontend
SKSE DLL owns game state/actions while HTML UI presents data and sends commands.

### Papyrus bridge
Papyrus scripts exchange data/events with PrismaUI/native backend.

### Native API bridge
C++ plugin communicates directly with web view.

### Event/message bridge
Serialized events/messages pass between UI JavaScript and game/native side.

### UI state model
Structured data representing inventory/tree/settings/etc. sent to web view.

### Command
UI action sent back to plugin such as equip, teleport, unlock, configure.

### Validation boundary
Native backend must validate UI-supplied forms/values rather than trusting arbitrary web input.

## Examples

### PrismaUI Teleport Menu
HTML GUI listing cells/locations and invoking teleport utilities.

### PrismaUI AddItemMenu
Modern item browser spawning/adding forms from load order.

### PrismaUI QTE Framework
Reusable quick-time-event frontend/framework.

### iWant Prisma Widgets
PrismaUI reimplementation of iWant Widgets rendering API, preserving script API compatibility while replacing Flash/SWF renderer.

### Tullius Widgets
PrismaUI widget framework with external JSON localization/assets.

### Transmog UI
Modern armor/weapon appearance tools use PrismaUI to browse many forms and apply native visual transformations.

### Heart of Magic
Spell-progression mod using PrismaUI-based tree/scan interface.

### SkyrimNet UI
AI framework ecosystem can use modern UI surfaces alongside native/Papyrus backend.

## PrismaUI vs Scaleform

### Scaleform
Skyrim's built-in Flash/SWF UI runtime.

### HTML renderer
Modern external/native framework rendering HTML rather than ActionScript/SWF.

### SkyUI independence
PrismaUI view can coexist without replacing SkyUI menu files, depending on mod.

### SWF conflict avoidance
HTML view does not need to overwrite InventoryMenu/Favorites/Menu SWF, reducing traditional interface conflicts.

### New dependency layer
Tradeoff: introduces native SKSE DLL/web-renderer/runtime compatibility instead of SWF-only dependency.

### CSS responsive layout
UI can adapt screen sizes using web layout techniques.

### Web font
Font loaded from view assets rather than Skyrim Scaleform font library.

### Web animation
CSS/JS animation independent of Skyrim animation graph.

## Browser limitations

### Ultralight limitation
Embedded renderer may not support every modern website/browser feature expected by Chromium.

### iframe restriction
External websites can block embedding through security headers.

### CEF/Chromium
Full browser engine heavier/more capable than Ultralight; current in-game browser experiments may use WebView2/Chromium when PrismaUI isn't sufficient for general web browsing.

### WebView2
Microsoft Edge Chromium embedded runtime used by a 2026 in-game-browser mod because arbitrary websites often require full browser capabilities.

### Local asset delivery
Serving/loading view files in a way compatible with MO2 VFS and web renderer.

### Browser profile
Persistent cookies/cache/history/storage for a full embedded browser; separate privacy/security consideration from ordinary mod config.

## Input/focus

### Web-view focus
PrismaUI panel currently receives keyboard/mouse/controller input.

### Text-input suppression
Gameplay hotkeys must be suppressed while typing.

### Escape close
Menu-level input closing view.

### Mouse capture
Cursor interaction within HTML view.

### Gamepad navigation
Requires explicit mapping/implementation; ordinary HTML controls aren't automatically Skyrim-controller-friendly.

### Paused vs unpaused
Framework/mod determines whether game simulation pauses while view open.

## Security and privacy

### External web content
HTML UI fetching arbitrary internet content introduces network/privacy/security surface not present in local-only UI.

### Local-only view
Bundled static HTML/JS/CSS with no external network requests.

### Credential storage
Embedded browser handling logins/passwords must store profile data separately and securely; not normal Skyrim save state.

### Remote asset
UI loads image/script/API response over network; can break independently of mod load order.

### Content security
Web-view code should avoid arbitrary remote script execution when not needed.

## Diagnostic rules

1. Separate native backend success from HTML view rendering.
2. Check PrismaUI/native runtime compatibility and view asset paths when UI is blank.
3. A UI button failing can be JS bridge/command validation even when game plugin loaded.
4. MO2 VFS must expose view assets to the renderer.
5. Text input must suppress gameplay/global hotkeys.
6. PrismaUI and SkyUI can coexist because they are different render paths, but input/menu focus can still conflict.
7. Full web-browser functionality requires a different capability/security model than local mod UI.

## Sources

- PrismaUI-based Teleport Menu: https://www.nexusmods.com/skyrimspecialedition/mods/187563
- PrismaUI AddItem Menu: https://www.nexusmods.com/skyrimspecialedition/mods/179949
- PrismaUI QTE Framework: https://www.nexusmods.com/skyrimspecialedition/mods/189948
- iWant Prisma Widgets: https://www.nexusmods.com/skyrimspecialedition/mods/190876
- Tullius Widgets: https://www.nexusmods.com/skyrimspecialedition/mods/172458
- SkyNet browser example: https://www.nexusmods.com/skyrimspecialedition/mods/192735

## Dated note

PrismaUI's ecosystem expanded rapidly in 2026, including teleport/add-item menus, QTE framework and widget ports. Treat specific renderer/API capabilities as current-version facts rather than timeless Skyrim UI behavior.
