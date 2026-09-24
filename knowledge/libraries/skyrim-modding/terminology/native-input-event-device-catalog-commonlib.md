# Skyrim Native Input Event and Device Catalog — CommonLibSSE-NG

Imported: 2026-09-24
Source:
- `include/RE/I/InputEvent.h` blob `d87b7d92201d999978da6bb3ff67cd1302a8185e`
- `include/RE/I/InputDevices.h` blob `eb1f1107f40ddf1a0828c33a96c3310140ce8593`
Branch: `alandtse/CommonLibSSE-NG` `ng`
Status: reverse-engineered finite native enums

## Input event types

### Flat/common values

| ID | Event type |
|---:|---|
| 0 | Button |
| 1 | MouseMove |
| 2 | Char |
| 3 | Thumbstick |
| 4 | DeviceConnect |
| 5 | Kinect |

### Skyrim VR additions

| ID | VR event |
|---:|---|
| 6 | VrWandTouchpadPositionEvent |
| 7 | VrWandTouchpadSwipeEvent |

### AE/flat compile-time additions

CommonLib source also defines, under its AE compile path:

| ID | Event |
|---:|---|
| 6 | SixaxisEvent |
| 7 | MotionGestureEvent |
| 8 | AmiiboEvent |

The duplicate values 6/7 are intentional in CommonLib source: the VR and AE-only event families are compile/runtime-specific and are not treated as one shared semantic enum.

## Input device IDs — flat Skyrim

| ID | Device |
|---:|---|
| -1 | None |
| 0 | Keyboard |
| 1 | Mouse |
| 2 | Gamepad |
| 3 | FlatVirtualKeyboard |

`kFlatTotal = 4`.

## Input device IDs — Skyrim VR

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

`kVRTotal = 10`.

## InputEvent structure

CommonLib models the native event as:
- `device` — INPUT_DEVICE enum;
- `eventType` — INPUT_EVENT_TYPE enum;
- `next` — pointer to the next InputEvent in the linked event list.

This is why native input sinks often receive the head of an event chain and iterate through multiple events.

## Event subclasses

### ButtonEvent
Button/key/controller-button state with ID/user-event semantics.

### MouseMoveEvent
Mouse-axis movement.

### CharEvent
Character/text input.

### ThumbstickEvent
Analog stick position/movement.

### DeviceConnectEvent
Input device connection/disconnection state.

### VR wand touchpad events
VR-specific touchpad position/swipe inputs.

## Papyrus relationship

SKSE Papyrus APIs expose a higher-level view:
- physical key scan codes through `RegisterForKey`;
- abstract user controls through `RegisterForControl`;
- `Input.GetMappedKey`;
- `Input.GetMappedControl`.

Native `InputEvent` hooks operate below that layer and can inspect device/event structures directly.

## Diagnostic rules

1. **Button event** does not automatically mean keyboard: device identifies keyboard, mouse, gamepad, or VR controller family.
2. Prefer user-event/control names when a feature should respect rebinding.
3. Use physical scan/button IDs only when hardware-specific behavior is intentional.
4. VR uses additional device IDs and event types; a flat-only switch statement can silently drop VR input.
5. Text entry (`CharEvent`) is distinct from button presses.
6. One dispatch can contain a linked chain of InputEvents.
7. A native input hook should not assume CommonLib's compile-time AE-only IDs and VR-only IDs coexist with the same semantics.
