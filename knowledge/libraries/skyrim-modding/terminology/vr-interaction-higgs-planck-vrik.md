# Skyrim Modding Terminology — Skyrim VR Interaction, HIGGS, PLANCK, and VRIK

Imported: 2026-09-24
Status: sourced frontier-deepening pass

## VR interaction stack

### HIGGS
**Expansion:** Hand Interaction and Gravity Gloves for Skyrim VR. Native SKSEVR framework adding physics-driven hand/object interaction, gravity-glove grabbing, two-handing, weapon collision and haptics.

### PLANCK
**Expansion:** Physical Animation and Character Kinetics. Native Skyrim VR framework adding physical animation/active-ragdoll-style actor interaction, physics-driven melee and body grabbing/contact behavior.

### VRIK
VR body/avatar framework reconstructing player's visible body from HMD/controller tracking and providing weapon holsters/gesture systems.

### SKSEVR
Skyrim Script Extender for Skyrim VR.

### Skyrim VR Tools
Framework utilities used by VR mods for controller/haptic/input integration.

## HIGGS concepts

### Physics grab
Object is moved through Havok/constraint/velocity behavior rather than vanilla instant Activate pickup alone.

### Gravity gloves
Point/reach toward distant object and pull it to hand.

### Hand collision
Tracked VR hand has collision semantics with world objects.

### Weapon collision
Held weapon participates in physical collisions.

### Two-handing
Second controller grips weapon and constrains/orients it together with primary hand.

### Grip
Controller input representing physical grab.

### Grabbed object
Reference currently constrained/controlled by VR hand.

### Grab constraint
Havok constraint connecting object to hand representation.

### Finger curl
Per-finger tracked/animated value exposed to compatible systems.

### Haptics
Controller vibration feedback on contact/grab/holster/etc.

### Selection beam
Pointer/visual target aid optionally disabled by HIGGS config.

### ForcePhysicsGrab
HIGGS config behavior forcing held objects into physics-driven movement.

### HIGGS API
Native C++ interface for callbacks/state.

### PostPostLoad API timing
HIGGS upstream states its C++ interface should be acquired at SKSE PostPostLoad or later, not PostLoad.

### Weapon-grab callback
API callback when player grabs weapon/two-hands/etc.

## PLANCK concepts

### Physical animation
Character remains animation-driven but physics can influence/reroute body bones in response to player/world contact.

### Active ragdoll
Physics constraints/motors try to follow animation target while allowing dynamic physical response.

### Body grabbing
Player can physically grab NPC limbs/body.

### Physical melee hit
Weapon collision determines contact more directly than vanilla abstract melee trace.

### PLANCK hit event
Extension of TESHitEvent with additional physical hit information.

### Node hit
Extended hit data can report which skeleton node/body part was struck.

### PLANCK API
Native C++ interface for integrations.

### PLANCK PostPostLoad timing
Upstream likewise documents interface acquisition at PostPostLoad or later.

### Ragdoll force
Physical impulse applied through body.

### Grab resistance
Actor/body resists player movement according to mass/constraints/config.

### Physical stagger
Collision/force interaction contributes to actor reaction.

## VRIK concepts

### Full-body avatar
Visible player body positioned to tracked HMD/controllers.

### Inverse kinematics
Solve skeleton joint rotations from tracked head/hand targets.

### IK target
Tracked hand/head/pelvis/foot target used to solve body.

### Body calibration
User height/arm/body alignment setup.

### VRIK holster
Body-relative location where weapon can be stored/drawn physically.

### Holster gesture
Move/grip weapon near configured body slot.

### Gesture input
Hand/controller movement pattern mapped to spell/power/action.

### Selfie mode
Camera/avatar mode allowing player to view body externally.

### VRIK API
Native interface consumed by VR mods such as HIGGS for body/hand data.

## VR camera/body differences

### HMD pose
Head position/orientation controlled by headset.

### Tracked controller pose
Hand transform comes from VR hardware.

### Room-scale movement
Physical user movement independent of thumbstick locomotion.

### Playspace
Tracked real-world coordinate space.

### Recenter
Reset VR origin/orientation.

### Seated mode
VR configuration adjusting body/camera for seated play.

### Head-body decoupling
Player head can move independently from actor root.

### First-person body
In VR, visible body/arms may be synthesized differently than flat-screen first-person meshes.

### Body clipping
HMD enters player torso/geometry due calibration/IK/camera offsets.

## VR input

### OpenVR/OpenXR controller input
Runtime-specific tracked-button/axis system distinct from DirectInput keyboard/gamepad assumptions.

### Grip
Physical grab button.

### Trigger
Index trigger.

### Touchpad/thumbstick
Movement/menu input.

### Controller role
Left/right tracked controller.

### Haptic pulse
Short vibration command.

### Gesture
Pose/motion interpretation used as command.

### Input remap
Controller binding through SteamVR/OpenXR layer can alter physical button semantics before Skyrim sees them.

## VR UI

### World-space UI
Menu/panel rendered in 3D space.

### Laser pointer
Ray-based menu interaction.

### Hand pointer
Controller acts as cursor.

### VR menu plane
Scaleform menu presented as floating screen/plane.

### Physical inventory
Modded interaction representing items spatially instead of flat menu.

### Spell wheel
VR radial/world UI allowing quick equipment selection.

## VR compatibility implications

### Flat-screen-only camera mod
Assumes PlayerCamera/first-person body architecture incompatible with VR HMD tracking.

### VR-specific DLL
Built for SkyrimVR.exe offsets/ABI.

### SE plugin port to VR
Requires CommonLibVR/VR Address Library/runtime mapping and feature review.

### Interaction conflict
Two VR mods both own hand collision/grab/weapon behavior.

### Physics conflict
HIGGS/PLANCK/FSMP/CBPC interactions can touch physics at different layers.

### Node dependency
VRIK/HIGGS/PLANCK depend on skeleton node names/layout.

### Animation mismatch
Flat-screen animation assumes hand/weapon positions that conflict with physical VR hand tracking.

## Diagnostic rules

1. Treat HMD/controller transforms as authoritative VR inputs, not ordinary camera animation.
2. Separate VRIK IK/body, HIGGS object/hand interaction and PLANCK actor physical animation.
3. HIGGS/PLANCK APIs must be acquired at documented lifecycle stage.
4. VR native plugins need SkyrimVR-specific ABI support even when config/Papyrus looks identical to SE.
5. Skeleton node changes can break all three frameworks simultaneously.
6. Test physical interaction and ordinary Activate separately.
7. Flat-screen compatibility claims do not imply VR support.

## Sources

- HIGGS upstream: https://github.com/adamhynek/higgs
- PLANCK upstream: https://github.com/adamhynek/activeragdoll
- VR Address Library: https://github.com/alandtse/skyrim_vr_address_library
