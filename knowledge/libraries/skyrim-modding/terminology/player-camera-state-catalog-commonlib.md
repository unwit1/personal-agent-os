# Skyrim Player Camera State Catalog — CommonLibSSE-NG

Imported: 2026-09-24
Source: `alandtse/CommonLibSSE-NG` branch `ng`
Source file: `include/RE/P/PlayerCamera.h`
Source blob SHA: `1e9278732f7f5c15186ce98a1564c8fbf9cd686c`
Status: reverse-engineered finite native enum

## Flat Skyrim SE/AE camera states

| ID | State |
|---:|---|
| 0 | `FirstPerson` |
| 1 | `AutoVanity` |
| 2 | `VATS` |
| 3 | `Free` |
| 4 | `IronSights` |
| 5 | `Furniture` |
| 6 | `PCTransition` |
| 7 | `Tween` |
| 8 | `Animated` |
| 9 | `ThirdPerson` |
| 10 | `Mount` |
| 11 | `Bleedout` |
| 12 | `Dragon` |

`kTotal = 13`, so the indexed states are 0–12.

## Skyrim VR camera states

VR inserts a dedicated state **between Animated and ThirdPerson**.

| ID | State |
|---:|---|
| 0 | `FirstPerson` |
| 1 | `AutoVanity` |
| 2 | `VATS` |
| 3 | `Free` |
| 4 | `IronSights` |
| 5 | `Furniture` |
| 6 | `PCTransition` |
| 7 | `Tween` |
| 8 | `Animated` |
| 9 | `VR` |
| 10 | `VRThirdPerson` |
| 11 | `VRMount` |
| 12 | `VRBleedout` |
| 13 | `VRDragon` |

`kVRTotal = 14`, so the indexed VR states are 0–13.

## Critical VR distinction

CommonLib source explicitly warns that camera-state indices shift in VR because `kVR` is inserted before ThirdPerson/Mount/Bleedout/Dragon.

Therefore:

| Semantic state | Flat ID | VR ID |
|---|---:|---:|
| Third Person | 9 | 10 |
| Mount | 10 | 11 |
| Bleedout | 11 | 12 |
| Dragon | 12 | 13 |

A native plugin that compares `currentState` to the flat enum value while running in VR can misclassify the active camera.

CommonLib exposes a helper pattern that accepts both the flat and VR enum values for the same semantic state.

## Key PlayerCamera concepts from current source

### cameraTarget
Actor handle used as camera target.

### worldFOV
Runtime world field of view.

### firstPersonFOV
Runtime first-person field of view.

### idleTimer
Countdown toward auto-vanity camera.

### allowAutoVanityMode
Runtime flag permitting automatic vanity camera.

### bowZoomedIn
Runtime bow-zoom state.

### isWeapSheathed
Cached weapon-sheathed state.

### ForceFirstPerson
Native PlayerCamera operation forcing first-person state.

### ForceThirdPerson
Native operation forcing third person.

### ToggleFreeCameraMode
Native operation entering/leaving free camera.

### PushCameraState
Push a requested camera state.

### IsInFirstPerson / IsInThirdPerson
Semantic native helpers preferable to raw numeric comparisons when available.

## Papyrus/SKSE relation

SKSE `Form.psc` exposes:
- `RegisterForCameraState()`
- `UnregisterForCameraState()`
- `OnPlayerCameraState(int oldState, int newState)`

Scripts receiving numeric state IDs must use the correct runtime mapping when VR is supported.

## Diagnostic rules

1. Record exact runtime (flat SE/AE vs VR) before interpreting a numeric camera state.
2. Do not hard-code 9 as "Third Person" in shared SE/VR logic.
3. Furniture, mount, bleedout and dragon states are distinct camera modes and can bypass assumptions made only for First/Third Person.
4. Camera state and player animation state are related but not identical.
5. Free camera/tween/transition states can appear transiently during menus, loading or scripted camera work.
6. Native camera mods should prefer semantic helpers/runtime-branching over naked enum integers.
