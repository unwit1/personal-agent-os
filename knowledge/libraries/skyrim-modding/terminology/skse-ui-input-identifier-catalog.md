# Skyrim SKSE UI Menu, Input Control, and Actor Action Identifiers

Imported: 2026-09-24
Sources:
- `ianpatt/skse64/scripts/modified/UI.psc` blob `2a8f18921c3ba382ea326ae677c686e75f8db99d`
- `ianpatt/skse64/scripts/modified/Input.psc` blob `14e380527f376cf41e875b8951233f285facaade`
- `ianpatt/skse64/scripts/modified/Form.psc` blob `c8410ae0d52383d03c214e0e07d402211b5cef67`
Status: source-derived identifier catalog

## Valid SKSE UI menu names

These strings are documented by SKSE's `UI.psc` for functions requiring `menuName`.

| Menu identifier | Source line |
|---|---:|
| `InventoryMenu` | 4 |
| `Console` | 5 |
| `Dialogue Menu` | 6 |
| `HUD Menu` | 7 |
| `Main Menu` | 8 |
| `MessageBoxMenu` | 9 |
| `Cursor Menu` | 10 |
| `Fader Menu` | 11 |
| `MagicMenu` | 12 |
| `Top Menu` | 13 |
| `Overlay Menu` | 14 |
| `Overlay Interaction Menu` | 15 |
| `Loading Menu` | 16 |
| `TweenMenu` | 17 |
| `BarterMenu` | 18 |
| `GiftMenu` | 19 |
| `Debug Text Menu` | 20 |
| `MapMenu` | 21 |
| `Lockpicking Menu` | 22 |
| `Quantity Menu` | 23 |
| `StatsMenu` | 24 |
| `ContainerMenu` | 25 |
| `Sleep/Wait Menu` | 26 |
| `LevelUp Menu` | 27 |
| `Journal Menu` | 28 |
| `Book Menu` | 29 |
| `FavoritesMenu` | 30 |
| `RaceSex Menu` | 31 |
| `Crafting Menu` | 32 |
| `Training Menu` | 33 |
| `Mist Menu` | 34 |
| `Tutorial Menu` | 35 |
| `Credits Menu` | 36 |
| `TitleSequence Menu` | 37 |
| `Console Native UI Menu` | 38 |
| `Kinect Menu` | 39 |

### Menu-name rules

- Use the exact engine/SKSE identifier, including spaces where present.
- User-facing labels are not reliable substitutes.
- `RegisterForMenu`, `UI.IsMenuOpen`, UI Get/Set/Invoke calls and other menu integrations should share the same canonical identifier.
- Custom-menu frameworks can register additional menus not present in this vanilla/SKSE list.

## Valid mapped control names from SKSE Input.psc

- `Forward`
- `Back`
- `Strafe Left`
- `Strafe Right`
- `Move`
- `Look`
- `Left Attack/Block`
- `Right Attack/Block`
- `Activate`
- `Ready Weapon`
- `Tween Menu`
- `Toggle POV`
- `Zoom Out`
- `Zoom In`
- `Jump`
- `Sprint`
- `Shout`
- `Sneak`
- `Run`
- `Toggle Always Run`
- `Auto-Move`
- `Favorites`
- `Hotkey1`
- `Hotkey2`
- `Hotkey3`
- `Hotkey4`
- `Hotkey5`
- `Hotkey6`
- `Hotkey7`
- `Hotkey8`
- `Quicksave`
- `Quickload`
- `Wait`
- `Journal`
- `Pause`
- `Screenshot`
- `Multi-Screenshot`
- `Console`
- `CameraPath`
- `Quick Inventory`
- `Quick Magic`
- `Quick Stats`
- `Quick Map`

### Device types

- `0` — keyboard
- `1` — mouse
- `2` — gamepad
- `0xFF`/default — auto detect

Use `Input.GetMappedKey(control, deviceType)` when a mod should respect the player's current bindings instead of hard-coding a scan code.

## Actor Action event types

SKSE `Form.psc` documents these values for `RegisterForActorAction` / `OnActorAction`.

| ID | Action |
|---:|---|
| 0 | Weapon Swing (Melee weapons that are swung, also barehand) |
| 1 | Spell Cast (Spells and staves) |
| 2 | Spell Fire (Spells and staves) |
| 3 | Voice Cast |
| 4 | Voice Fire |
| 5 | Bow Draw |
| 6 | Bow Release |
| 7 | Unsheathe Begin |
| 8 | Unsheathe End |
| 9 | Sheathe Begin |
| 10 | Sheathe End |

### Actor Action slots

- `0` — Left Hand
- `1` — Right Hand
- `2` — Voice

## Registration APIs

Relevant `Form.psc` registrations include:
- `RegisterForKey`
- `RegisterForControl`
- `RegisterForMenu`
- `RegisterForModEvent`
- `RegisterForCameraState`
- `RegisterForCrosshairRef`
- `RegisterForActorAction`
- `RegisterForNiNodeUpdate`

## Diagnostic rules

1. Exact menu/control strings are API identifiers; a space/capitalization mismatch can prevent events/lookups.
2. Prefer mapped controls for user-remappable gameplay actions.
3. Physical DX key registration and abstract control registration solve different problems.
4. UI text-entry mode should suppress global hotkeys that would otherwise fire while the user types.
5. Actor Action IDs are SKSE event categories, not behavior-graph animation-event names.
6. A UI mod may add custom menus outside this finite SKSE list; record their provider/framework separately.
