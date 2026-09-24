# MCM Helper 1.6.3 Source Manifest

Snapshot date: 2026-09-24
Upstream: `Exit-9B/MCM-Helper`
Pinned source commit: `a30334864ea46ab6ee9e74bca06187630b67c039`
Source branch: `main`
Status: current-source snapshot, not a v1.6.3 GitHub release tag

## Version identity

At this pinned commit, `CMakeLists.txt` declares:
- project version **1.6.3**;
- `PLUGIN_VERSION 15`;
- `MCM_VERSION_RELEASE=15`.

The public `MCM.GetVersionCode()` native returns this release code.

GitHub's latest formal release tag is still v1.6.2, while the current source and Nexus distribution have moved to 1.6.3. Preserve that distinction when citing source or binary releases.

## Public Papyrus sources

| Script | Extends | Blob SHA | Function/event declarations |
|---|---|---|---:|
| `MCM` | — | `da22ff3d5114101017302201149b44ee44ba07f1` | 10 |
| `MCM_ConfigBase` | `SKI_ConfigBase` | `5cd277f23729a2229ee67a21d14691eaa4ceaa33` | 15 |
| `SKI_ConfigBase` | `SKI_QuestBase` | `87f2f211cee2458ba40ddcbb85a4342c97af2553` | 10 |
| `SKI_ConfigMenu` | `MCM_ConfigBase` | `80f8e681b8681778dcc72ec850ec37679e2a2cca` | 17 |
| `SKI_QuestBase` | `Quest` | `bb57000176bd59f9ecc2ce1f36242e5f79a54de7` | 6 |

## Schemas

- `docs/config.schema.json` — blob `c1e22bf1a843f62a4948a0d9c90be5d3bc6dccc4`
- `docs/keybinds.schema.json` — blob `5df5d9a43673149b51b95ec17c4fd73dbbb86463`

## Native/storage components

Important source files in this snapshot include:
- `src/SettingStore.cpp` — default/user INI settings;
- `src/ConfigStore.cpp` — declarative MCM config loading;
- `src/KeybindManager.cpp` — keybind config + user registration persistence;
- `src/Config/ValueSource.*` — property/mod-setting/global value backends;
- `src/Config/Action.*` — function/event/console actions;
- `src/Papyrus/MCM*.cpp` — native Papyrus registration.

## Runtime lifecycle

Current `main.cpp`:
- requires at least the configured SKSE/XSE interface level;
- reads settings and saved keybind registrations during plugin load;
- reads configs after game load;
- registers native input handling after input is loaded;
- clears/rebuilds relevant in-memory config/key state on new game/load transitions.

## Evidence policy

Use this exact source commit for API/schema facts. Runtime-support claims still belong in the version matrix and should be tied to the actual distributed file/runtime combination rather than inferred only from source.
