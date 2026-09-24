# Skyrim Modding Terminology — Skyrim Platform and TypeScript Mods

Imported: 2026-09-24
Status: sourced deep-ingestion pass 9

## Skyrim Platform

### Skyrim Platform
Runtime framework allowing Skyrim mods to be authored in JavaScript/TypeScript with APIs modeling Papyrus/game objects plus additional browser/HTTP/Win32/event capabilities.

### JavaScript plugin
Bundled JS file loaded by Skyrim Platform at runtime.

### TypeScript plugin
Developer-authored TypeScript compiled/bundled into JavaScript for Skyrim Platform.

### Type definitions
`@skyrim-platform/skyrim-platform` TypeScript declarations describing Skyrim Platform APIs and Papyrus-like types.

### PapyrusObject
Base TypeScript/runtime abstraction corresponding to Papyrus/game objects.

### PapyrusValue
JS/TS value set that can represent Papyrus-compatible objects/primitives/arrays.

### Platform folder
Runtime data folder used by Skyrim Platform.

### Platform/Plugins
Distribution/runtime directory containing bundled Skyrim Platform JS plugins.

### Hot reload
Framework watches plugin files and reloads code during development after changes.

### update event
Skyrim Platform frame/update hook used by many JS plugins.

### tick
Special execution/update context available outside ordinary game-object event hooks according to platform rules.

### once
Event helper registering one-time callback.

### on
Event helper registering recurring callback.

### Native function bridge
Skyrim Platform exposes game/Papyrus/native operations to JS/TS.

### Papyrus call
Calling vanilla or third-party Papyrus functions from JS/TS through Skyrim Platform bindings.

### Third-party SKSE function bridge
Ability to invoke compatible SKSE/Papyrus functions exposed by installed mods from TypeScript.

### Promise
JavaScript async abstraction used by platform for asynchronous/latent-like calls.

### async/await
JS syntax used to sequence asynchronous Skyrim Platform operations.

### Hook context
Execution context in which access to Papyrus/game APIs is valid. Platform docs warn that Papyrus objects/functions are not valid from arbitrary JS execution contexts.

### Skyrim Platform event
Framework-defined event delivered to JS plugins.

### Browser/UI
Platform capability providing browser/web-style UI integration beyond vanilla Scaleform patterns.

### HTTP
Platform capability allowing web requests from plugins. Security/privacy/reliability implications should be considered.

### Win32
Platform bridge exposing selected Windows capabilities.

### npm dependency
Third-party JS package used in a plugin build.

### Bundling
Combining TypeScript/JavaScript and dependencies into distributable JS artifact.

### package.json
Node package metadata declaring scripts/dependencies/version.

### Semantic versioning
Skyrim Platform documents JS runtime API stability using semver, while TypeScript definition updates can require compile-time changes even without a runtime-major bump.

### TypeScript definition break
Compile errors after updating type declarations even if existing built JS remains compatible.

## Development workflow

### Plugin example
Official/example project used as a starting template.

### Source directory
Author's TS/JS source kept outside game/mod folder during development where recommended.

### build artifact
Bundled JS intended for `Platform/Plugins`.

### dist artifact
Intermediate JS output not necessarily intended to be distributed directly.

### npm run zip
Example packaging script producing a distributable archive.

### Platform-only mod
Plugin containing only JS runtime code and not ordinary ESP/assets.

### Hybrid Platform mod
Mod containing Platform JS plus ESP, meshes, textures, scripts or other normal Data assets.

### papyrus-bridge
Community library/pattern enabling communication between Papyrus scripts and Skyrim Platform TypeScript.

### TypeScript wrapper library
Typed JS package exposing functions from PapyrusUtil, JContainers, po3 Papyrus Extender or other frameworks.

## Safety and performance

### Main-thread game object access
Skyrim object APIs must be used from permitted platform/game contexts rather than arbitrary background JS execution.

### Update-loop cost
Heavy code in every update/tick can create frame-time cost just like native/Papyrus polling.

### HTTP latency
External requests are asynchronous and should never be treated as deterministic immediate gameplay operations.

### Hot-reload state
Reloaded JS code may not automatically reset all game/Papyrus/native state.

### Plugin exception
JS runtime exception that can disable/break a plugin without necessarily crashing Skyrim.

## Diagnostic rules

1. Distinguish compile-time TypeScript errors, bundler/npm problems and runtime JS exceptions.
2. Existing built JS may remain runtime-compatible when newer type declarations stop compiling source.
3. Only call game/Papyrus APIs from supported hooks/events.
4. Treat update callbacks as per-frame workload; avoid expensive scans each frame.
5. Hybrid mods still need normal plugin/asset/load-order troubleshooting for non-Platform components.
6. Third-party SKSE/Papyrus bridges inherit the dependency/version requirements of those frameworks.

## Sources

- Skyrim Platform core/docs: https://github.com/skyrim-multiplayer/skymp/blob/main/docs/docs_skyrim_platform.md
- Skyrim Platform README: https://github.com/skyrim-multiplayer/skymp/blob/main/skyrim-platform/README.md
- TypeScript declarations: https://github.com/skyrim-platform/skyrim-platform
- Example plugin/package workflow: https://github.com/skyrim-multiplayer/skymp/tree/main/skyrim-platform/tools/plugin-example
