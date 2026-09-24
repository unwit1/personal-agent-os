# Skyrim Modding Terminology Index

Updated: 2026-09-24
Status: active
Terminology/reference modules: 28
Indexed headings: 2374
Canonical alias mappings: 76

This index is the navigation layer for the technical Skyrim Modding Knowledge Repository. The heading total is an index count rather than a claim that every heading is a unique semantic entity: important concepts intentionally recur across subsystem modules when the diagnostic context differs.

## Module index

| Module | Indexed headings |
|---|---:|
| `animation-assets-bodyslide-ui.md` | 93 |
| `audio-localization-archives.md` | 92 |
| `automated-patchers-mutagen-synthesis.md` | 75 |
| `core-glossary.md` | 85 |
| `crash-log-patterns.md` | 47 |
| `creation-kit-record-type-catalog.md` | 108 |
| `creation-kit-worldbuilding-navmesh.md` | 121 |
| `development-toolchains.md` | 72 |
| `engine-fixes-runtime-frameworks.md` | 66 |
| `gameplay-records-combat-magic-crafting.md` | 106 |
| `lod-grass-seasons-occlusion.md` | 94 |
| `mod-managers-modlists-deployment.md` | 83 |
| `npc-appearance-facegen-racemenu.md` | 92 |
| `papyrus-api-event-catalog.md` | 159 |
| `papyrus-persistence-advanced.md` | 85 |
| `papyrus-quests-dialogue-ai-magic.md` | 104 |
| `performance-engine-limits.md` | 73 |
| `physics-hdt-smp-collision.md` | 76 |
| `records-patching-load-order.md` | 61 |
| `rendering-shaders-lighting.md` | 91 |
| `runtime-distribution-frameworks.md` | 81 |
| `skse-commonlib-native-crash.md` | 72 |
| `skypatcher-runtime-record-patching.md` | 31 |
| `story-manager-quests-dialogue-scenes.md` | 98 |
| `textures-nif-asset-optimization.md` | 80 |
| `ui-skyui-mcm-scaleform.md` | 79 |
| `worldspace-navmesh-saves-persistence.md` | 73 |
| `xedit-plugin-format-advanced.md` | 77 |

## Retrieval

Use `aliases.json` to normalize acronyms and shorthand, then use `troubleshooting-routing.md` to choose subsystem modules. Do not answer cross-layer troubleshooting from one matching definition.

### Primary routing layers

- plugin format, records, xEdit, FormIDs and load order;
- mod-manager deployment, archives and asset priority;
- Papyrus, quests, Story Manager and save persistence;
- SKSE/CommonLib/native code, engine fixes and crash logs;
- runtime distribution/config patchers and generated patches;
- animations, skeletons, physics, BodySlide, RaceMenu and FaceGen;
- UI/Scaleform/SkyUI/MCM/input;
- worldspaces, cells, navmesh and encounter/location systems;
- textures, NIF materials, rendering and shaders;
- LOD, grass, seasons, large references and occlusion;
- gameplay records including actor values, perks, magic, combat, equipment and crafting;
- development/build/testing/release workflows.

## Maintenance rules

1. Regenerate counts when modules are added or headings materially change.
2. Add common synonyms/acronyms to `aliases.json`.
3. Add new symptom routes to `troubleshooting-routing.md`.
4. Version-scope volatile tool/runtime facts.
5. Preserve conflicting evidence until resolved rather than silently overwriting it.
6. Prefer source-backed diagnostic relationships over isolated definitions.
