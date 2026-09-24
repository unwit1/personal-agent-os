# Skyrim Modding Terminology Index

Updated: 2026-09-24
Status: active
Terminology modules: 44
Indexed terminology headings: 3325

This index inventories the canonical Skyrim technical terminology corpus. Counts include intentional cross-module repetitions where a concept has different diagnostic implications; 3267 is therefore an indexed-heading count rather than a unique-concept count.

## Retrieval strategy

Do not load every module for every question. Start with `../troubleshooting/diagnostic-router.md`, then retrieve only the modules relevant to the suspected layers. The core glossary is the general fallback.

## Modules

| Module | Indexed headings |
|---|---:|
| [animation-assets-bodyslide-ui.md](../terminology/animation-assets-bodyslide-ui.md) | 93 |
| [asset-conversion-porting.md](../terminology/asset-conversion-porting.md) | 48 |
| [audio-localization-archives.md](../terminology/audio-localization-archives.md) | 92 |
| [automated-patchers-mutagen-synthesis.md](../terminology/automated-patchers-mutagen-synthesis.md) | 75 |
| [core-glossary.md](../terminology/core-glossary.md) | 85 |
| [crash-log-patterns.md](../terminology/crash-log-patterns.md) | 47 |
| [creation-kit-record-type-catalog.md](../terminology/creation-kit-record-type-catalog.md) | 108 |
| [creation-kit-worldbuilding-navmesh.md](../terminology/creation-kit-worldbuilding-navmesh.md) | 121 |
| [data-frameworks-audio-engine-fixes.md](../terminology/data-frameworks-audio-engine-fixes.md) | 48 |
| [development-toolchains.md](../terminology/development-toolchains.md) | 72 |
| [engine-fixes-runtime-frameworks.md](../terminology/engine-fixes-runtime-frameworks.md) | 66 |
| [environment-projectiles-impacts.md](../terminology/environment-projectiles-impacts.md) | 76 |
| [gameplay-record-systems.md](../terminology/gameplay-record-systems.md) | 81 |
| [gameplay-records-combat-magic-crafting.md](../terminology/gameplay-records-combat-magic-crafting.md) | 106 |
| [graphics-shaders-rendering.md](../terminology/graphics-shaders-rendering.md) | 85 |
| [ini-console-testing-environment.md](../terminology/ini-console-testing-environment.md) | 60 |
| [lod-grass-occlusion-world-rendering.md](../terminology/lod-grass-occlusion-world-rendering.md) | 53 |
| [lod-grass-seasons-occlusion.md](../terminology/lod-grass-seasons-occlusion.md) | 94 |
| [mod-managers-modlists-deployment.md](../terminology/mod-managers-modlists-deployment.md) | 83 |
| [mod-managers-wabbajack-patching-pipelines.md](../terminology/mod-managers-wabbajack-patching-pipelines.md) | 72 |
| [modern-runtime-frameworks.md](../terminology/modern-runtime-frameworks.md) | 53 |
| [npc-appearance-facegen-racemenu.md](../terminology/npc-appearance-facegen-racemenu.md) | 92 |
| [papyrus-api-event-catalog.md](../terminology/papyrus-api-event-catalog.md) | 159 |
| [papyrus-performance-native-serialization.md](../terminology/papyrus-performance-native-serialization.md) | 65 |
| [papyrus-persistence-advanced.md](../terminology/papyrus-persistence-advanced.md) | 85 |
| [papyrus-quests-dialogue-ai-magic.md](../terminology/papyrus-quests-dialogue-ai-magic.md) | 104 |
| [patching-tool-lineage.md](../terminology/patching-tool-lineage.md) | 39 |
| [performance-engine-limits.md](../terminology/performance-engine-limits.md) | 73 |
| [physics-hdt-smp-collision.md](../terminology/physics-hdt-smp-collision.md) | 76 |
| [plugin-format-localization-archives.md](../terminology/plugin-format-localization-archives.md) | 53 |
| [racemenu-facegen-bodymorph-physics.md](../terminology/racemenu-facegen-bodymorph-physics.md) | 56 |
| [records-patching-load-order.md](../terminology/records-patching-load-order.md) | 61 |
| [rendering-shaders-lighting.md](../terminology/rendering-shaders-lighting.md) | 91 |
| [runtime-distribution-frameworks.md](../terminology/runtime-distribution-frameworks.md) | 81 |
| [runtime-platform-config-files.md](../terminology/runtime-platform-config-files.md) | 55 |
| [skse-commonlib-native-crash.md](../terminology/skse-commonlib-native-crash.md) | 72 |
| [skypatcher-runtime-record-patching.md](../terminology/skypatcher-runtime-record-patching.md) | 31 |
| [story-manager-locations-events.md](../terminology/story-manager-locations-events.md) | 49 |
| [story-manager-quests-dialogue-scenes.md](../terminology/story-manager-quests-dialogue-scenes.md) | 98 |
| [textures-nif-asset-optimization.md](../terminology/textures-nif-asset-optimization.md) | 80 |
| [ui-skyui-mcm-scaleform.md](../terminology/ui-skyui-mcm-scaleform.md) | 79 |
| [worldspace-navmesh-saves-persistence.md](../terminology/worldspace-navmesh-saves-persistence.md) | 73 |
| [vr-linux-proton-cross-platform.md](../terminology/vr-linux-proton-cross-platform.md) | 58 |
| [xedit-plugin-format-advanced.md](../terminology/xedit-plugin-format-advanced.md) | 77 |

## Broad domain coverage

The corpus now covers plugin/xEdit internals, Creation Kit record types and worldbuilding, Papyrus APIs/performance/persistence, quests/dialogue/scenes/Story Manager, gameplay/magic/combat/crafting, SKSE/CommonLib/native development, crash diagnostics, engine fixes and utilities, runtime distributors/patchers, MO2/Vortex/Wabbajack, automated patching, animation/behavior systems, NIF/textures/BodySlide, NPC appearance/RaceMenu, physics, UI/MCM/Scaleform, audio/localization/BSA resources, rendering/ENB/Community Shaders, LOD/grass/seasons/occlusion, platform/runtime config, performance/engine limits, porting, development toolchains, Skyrim VR, and Linux/Proton/Steam Deck environments.

## Deduplication note

Several specialist modules overlap intentionally. Examples:
- `graphics-shaders-rendering.md` and `rendering-shaders-lighting.md`;
- `racemenu-facegen-bodymorph-physics.md` and `npc-appearance-facegen-racemenu.md`;
- `mod-managers-wabbajack-patching-pipelines.md` and `mod-managers-modlists-deployment.md`;
- `lod-grass-occlusion-world-rendering.md` and `lod-grass-seasons-occlusion.md`.

Future normalization should map aliases/duplicates to stable concept IDs while retaining specialist context rather than deleting useful domain-specific explanations.
