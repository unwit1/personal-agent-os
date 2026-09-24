# Skyrim Modding Research Coverage Manifest

Updated: 2026-09-24
Status: active corpus map

This manifest tracks which major Skyrim modding knowledge domains have been ingested and which sources should be preferred. “Covered” means the repository contains a substantive terminology/diagnostic module; it does not mean the ecosystem can never change.

| Domain | Coverage | Primary evidence families |
|---|---|---|
| Plugin records, FormIDs, overrides, cleaning | deep | xEdit/Tome of xEdit, xEdit source |
| ESP/ESM/ESL/light plugins | deep | xEdit docs/source |
| LOOT/load-order metadata | strong | LOOT docs + xEdit conflict semantics |
| MO2/USVFS | strong | Mod Organizer 2 + USVFS upstream |
| Vortex/deployment | strong | Nexus Vortex upstream/wiki |
| Wabbajack/modlists | strong | Wabbajack upstream/docs |
| Creation Kit basics/worldbuilding | deep | CK Wiki + CKPE + xEdit |
| Navmesh/cells/worldspaces | deep | CK Wiki + xEdit + DynDOLOD specialist docs |
| Story Manager/quests/dialogue/scenes | deep | CK Wiki + observed game-data conventions |
| Papyrus language/runtime | deep | CK Wiki + SKSE + FallrimTools |
| Papyrus/save persistence | deep | FallrimTools + SKSE/CommonLib serialization |
| SKSE/native plugins | deep | SKSE + CommonLibSSE-NG upstream |
| Address Library/relocations/hooks | deep | CommonLibSSE-NG + Address Library + source |
| Native crash diagnosis | deep | Crash Logger + Trainwreck + CommonLib/source |
| Engine fixes/runtime frameworks | strong | Engine Fixes, po3, Papyrus Extender, JContainers/PapyrusUtil |
| SPID/KID/BOS/FLM | deep | powerofthree/FLM upstream + current docs |
| SkyPatcher | strong | upstream source + current Nexus/docs |
| Mutagen/Synthesis/Spriggit | strong | Mutagen-Modding upstream |
| xEdit scripting | strong | xEdit docs/scripts |
| NIF/meshes/materials | deep | NifSkope + BodySlide + specialist tooling |
| DDS/textures/compression/mipmaps | strong | DirectX-era format knowledge + CAO/NifSkope/DynDOLOD docs |
| BodySlide/Outfit Studio | deep | upstream + project wiki |
| RaceMenu/BodyMorph/BodyGen | strong | RaceMenu current docs/source lineage + BodySlide |
| FaceGen/NPC appearance | deep | CK Wiki + RaceMenu + practical record/asset model |
| Animation/OAR/Pandora | deep | OAR + Pandora upstream |
| HDT-SMP/FSMP physics | strong | FSMP upstream/docs + NIF/skeleton tooling |
| SkyUI/Scaleform/MCM | deep | SkyUI source/MCM API + MCM Helper |
| Audio/FUZ/XWM/LIP | strong | current audio tools + CK asset conventions |
| Localization/STRINGS | strong | xTranslator + CK/xEdit |
| BSA/archive packaging | strong | CK/xEdit/BSArch/BSA tooling |
| LOD/TexGen/DynDOLOD/xLODGen | very deep | DynDOLOD current specialist docs |
| Grass LOD/Seasons/Occlusion | deep | DynDOLOD current docs |
| Rendering/Community Shaders | strong | Community Shaders upstream |
| ENB | foundation | ENB official documentation; version/preset-specific behavior needs contextual ingestion |
| SSE Display Tweaks | strong | upstream source/docs |
| Performance/engine limits | strong | Engine Fixes + DynDOLOD + Display Tweaks + logs |
| Gameplay forms/combat/magic/crafting | deep | CK Wiki + xEdit/game record schemas |
| Save repair/ReSaver | deep | FallrimTools source |
| Release/testing methodology | deep playbook | cross-source engineering practice |

## Evidence hierarchy

1. Shipped game data and reproducible runtime tests.
2. Current upstream source/documentation for the exact tool/framework.
3. Current specialist documentation maintained by tool authors.
4. xEdit/CK format/editor documentation.
5. Mod-author documentation for that mod.
6. High-quality technical community investigations.
7. Forums/Reddit/Discord as leads until corroborated.

## Version-sensitive source rule

Never promote a current version number, supported runtime, config syntax, hook address, ABI/layout detail, or changelog statement into timeless knowledge. Store the observation date and re-check upstream before implementation.

## Contradiction rule

When sources disagree:
- preserve both claims with provenance;
- prefer direct source/runtime evidence over popularity;
- identify version/runtime differences;
- run a controlled test when feasible;
- promote a resolution only after evidence is sufficient.

## Copyright/storage rule

The repository stores normalized terminology, structured facts, diagnostic relationships, brief summaries and source pointers. It does not mirror full copyrighted guides/mod descriptions merely to make them searchable.
