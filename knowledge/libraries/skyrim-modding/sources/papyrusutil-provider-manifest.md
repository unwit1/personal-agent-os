# PapyrusUtil Provider Manifest

Snapshot date: 2026-09-24
Upstream: `eeveelo/PapyrusUtil`
Source directory: `Scripts/Source/`
PSC providers: 6
Status: provider manifest

| PSC | Blob SHA | Functions | Events |
|---|---|---:|---:|
| `ActorUtil.psc` | `cff8e7b69c9f9edcb6f8051699c817e7d3d34b37` | 5 | 0 |
| `JsonUtil.psc` | `7618e9f385daf60b94cde392015489fd585c6098` | 135 | 0 |
| `MiscUtil.psc` | `ccbf5e6b59f7954ae525ba1c978d08900a2e03b3` | 18 | 0 |
| `ObjectUtil.psc` | `5f7be6a55a1b060efc4c58da7f56c905c7ba65f6` | 0 | 0 |
| `PapyrusUtil.psc` | `9f8c370b3f2a170d9ddd9d627f47df9850bf1f50` | 97 | 0 |
| `StorageUtil.psc` | `c309fef20cf56342c5ee0ed53f5d146af51bc940` | 282 | 0 |

## Provider roles

- `StorageUtil.psc` — save-associated typed key/value and dynamic-list storage.
- `JsonUtil.psc` — external JSON-backed typed values/lists.
- `ActorUtil.psc` — actor/package/combat-related utilities.
- `ObjectUtil.psc` — form/object-related utilities.
- `MiscUtil.psc` — miscellaneous helpers.
- `PapyrusUtil.psc` — core/version/general framework helpers.

Every call should retain provider identity; a StorageUtil/JsonUtil call is not a vanilla Papyrus API.
