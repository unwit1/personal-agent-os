# Skyrim Modding Terminology — Camera, Input, HUD, and Equipment Display

Imported: 2026-09-24
Status: sourced deep-ingestion pass 8

## Camera systems

### PlayerCamera
Native game camera manager controlling active camera state and transitions.

### Camera state
Engine mode such as first person, third person, mount, dragon, furniture, tween/menu or other specialized states.

### First-person camera
Camera mode attached to first-person player representation and state machine.

### Third-person camera
Camera mode orbiting/following the player using configurable position, pitch, yaw and collision logic.

### Camera state hook
Native hook changing camera behavior inside one or more engine camera states.

### Camera target
Reference/point the camera tracks or orbits around.

### Camera anchor
World/skeleton-relative point used as the basis for follow position.

### Follow bone
Skeleton node used by a third-person camera as its anchor/reference.

### Camera interpolation
Smoothing movement/rotation from current camera state toward target state.

### Camera smoothing
Time/filter-based dampening of camera translation or rotation.

### Camera lag
Intentional delayed camera response used for cinematic/smooth movement.

### Camera offset
Translation relative to player/target used to position the camera.

### Shoulder offset
Horizontal offset placing the third-person camera over one shoulder.

### Camera collision
System preventing camera from passing through world geometry.

### Camera clipping
Camera intersects geometry because collision/near-plane behavior fails or is intentionally disabled.

### Near clip
Nearest distance at which geometry is rendered. First-person body/camera mods may alter near-plane behavior to reduce clipping.

### FOV
Field of view. Different camera states, weapon states, menus and mods may use different FOV values.

### Zoom
Distance/FOV-based camera adjustment, distinct from physical player movement.

### Camera pitch
Vertical look angle.

### Camera yaw
Horizontal look angle.

### Camera roll
Rotation around viewing axis. Usually minimal in vanilla but used by specialized mods/effects.

### Lock-on camera
Camera behavior oriented around a selected combat target.

### Camera-relative movement
Movement direction interpreted relative to camera orientation rather than actor facing.

### Actor-relative movement
Movement direction interpreted relative to actor facing.

### Free movement
Third-person movement allowing actor facing to differ from camera heading.

### Camera snap
Immediate camera reorientation, often used when entering target lock or switching targets.

### Camera transition
Change between first/third/mount/furniture/etc. states. Compatibility bugs commonly appear only during transitions.

### Improved Camera
Native first-person camera framework/mod that exposes full-body/immersive first-person behavior by hooking camera/player representation.

### SmoothCam
Native third-person camera framework/mod with interpolation, offsets, presets, crosshair/aim handling and compatibility integrations.

### SmoothCam preset
Serialized/configured camera settings loaded into SmoothCam.

### SmoothCam compatibility layer
Code path detecting/integrating with other camera/movement mods such as first-person mods or directional movement.

### True Directional Movement / TDM
Native movement/target-lock framework that decouples character facing from camera heading and adds target lock and related movement/camera behavior.

### Target lock
System selecting a combat target and orienting camera/actor behavior around it.

### Target point
Bone/body-part-based point on an actor used for target-lock aim/camera calculations.

### Target switch
Changing the current target lock among eligible targets.

### Melee magnetism
TDM-style facing/rotation assistance nudging attack direction toward a target.

### Controller deadzone
Stick input region ignored near center to prevent drift.

### Radial deadzone
Deadzone based on vector magnitude.

### Axial deadzone
Deadzone applied per stick axis.

### Thumbstick bounce
Controller artifact where direction briefly flips/overshoots when stick returns toward center.

## Input

### Input event
Native event representing keyboard, mouse or controller actions.

### ButtonEvent
SKSE/CommonLib native event for button press/release/hold.

### Mouse move event
Input event carrying mouse movement deltas.

### Thumbstick event
Controller analog-stick movement event.

### Device code
Numeric input identifier whose interpretation depends on keyboard/mouse/gamepad device.

### DirectInput scan code
Key code convention commonly exposed by Skyrim/SkyUI MCM hotkeys.

### Control map
Engine mapping between abstract controls and physical input devices.

### User event
Abstract Skyrim control such as Activate, Jump, Attack, Ready Weapon or Shout mapped through ControlMap.

### Input context
Mode-specific input layer such as gameplay, menu, console or other contexts.

### Input sink
Native event listener consuming/observing input events.

### Input interception
Hook preventing/altering an input before vanilla logic receives it.

### Input passthrough
Mod observes input but allows ordinary engine processing.

### Hotkey conflict
Multiple mods bind the same physical input and both react or one consumes it.

### Gamepad parity
Feature ensuring a mod's UI/functionality is fully controllable on controller, not just keyboard/mouse.

## HUD

### HUD
Heads-up display rendered during gameplay.

### HUDMenu
Primary Skyrim gameplay HUD Scaleform menu.

### HUD widget
Custom SWF/Scaleform element displayed in HUDMenu or another UI layer.

