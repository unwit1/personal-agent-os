# JContainers Native Papyrus API Provider Manifest

Snapshot date: 2026-09-24
Upstream: `SilverIce/JContainers`
Registration source directory: `JContainers/src/api_3/`
Source files in directory: 14
Status: native-provider manifest

## api_3 source files

| File | Blob SHA |
|---|---|
| `master.h` | `aedc24848075b17a2b871672da5a807e2eac4da9` |
| `string_wrapper.cpp` | `c93b63eefaf01b9eaaf68e6172cd59b23d217713` |
| `tes_api_3.cpp` | `6cf71de1e7278d66b2ed81dd92fbf3cc65c7fbac` |
| `tes_array.h` | `1d8450e020952a9efc3f1d0df3bb74e238d53142` |
| `tes_atomic.h` | `c8e3f860e353d3f8de93c333df97b176a28b8f03` |
| `tes_db.h` | `a63e5aef707c532a504597993c9fa0e928e23687` |
| `tes_form_db.h` | `8ff16cbb7f834392e1939fcc302048a12959f8e9` |
| `tes_inteface.cpp` | `c4cfb86da2dbad523b6d4421e8fbf649911c15b9` |
| `tes_jcontainers.h` | `2b07b7b22219b47d030de568d7369d8804e9d7ed` |
| `tes_lua.h` | `74bbf3ecc1176f9840eabd5d9934f2b2d8e65e71` |
| `tes_map.h` | `3518a0f65666b54959863d69328e084f96b3733d` |
| `tes_object.h` | `48a881ba7db5e97f59a4146bfd5237b53ae7e7a8` |
| `tes_string.h` | `4a7c320b1861ddcf316771e0903b09d38530a8b1` |
| `tests.hpp` | `8384a479bcb37f8772ce8184c19b9efb08999ba8` |

## Architecture

JContainers does not keep its public API as a normal committed PSC source tree. Its Papyrus surface is registered/generated from native `api_3` source.

Core public abstractions include:
- `JValue` — shared object/handle operations;
- `JArray` — ordered heterogeneous container;
- `JMap` — string-keyed associative container;
- `JFormMap` — Form-keyed associative container;
- `JIntMap` / integer-map support where registered;
- `JDB` — global database/root map;
- `JFormDB` — form-keyed database wrapper;
- Lua evaluation/transport helpers;
- string/atomic helper surfaces.

Because registration is native-generated, API extraction should target `REGISTER_TES_NAME` / `REGISTERF` metadata rather than expecting PSC files.
