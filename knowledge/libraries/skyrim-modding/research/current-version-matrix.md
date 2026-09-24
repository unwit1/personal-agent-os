# Skyrim Modding Current Version Matrix

Snapshot date: 2026-09-24
Status: dated observation — never treat this file as timeless

## Purpose

This file records versions that were directly verified from authoritative upstream release surfaces on the snapshot date. It is intentionally conservative: an unverified tool is omitted rather than guessed.

| Component | Verified current release | Upstream | Snapshot notes |
|---|---|---|---|
| xEdit / SSEEdit | 4.1.5f | https://github.com/TES5Edit/TES5Edit/releases | Latest GitHub release observed. Release includes TES5VR Backported ESL-range fix and TES5/SSE definition updates. |
| LOOT | 0.29.1 | https://github.com/loot/loot/releases | Latest GitHub release observed. Windows build requires 64-bit Windows 10 1809+ and MSVC 2022 x64 redistributable. |
| Mod Organizer 2 | 2.5.2 | https://github.com/ModOrganizer2/modorganizer/releases | Latest GitHub release observed. Release lists libloot 0.23.0, Qt/PyQt 6.7.1 and Python 3.12.3 among bundled dependencies. |
| Community Shaders | 1.9.1 | https://github.com/community-shaders/skyrim-community-shaders/releases | Released 2026-09-24. Upstream release commit shown as 265c28f. |

## Verified runtime/framework spine

| Component | Verified version/build | Runtime scope observed | Source |
|---|---|---|---|
| SKSE64 AE | 2.3.1 | Steam Skyrim 1.7.104 | https://skse.silverlock.org/ |
| SKSE64 GOG | 2.2.6 | GOG Skyrim 1.6.1179 | https://skse.silverlock.org/ |
| SKSE64 legacy SE | 2.0.20 | Skyrim 1.5.97 | https://skse.silverlock.org/ |
| SKSEVR | 2.0.12 | Skyrim VR 1.4.15 | https://skse.silverlock.org/ |
| Address Library | v13 | All supported game versions through Steam 1.7.104 per current file description; separate databases/runtime matching still matter | https://www.nexusmods.com/skyrimspecialedition/mods/32444 |
| CommonLibSSE-NG | v9.1.0 | Current multi-runtime library release; source changelog includes 1.7.x/VR work and breaking v9 API naming changes | https://github.com/alandtse/CommonLibSSE-NG/releases |
| Open Animation Replacer | 3.2.1 | Current Nexus release observed; updated 2026-08-31 | https://www.nexusmods.com/skyrimspecialedition/mods/92109 |
| Pandora Behaviour Engine+ | v4.4.0-beta | Current GitHub release observed; beta channel | https://github.com/Monitor221hz/Pandora-Behaviour-Engine-Plus/releases |
| PapyrusUtil SE/AE | 4.8 | SKSE 2.3.1 / Skyrim 1.7.104 / Address Library AE for current main file | https://www.nexusmods.com/skyrimspecialedition/mods/13048 |
| PapyrusUtil GOG | 4.6 | SKSE 2.2.6 / Skyrim GOG 1.6.1179 | https://www.nexusmods.com/skyrimspecialedition/mods/13048 |
| PapyrusUtil legacy SE | 3.9 | SKSE 2.0.20 / Skyrim 1.5.97 | https://www.nexusmods.com/skyrimspecialedition/mods/13048 |
| JContainers SE/AE | 4.3.2 page version | Current main file targets SKSE 2.3.1 / Skyrim 1.7.104 | https://www.nexusmods.com/skyrimspecialedition/mods/16495 |
| JContainers GOG | 4.3.2 page version | Current GOG file targets SKSE 2.2.6 / Skyrim 1.6.1179 | https://www.nexusmods.com/skyrimspecialedition/mods/16495 |
| JContainers VR | 4.3.2 page version | Current VR file targets Skyrim VR 1.4.15 / SKSEVR 2.0.12 | https://www.nexusmods.com/skyrimspecialedition/mods/16495 |
| MCM Helper | 1.6.3 | Current file description supports Steam Skyrim 1.7.99+ and Skyrim VR 1.4.15.1; separate legacy 1.5.97 backport remains available | https://www.nexusmods.com/skyrimspecialedition/mods/53000 |
| SSE Engine Fixes main | 7.0.20 | Main page version; file description supports SE 1.5.97 and AE 1.6.1170+ with preloader/Address Library requirements | https://www.nexusmods.com/skyrimspecialedition/mods/17230 |
| SSE Engine Fixes 1.7.99 beta | 7.0.21 | Separate beta file specifically for 1.7.99; page says preloader not required on 1.7.99 | https://www.nexusmods.com/skyrimspecialedition/mods/17230 |

### Compatibility interpretation

- A page-level version can cover several separately built runtime files. Store file/runtime identity as well as page version.
- "AE" is not a runtime number. Prefer exact executable version.
- Address Library v13 being installed does not make an old CommonLib/plugin binary understand the current Address Library file format or changed engine layouts.
- CommonLibSSE-NG v9.0.0 included breaking source-level member renames even though the cited HitData layout/sizeof did not change; native source compatibility and binary/game-runtime compatibility are separate axes.
- Pandora's current release is explicitly beta; do not flatten its status into a stable-release claim.
- Engine Fixes currently exposes different files/runtime requirements rather than one universal "latest DLL" rule.
- Current PapyrusUtil/JContainers main files target 1.7.104, while legacy/GOG variants remain separate compatibility tracks.

## Compatibility dimensions to track separately

A single version string is not enough for Skyrim compatibility. For every native/tool entry, preserve where relevant:

- Skyrim executable version;
- Steam/GOG/VR distribution;
- SKSE/SKSEVR version;
- Address Library version;
- BEES requirement;
- Creation Kit generation;
- configuration grammar version;
- source commit/tag;
- observed release date;
- whether the entry is upstream, fork, port, or backport.

## Update policy

1. Refresh from upstream release pages/repositories.
2. Never infer a release from a Nexus “updated” date alone.
3. Keep old snapshots when they explain historical compatibility.
4. Mark prerelease/experimental builds explicitly.
5. If GitHub/Nexus disagree, record both and determine whether one is a mirror, prerelease, hotfix, or delayed tag.
6. Do not overwrite a version-scoped compatibility fact merely because a newer release exists.
7. Link release notes/change logs when a change affects runtime support, record schemas, config grammar, or generated outputs.

## Automation target

A future updater should:
- query configured upstream providers;
- compare semantic/tag versions;
- record release timestamp and source commit;
- detect compatibility-impacting release-note terms;
- create a candidate update rather than silently changing canonical support claims;
- run relevant regression/ingestion jobs after approval or high-confidence policy rules.

See `version-provenance-model.md` for evidence semantics.
