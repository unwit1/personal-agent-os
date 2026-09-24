# Skyrim Native Camera, Input, and Control Context Catalog — CommonLibSSE-NG

Imported: 2026-09-24
Status: source-derived native enum/identifier catalog

## Sources

- `PlayerCamera.h` blob `1e9278732f7f5c15186ce98a1564c8fbf9cd686c`
- `InputDevices.h` blob `eb1f1107f40ddf1a0828c33a96c3310140ce8593`
- `InputEvent.h` blob `d87b7d92201d999978da6bb3ff67cd1302a8185e`
- `UserEvents.h` blob `e65f65854f7f4d8d1311c656c21e90777b60b7b3`
- `PCGamepadType.h` blob `0d649e321a9335a5fbc1b175bc79606b48eb6cdc`
- `ButtonEvent.h` blob `fdb38b90e7ed426ed7a2d4537663677e65cbda10`
- `ThumbstickEvent.h` blob `377316ae8f1028c71b0228022605c877fc04becb`

Upstream: https://github.com/alandtse/CommonLibSSE-NG

## Player camera states — flat Skyrim

| ID | State |
|---:|---|
| 0 | FirstPerson |
| 1 | AutoVanity |
| 2 | VATS |
| 3 | Free |
| 4 | IronSights |
| 5 | Furniture |
| 6 | PCTransition |
| 7 | Tween |
| 8 | Animated |
| 9 | ThirdPerson |
| 10 | Mount |
| 11 | Bleedout |
| 12 | Dragon |

`kTotal = 13`.

## Player camera states — Skyrim VR

VR inserts a dedicated VR state **at index 9**, after Animated. That shifts the corresponding third-person/mount/bleedout/dragon slots.

| ID | VR state |
|---:|---|
| 0 | FirstPerson |
| 1 | AutoVanity |
| 2 | VATS |
| 3 | Free |
| 4 | IronSights |
| 5 | Furniture |
| 6 | PCTransition |
| 7 | Tween |
| 8 | Animated |
| 9 | VR |
| 10 | VRThirdPerson |
| 11 | VRMount |
| 12 | VRBleedout |
| 13 | VRDragon |

`kVRTotal = 14`.

### Critical VR rule

Do not compare a flat camera-state integer directly against VR after index 8. CommonLib explicitly exposes dual-state comparison because:
- flat ThirdPerson = 9;
- VR-specific state = 9;
- VR ThirdPerson = 10.

A plugin using raw flat indices on VR can therefore misclassify camera state without crashing.

## Input device IDs — flat

| ID | Device |
|---:|---|
| -1 | None |
| 0 | Keyboard |
| 1 | Mouse |
| 2 | Gamepad |
| 3 | FlatVirtualKeyboard |

Flat `kTotal = 4`.

## Input device IDs — VR

| ID | Device |
|---:|---|
| -1 | None |
| 0 | Keyboard |
| 1 | Mouse |
| 2 | Gamepad |
| 3 | VivePrimary |
| 4 | ViveSecondary |
| 5 | OculusPrimary |
| 6 | OculusSecondary |
| 7 | WMRPrimary |
| 8 | WMRSecondary |
| 9 | VRVirtualKeyboard |

VR `kTotal = 10`.

### Virtual keyboard

CommonLib's `INPUT_DEVICES::VirtualKeyboard()` selects:
- flat virtual keyboard on non-VR;
- last VR device slot on VR.

## Input event types

| ID | Event type |
|---:|---|
| 0 | Button |
| 1 | MouseMove |
| 2 | Char |
| 3 | Thumbstick |
| 4 | DeviceConnect |
| 5 | Kinect |
| 6 | VR Touchpad Position (VR) / Sixaxis (AE) |
| 7 | VR Touchpad Swipe (VR) / MotionGesture (AE) |
| 8 | Amiibo (AE) |

### Shared numeric IDs across mutually exclusive runtime families

CommonLib source intentionally reuses:
- 6 for VR touchpad-position vs AE Sixaxis;
- 7 for VR touchpad-swipe vs AE MotionGesture.

Do not infer event class from integer alone without runtime family.

## ButtonEvent state semantics

CommonLib derives:

- **Pressed:** value > 0.
- **Repeating:** held duration > 0.
- **Down:** pressed and held duration == 0.
- **Held:** pressed and repeating.
- **Up:** value == 0 and repeating.

This is more precise than treating every button callback as a simple key-down event.

## Thumbstick IDs

- `0x0B` — Left Thumbstick.
- `0x0C` — Right Thumbstick.

Thumbstick events carry X and Y float values.

## Input contexts — SE/VR baseline

| ID | Context |
|---:|---|
| 0 | Gameplay |
| 1 | MenuMode |
| 2 | Console |
| 3 | ItemMenu |
| 4 | Inventory |
| 5 | DebugText |
| 6 | Favorites |
| 7 | Map |
| 8 | Stats |
| 9 | Cursor |
| 10 | Book |
| 11 | DebugOverlay |
| 12 | Journal |
| 13 | TFCMode |
| 14 | MapDebug |
| 15 | Lockpicking |
| 16 | Favor |

Flat SE total is 17. CommonLib's current VR source also exposes `kVRTotal = 17`, but explicitly notes that more VR contexts may exist and still need reverse engineering; VR `kNone = 22`.

