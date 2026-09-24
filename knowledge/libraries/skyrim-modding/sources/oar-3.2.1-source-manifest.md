# Open Animation Replacer 3.2.1 Source Manifest

Snapshot date: 2026-09-24
Upstream: `ersh1/OpenAnimationReplacer`
Pinned commit: `f4e7688b065175aff70aa523073857911e15aca3`
Source version: **3.2.1**
Status: pinned current-source snapshot

## Version evidence

At the pinned source commit, `CMakeLists.txt` sets:

`VERSION 3.2.1`

The repository was pushed 2026-08-31, matching the current 3.2.1 generation already tracked in the compatibility matrix.

## Core evidence files

| Surface | File | Blob SHA |
|---|---|---|
| Built-in conditions | `src/Conditions.h` | `d4559c9c3bfc100596a2370dd7108180045862d0` |
| Condition API types | `src/API/OpenAnimationReplacer-ConditionTypes.h` | `e43c62e33abb2f69a3c02084c950c9406dad8ce7` |
| Condition components/state scopes | `src/BaseConditions.h` | `3babd3574af29a823844c8b691f9424875a72795` |
| JSON/legacy parsing | `src/Parsing.cpp` | `71e6b6c11f597af82b77ba273411390f22ac3041` |
| Parsed config structures | `src/Parsing.h` | `efa40dc4f7d24850dddd323c498b1074edfe517a` |
| Replacer/submod state and defaults | `src/ReplacerMods.h` | `9d2779e4c5a7820e4d8242ed44b0eee743e97e3e` |
| Variant runtime model | `src/Variants.h` | `dd9fd8b33b627ef06aa9e6485ee4474acfa94c3a` |
| Replacement selection/evaluation | `src/ReplacementAnimation.cpp` | `f2afc938b257c6d15808874835ff0961b7431b91` |

## Finite source surfaces identified

- **123 built-in user-facing condition names** in this source snapshot.
- condition API version enum through **V4**;
- three condition types: normal, custom, preset;
- four non-zero state scopes: Local, SubMod, ReplacerMod, Reference;
- essential/non-essential missing-provider behavior;
- Random and Sequential variant modes;
- author JSON, user JSON and legacy DAR-style parsing paths.

## Evidence policy

This manifest describes OAR 3.2.1 source. Third-party custom condition plugins extend the runtime condition vocabulary and must be ingested separately with their own provider/version provenance.
