# JContainers v4.3.2 Source Manifest

Snapshot date: 2026-09-24
Release: `v4.3.2`
Published: 2026-08-29
Upstream: `ryobg/JContainers`
Status: pinned source release

## Runtime compatibility from release

| Edition | SKSE | Skyrim |
|---|---|---|
| AE/64 | 2.3.1 | 1.7.104 |
| GOG | 2.2.6 | 1.6.1179 |
| VR | 2.0.12 | 1.4.15 |

## Internal version constants

The v4.3.2 source defines:
- API version 4;
- feature version 3;
- minor version 2;
- patch version 0.

JContainers uses `API.Feature.Minor.Patch` internally, so the source constant string is `4.3.2.0`, while the GitHub/Nexus release is labeled `4.3.2`.

## Serialized storage

- chunk ID: `JSTR`;
- save/load/revert callbacks registered through SKSE serialization;
- Form-delete callback registered;
- runtime-dependent plugin names: JContainers64 / JContainersGOG / JContainersVR.

## Papyrus binding modules

`api_3/master.h` includes:
- tes_object;
- tes_atomic;
- tes_array;
- tes_map;
- tes_db;
- tes_jcontainers;
- tes_string;
- tes_form_db;
- tes_lua.

## Source evidence classification

JContainers is a maintained fork of the original SilverIce/JContainers, and the v4.3.2 tag is the authoritative snapshot used here for the 2026 runtime builds.
