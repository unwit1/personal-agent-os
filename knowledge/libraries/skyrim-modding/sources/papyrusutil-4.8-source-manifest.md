# PapyrusUtil 4.8 Source Manifest

Snapshot date: 2026-09-24
Upstream: `eeveelo/PapyrusUtil`
Pinned commit: `ff854180db67d330da34371781bcf9e6443b53c3`
Source status: current public source snapshot corresponding to version 48
Distributed binary reference: Nexus PapyrusUtil SE 4.8, uploaded 2026-08-30
Status: source-backed, with explicit source/binary provenance

## Version evidence

`Plugin.h` at the pinned source commit defines:

`PAPYRUSUTIL_VERSION 48`

The current Nexus main file is version 4.8 for SKSE 2.3.1 / Skyrim 1.7.104 / Address Library AE and was uploaded 2026-08-30.

The source repository head was also pushed 2026-08-30. Because the Git repository has no formal v4.8 tag/release, preserve this as a strong correspondence rather than pretending a signed/tagged source-build identity exists.

## Papyrus source files

| Script | Source path | Blob SHA | Function declarations |
|---|---|---|---:|
| `PapyrusUtil` | `Scripts/Source/PapyrusUtil.psc` | `9f8c370b3f2a170d9ddd9d627f47df9850bf1f50` | 97 |
| `StorageUtil` | `Scripts/Source/StorageUtil.psc` | `c309fef20cf56342c5ee0ed53f5d146af51bc940` | 282 |
| `JsonUtil` | `Scripts/Source/JsonUtil.psc` | `7618e9f385daf60b94cde392015489fd585c6098` | 135 |
| `ActorUtil` | `Scripts/Source/ActorUtil.psc` | `cff8e7b69c9f9edcb6f8051699c817e7d3d34b37` | 5 |
| `ObjectUtil` | `Scripts/Source/ObjectUtil.psc` | `5f7be6a55a1b060efc4c58da7f56c905c7ba65f6` | 0 |
| `MiscUtil` | `Scripts/Source/MiscUtil.psc` | `ccbf5e6b59f7954ae525ba1c978d08900a2e03b3` | 18 |

## Primary responsibilities

- `PapyrusUtil` — array/string/numeric convenience functions and library version.
- `StorageUtil` — typed persistent values/lists keyed globally or to Forms; save-local serialization.
- `JsonUtil` — typed values/lists and JSON path APIs stored in external files.
- `ActorUtil` — actor/package-related helpers.
- `ObjectUtil` — legacy object/model helpers; current source explicitly comments out unsupported SE functions.
- `MiscUtil` — filesystem/string/scan and miscellaneous utility functions.

## Persistence architecture

The native plugin registers SKSE serialization callbacks for Save, Load and Revert. StorageUtil's normal storage is therefore part of PapyrusUtil's serialized save/co-save state.

JsonUtil instead reads/writes JSON beneath:

`Data\SKSE\Plugins\StorageUtilData\`

See `papyrusutil-persistence-storage-json.md` for operational semantics.
