# Skyrim Modding Retrieval and Troubleshooting Routing Matrix

Updated: 2026-09-24

Use this before searching individual glossary terms. Symptoms are cross-layer; route to all plausible modules, then narrow by evidence.

| Symptom / task | First modules | Secondary modules |
|---|---|---|
| “Mod doesn't work” | mod-managers-modlists-deployment; records-patching-load-order | engine-fixes-runtime-frameworks; papyrus; runtime frameworks |
| Missing/overwritten feature | records-patching-load-order | runtime-distribution-frameworks; skypatcher; asset/deployment |
| CTD/startup crash | crash-log-patterns; skse-commonlib-native-crash | engine-fixes-runtime-frameworks; deployment |
| CTD entering location | crash-log-patterns; creation-kit-worldbuilding-navmesh | textures/NIF; NPC appearance; physics; save state |
| Freeze/hang/ILS | crash-freeze playbook; performance-engine-limits | Papyrus persistence; native logs; asset I/O |
| New game works, old save fails | papyrus-persistence-advanced; worldspace-navmesh-saves-persistence | save-state playbook; quests/story manager |
| Dark/black/grey face | npc-appearance-facegen-racemenu | records; assets/deployment |
| Armor invisible/clipping | gameplay records; animation-assets-bodyslide-ui | textures/NIF; physics; RaceMenu |
| Hair/cloth explodes | physics-hdt-smp-collision | skeleton/BodySlide; crash patterns |
| Animation not playing | animation-assets-bodyslide-ui | OAR/Pandora configs; skeleton; gameplay/behavior |
| NPC stuck/not moving | creation-kit-worldbuilding-navmesh | packages/AI; scene/quest; collision |
| Dialogue missing | story-manager-quests-dialogue-scenes | audio-localization-archives; quest/Papyrus |
| Voice missing | audio-localization-archives | story-manager dialogue; mod deployment |
| MCM blank/missing | ui-skyui-mcm-scaleform | SKSE/native frameworks; deployment |
| Missing translation/$KEY | ui-skyui-mcm-scaleform | audio-localization-archives |
| Wrong texture/mesh | textures-nif-asset-optimization | mod-manager deployment; rendering |
| Flickering/distant object | lod-grass-seasons-occlusion | worldspace/large refs; rendering |
| FPS/stutter | performance-engine-limits | rendering; physics; Papyrus; world/LOD |
| Save corruption message | performance-engine-limits; save-state playbook | Engine Fixes; FallrimTools |
| Too many references | performance-engine-limits | xEdit plugin format; worldspace |
| ESL/compact question | records-patching-load-order; xedit-plugin-format-advanced | FaceGen/save identity when renumbering |
| “Which patch framework?” | runtime-distribution-frameworks | skypatcher; Synthesis |
| Make code patch | automated-patchers-mutagen-synthesis | xEdit schemas; testing playbook |
| Make SKSE DLL | development-toolchains | skse-commonlib-native-crash |
| Make quest/radiant event | story-manager-quests-dialogue-scenes | Papyrus API; world/location |
| Make worldspace/location | creation-kit-worldbuilding-navmesh | LOD; performance; testing |
| Port LE mod to SE | textures-nif-asset-optimization | xEdit plugin format; animation; SKSE compatibility |
| Package/release mod | mod-managers-modlists-deployment | audio/archive; testing/release playbook |

## Routing principles

- Search by **failure layer**, not just mod name.
- Load-order questions almost always require separate file-priority analysis.
- Established-save symptoms require save-state retrieval.
- Native DLL questions require exact runtime/version retrieval.
- Generated outputs are derived artifacts: retrieve both generator knowledge and source-layer knowledge.
- If evidence crosses two layers, do not force a single-layer explanation.