### TrueHUD
Native HUD framework exposing actor info bars, boss bars, floating text/widgets and an inter-plugin API.

### TrueHUD API
Versioned native interface other DLLs request from TrueHUD.

### API ownership
TrueHUD resource-control mechanism where a plugin can receive ownership/control over HUD resources and must not manipulate them when another mod owns them.

### Boss bar
HUD element displaying boss/priority actor health.

### Actor info bar
HUD element attached conceptually/spatially to actor health/magicka/stamina/status.

### Floating combat text
World/HUD text showing damage/healing/other values.

### HUD special resource
Shared HUD component whose control can be negotiated through a plugin API.

### Widget depth/layer
UI ordering determining which HUD elements draw over others.

### HUD scale
Scaleform/screen scaling affecting perceived size and placement across resolutions/aspect ratios.

### Ultrawide UI
HUD/menu adaptation for non-16:9 aspect ratios.

### Safe zone
Screen margin region used to keep UI away from display edges.

## Equipment display

### Immersive Equipment Displays / IED
Native framework for displaying equipped/favorited/custom items on actor skeleton nodes without relying solely on vanilla equipped-item display behavior.

### Equipment display
Visible world model attached to an actor skeleton when the item may not be actively equipped in hand.

### Gear node
Named actor skeleton node used to attach/display a weapon, shield, quiver or other item.

### GearNodeID
IED internal category for standard weapon/equipment node families such as swords, axes, daggers, bows, shields, quivers and staves.

### Placement
Logical gear-position variant such as hip, back, shoulder or custom attachment.

### MOV node
XPMSSE/IED-style move node used to change weapon position relative to skeleton hierarchy.

### CME node
Controller/helper node used in XPMSSE/IED node hierarchy for transform adjustment.

### Node override
Runtime replacement/adjustment of transform/parent/placement data for a skeleton node.

### Node monitor
IED mechanism tracking configured nodes/placements for runtime updates and integration.

### Extra node
Additional skeleton node definition loaded through IED configuration.

### Skeleton match
IED configuration logic selecting node behavior based on detected skeleton/layout.

### Custom item
IED-defined display entry that can show a model/form according to conditions independently of vanilla gear display.

### Display condition
Rule deciding whether a custom/equipment display should be shown for an actor.

### Display transform
Translation/rotation/scale applied to a displayed object relative to its attachment node.

### Equipment display preset
Reusable IED configuration describing display rules, nodes and transforms.

### Simple Dual Sheath
Native framework enabling left-hand/off-hand weapon and shield-on-back display support without legacy script-heavy dual-sheath systems.

### Dual sheath
Displaying both right- and left-hand weapon models while sheathed.

### Shield-on-back
Moving/displaying a shield on a back node while not held.

### Sheath node mismatch
Visual or animation issue where the displayed weapon node and draw/sheath animation expect different placements.

### Weapon placement animation coupling
Draw/sheath animation must correspond to the actual equipment display node location or the hand may move to the wrong position.

## Cross-system compatibility

### Camera/movement conflict
Two native plugins hook the same camera/movement logic with incompatible assumptions.

### Camera/HUD target lock integration
Target-lock framework provides target identity while HUD framework renders corresponding target widgets.

### Camera/skeleton coupling
Camera anchor/follow behavior may rely on skeleton nodes altered by custom skeletons or first-person-body frameworks.

### Equipment-display/animation coupling
IED/SDS controls model placement while OAR/behavior mods control draw/sheath animation. They must agree semantically.

### Equipment-display/physics coupling
Displayed gear can also receive IED/FSMP-style physics; transform and physics systems must not fight over the same node unexpectedly.

### Input/UI conflict
Hotkeys or menu focus cause gameplay camera/movement code to continue reacting while a menu expects exclusive input.

## Diagnostic rules

1. Record active camera state when a bug occurs; first/third/mount/dragon/furniture paths can be independently hooked.
2. Separate camera position logic from character movement rotation and from target-lock selection.
3. For target-lock issues, inspect target-point bones, skeleton compatibility and HUD/API integration.
4. For IED problems, inspect actual skeleton node names/parents and transform rules before editing weapon meshes.
5. Draw/sheath animation and displayed weapon position are different layers that must be coordinated.
6. TrueHUD API consumers must request a compatible interface version and respect resource ownership.
7. SmoothCam/TDM/Improved Camera compatibility should be evaluated by exact versions and overlapping features, not merely whether all DLLs load.

## Sources

- SmoothCam upstream: https://github.com/mwilsnd/SkyrimSE-SmoothCam
- True Directional Movement upstream: https://github.com/ersh1/TrueDirectionalMovement
- TrueHUD upstream/API: https://github.com/ersh1/TrueHUD
- Improved Camera SE-NG documentation: https://github.com/ArranzCNL/ImprovedCameraSE-NG
- Immersive Equipment Displays upstream: https://github.com/SlavicPotato/ied-dev
- Simple Dual Sheath upstream: https://github.com/SlavicPotato/SimpleDualSheath
