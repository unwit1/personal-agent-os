# RaceMenu / SKEE Source Manifest

Snapshot date: 2026-09-24
Upstream: `expired6978/SKSE64Plugins`
Pinned commit: `9ebcb733e17be695f994cd2e9cc383043446bc02`
Status: source snapshot; current public RaceMenu binary version must be tracked separately

## Source/binary version distinction

At this pinned source commit, `skee64/Resource.rc` reports **0.4.19.17**.

The current Nexus RaceMenu page advertises a newer **0.4.20.0** release. Therefore this public GitHub source snapshot is **not assumed to be identical to the latest distributed 0.4.20.0 binary**.

At this source commit, `main.cpp` declares:
- Bethesda/Steam runtime target: `RUNTIME_VERSION_1_7_99`;
- GOG runtime target: `RUNTIME_VERSION_1_6_1179_GOG`;
- plugin is not version-independent.

Use this source for architecture/API semantics with the pinned commit. Use the dated current-version matrix for binary runtime-support claims.

## Primary source files

| Surface | File | Blob SHA |
|---|---|---|
| SKEE lifecycle/serialization/config | `skee64/main.cpp` | `ff2aa12558b489fec85ef5ea1bea33c657efe2d3` |
| Binary resource version | `skee64/Resource.rc` | `86d0f22bad154107466542c960b345d57dc97286` |
| NiOverride Papyrus API | `skee64/PapyrusNiOverride.cpp` | `6d3270a8dbd02f243e9759a9b82c67c7d533690c` |
| CharGen Papyrus API | `skee64/PapyrusCharGen.cpp` | `1e879cfa59acc0e0d87147a4f1e4c8c860154fc4` |
| Native plugin interfaces | `skee64/IPluginInterface.h` | `6a0dd5855efffcb21d47fd9463f003b1abb605bc` |

## Papyrus registration counts

- `NiOverride`: **175** native registrations detected.
- `CharGen`: **13** native registrations detected.

## Native interface families

The SKEE plugin interface exposes versioned C++ interfaces including:
- BodyMorph;
- NiTransform;
- ItemData;
- Attachment/update notifications;
- Overlay;
- Override;
- Preset;
- FormTag.

These are separate contracts with their own plugin/serialization versions. Consumers should query/check interface versions rather than assuming every RaceMenu release exposes one monolithic API.

## Major implementation subsystems present in source

- face morph/sculpt;
- overlay installation and regeneration;
- armor/node/weapon/skin overrides;
- body morphs and TRI morph cache;
- per-item data/dyes/texture layers;
- node transforms;
- skeleton extension;
- face/tint mask handling;
- attachment/update observers;
- preset save/load;
- CharGen export/import;
- Scaleform integration;
- plugin-interface exchange;
- SKSE co-save serialization.

## Provenance rule

Do not call this pinned source “RaceMenu 0.4.20.0 source.” It identifies itself as 0.4.19.17. If/when the 0.4.20.0 source is published or tagged, ingest it as a new snapshot and diff API/runtime/serialization changes.