## Input contexts — newer AE family

Current CommonLib source inserts Marketplace before Favor:

| ID | Context |
|---:|---|
| 0 | Gameplay |
| 1 | MenuMode |
| 2 | Console |
| 3 | ItemMenu |
| 4 | Inventory |
| 5 | DebugText |
| 6 | Favorites |
| 7 | Map |
| 8 | Stats |
| 9 | Cursor |
| 10 | Book |
| 11 | DebugOverlay |
| 12 | Journal |
| 13 | TFCMode |
| 14 | MapDebug |
| 15 | Lockpicking |
| 16 | Marketplace |
| 17 | Favor |

AE total is 18 in the current source.

## User-event enable flags

| Bit | Flag |
|---|---|
| `0x00000001` | Movement |
| `0x00000002` | Looking |
| `0x00000004` | Activate |
| `0x00000008` | Menu |
| `0x00000010` | Console |
| `0x00000020` | POVSwitch |
| `0x00000040` | Fighting |
| `0x00000080` | Sneaking |
| `0x00000100` | MainFour |
| `0x00000200` | WheelZoom |
| `0x00000400` | Jumping |
| `0x00000800` | VATS |
| `0x80000000` | Invalid |

`kAll` is all bits set.

These flags control broad input categories such as movement, looking, activation, fighting and menus. They are not the same thing as individual mapped control names.

## Gamepad map type

- `0` — DirectX.
- `1` — Orbis.

## Canonical native user-event strings

Current CommonLib exposes **102 non-empty UserEvents strings**:

- `Forward`
- `Back`
- `Strafe Left`
- `Strafe Right`
- `Move`
- `Look`
- `Activate`
- `Left Attack/Block`
- `Right Attack/Block`
- `Dual Attack`
- `ForceRelease`
- `Pause`
- `Ready Weapon`
- `Toggle POV`
- `Jump`
- `Journal`
- `Sprint`
- `Sneak`
- `Shout`
- `KinectShout`
- `Grab`
- `Run`
- `Toggle Always Run`
- `Auto-Move`
- `Quicksave`
- `Quickload`
- `NewSave`
- `Inventory`
- `Stats`
- `Map`
- `Screenshot`
- `Multi-Screenshot`
- `Console`
- `CameraPath`
- `Tween Menu`
- `Take All`
- `Accept`
- `Cancel`
- `Up`
- `Down`
- `Left`
- `Right`
- `PageUp`
- `PageDown`
- `Pick`
- `PickNext`
- `PickPrevious`
- `Cursor`
- `Kinect`
- `SprintStart`
- `SprintStop`
- `sneakStart`
- `sneakStop`
- `blockStart`
- `blockStop`
- `blockBash`
- `attackStart`
- `attackPowerStart`
- `reverseDirection`
- `Unequip`
- `Zoom In`
- `Zoom Out`
- `RotateItem`
- `Left Stick`
- `PrevPage`
- `NextPage`
- `PrevSubPage`
- `NextSubPage`
- `LeftEquip`
- `RightEquip`
- `ToggleFavorite`
- `Favorites`
- `Hotkey1`
- `Hotkey2`
- `Hotkey3`
- `Hotkey4`
- `Hotkey5`
- `Hotkey6`
- `Hotkey7`
- `Hotkey8`
- `Quick Inventory`
- `Quick Magic`
- `Quick Stats`
- `Quick Map`
- `ToggleCursor`
- `Wait`
- `Click`
- `MapLookMode`
- `Equip`
- `DropItem`
- `Rotate`
- `NextFocus`
- `PreviousFocus`
- `SetActiveQuest`
- `PlacePlayerMarker`
- `XButton`
- `YButton`
- `ChargeItem`
- `PlayerPosition`
- `LocalMap`
- `LocalMapMoveMode`
- `Item Zoom`

These are engine/native event identifiers. They overlap heavily with, but are not identical to, the shorter SKSE `Input.psc` valid-control list already cataloged in `skse-ui-input-identifier-catalog.md`.

## ControlMap semantics

A `UserEventMapping` stores:
- event ID;
- input key;
- modifier;
- context index;
- remappable flag;
- linked flag;
- user-event group flags.

A ControlMap maintains:
- one mapping set per input context/device;
- a context-priority stack;
- enabled/stored control masks;
- text-entry count;
- keyboard/mouse ignore state;
- current gamepad map type.

### Text input

`ControlMap::AllowTextInput` participates in suppressing ordinary gameplay handling while UI text fields are active. Native/menu mods should coordinate this rather than only swallowing individual key events.

## Diagnostic rules

1. Record **runtime family + camera state**, not only the numeric camera-state ID.
2. Input event ID 6/7 has different meanings in AE and VR.
3. Device ID 3 means flat virtual keyboard on flat Skyrim but Vive Primary on VR.
4. Use input context when resolving a mapped key; the same event can map differently by context.
5. Distinguish physical ButtonEvent ID codes from UserEvent names.
6. Distinguish broad enabled-control flags from individual bindings.
7. Do not assume VR's currently reverse-engineered context list is exhaustive; CommonLib source explicitly leaves that open.
8. A mod that works with keyboard but fails with controller may be wrong at device/context/mapping level even when Papyrus `RegisterForControl` looks correct.
