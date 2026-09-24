# Skyrim Modding Terminology — CommonLibSSE-NG and SKSE Subsystem Map

Imported: 2026-09-24
Status: sourced frontier-deepening pass

This module is a retrieval map for native Skyrim systems exposed through CommonLibSSE-NG/SKSE. It is not an exhaustive symbol dump.

## Core singleton/system classes

### PlayerCharacter
Native player actor singleton with player-specific controls, inventory, crime, camera-adjacent and save lifecycle behavior.

### PlayerCamera
Singleton managing active camera state and first/third/mount/free/tween transitions.

### PlayerControls
Singleton handling gameplay input/control handlers.

### ControlMap
Maps abstract Skyrim controls to physical devices and input contexts.

### BSInputDeviceManager
Input-device event source for keyboard/mouse/gamepad events.

### UI
Menu manager/event source for MenuOpenCloseEvent and menu-mode changes.

### InterfaceStrings
Common menu/control/interface string identifiers.

### Calendar
Game date/time/timescale state.

### TESDataHandler
Central loaded-form/plugin data registry used to look up forms, files and loaded mods.

### TES
World/cell attach/detach and broad engine-world state.

### ProcessLists
Singleton tracking actors by processing level and actor-system collections.

### AIProcess
Per-actor AI/process state.

### HighProcessData
Detailed near-player actor state.

### BGSCreatedObjectManager
Manager for player-created objects such as custom enchanted/alchemy items.

### BGSStoryEventManager
Story Manager event-dispatch/evaluation system.

### BGSStoryManagerEventNode
Native Story Manager node representation.

### BGSFootstepManager
Footstep/event processing manager.

### Projectile::Manager
Projectile subsystem manager.

### BSTreeManager
Tree/vegetation manager.

### AnimationFileManagerSingleton
Animation-file loading management.

### BSSaveDataSystemUtility
Abstract save-file utility layer.

### BSWin32SaveDataSystemUtility
Windows save-system implementation.

### SkyrimVM
Papyrus VM host and event source.

## Forms and references

### TESForm
Base native form class.

### TESObjectREFR
Base placed/runtime reference class corresponding broadly to ObjectReference.

### Actor
Native actor/reference type combining TESObjectREFR with actor state, magic target and ActorValue ownership.

### TESNPC
NPC_ ActorBase record.

### TESRace
RACE form.

### TESQuest
QUST form plus native runtime quest state.

### BGSKeyword
KYWD form.

### BGSListForm
FLST FormList.

### TESGlobal
GLOB.

### TESObjectCELL
CELL.

### TESWorldSpace
WRLD.

### TESWeather
WTHR.

### TESClimate
CLMT.

### BGSMusicType
MUSC.

### EffectSetting
MGEF.

### SpellItem
SPEL.

### EnchantmentItem
ENCH.

### AlchemyItem
ALCH.

### TESObjectWEAP
WEAP.

### TESObjectARMO
ARMO.

### TESObjectARMA
ARMA.

### TESLevItem
LVLI.

### TESLevCharacter
LVLN.

## Scene graph / rendering classes

### NiAVObject
Base scene-graph object.

### NiNode
Scene-graph node containing child objects.

### NiTransform
Translation/rotation/scale representation.

### BSGeometry
Renderable geometry base.

### BSTriShape
Skyrim SE triangle-geometry object.

### BSLightingShaderProperty
Lighting shader property.

### BSShaderTextureSet
Texture path set.

### BSFadeNode
Common reference/model scene root supporting fade behavior.

### BGSScene
Scene quest/dialogue runtime representation.

### BShkbAnimationGraph
Actor behavior graph wrapper/event source.

### BSAnimationGraphManager
Manager coordinating animation graphs for a reference.

## Physics/native movement

### bhkWorld
Havok world wrapper.

### bhkRigidBody
Native Havok rigid body wrapper.

### bhkCharacterController
Actor movement/collision controller family.

### hkpWorld
Underlying Havok physics world type.

### hkbBehaviorGraph
Havok Behavior graph object.

## Events

### BSTEventSource
Generic native event-source template.

### BSTEventSink
Native listener interface.

### MenuOpenCloseEvent
Menu opened/closed.

### InputEvent
Keyboard/mouse/gamepad event hierarchy.

### CellAttachDetachEvent
Cell attach/detach lifecycle.

### TESActivateEvent
Reference activation.

### TESHitEvent
Hit event.

### TESDeathEvent
Death event.

### TESContainerChangedEvent
Inventory transfer.

### TESEquipEvent
Equip/unequip.

### TESMagicEffectApplyEvent
MagicEffect application.

### TESQuestStageEvent
Quest stage change.

### BGSActorCellEvent
Actor changes cell.

### BGSActorDeathEvent
Actor death tracking variant/system event.

### BSAnimationGraphEvent
Animation-event notification.

### PositionPlayerEvent
Player reposition/load transition event.

### StatsEvent
Tracked-stat event.

## SKSE interfaces

### LoadInterface
Object passed to SKSEPlugin_Load.

### QueryInterface
Legacy query-stage interface.

### MessagingInterface
Register/dispatch native lifecycle and plugin messages.

### PapyrusInterface
Register native Papyrus functions.

### SerializationInterface
Read/write plugin co-save records.

### TaskInterface
Schedule tasks onto game-safe/main/UI task queues.

### ScaleformInterface
Register native callbacks/integration with Scaleform.

### TrampolineInterface
Access SKSE executable trampoline allocation where applicable.

### ObjectInterface
SKSE object/handle-related interface family where available.

## Relocation layer

### REL::Module
Current executable module/version metadata.

### REL::Version
Runtime version abstraction.

### REL::ID
Address Library ID.

### REL::RelocationID
Multiple-runtime ID selection.

### REL::VariantID
SE/AE/VR multi-runtime identity abstraction.

### REL::Offset
Executable-relative offset.

### REL::VariantOffset
Multi-runtime offset.

### REL::Relocation<T>
Resolved pointer/function/member wrapper.

### REL::safe_write
Protected executable-memory write helper.

## Runtime feature detection

### REL::Module::IsSE
Check legacy SE runtime family.

### IsAE
AE/newer runtime family.

### IsVR
VR runtime.

### runtime version comparison
Select feature/offset/layout branch according to exact executable version.

### compile-time target
Build configuration can include/exclude VR or flat-rim code.

### runtime branch
One multi-runtime binary chooses implementation dynamically.

## Object lifetime

### NiPointer
Reference-counted smart pointer for NiObject-derived scene objects.

### BSTSmartPointer
Bethesda smart pointer used for selected engine-managed classes.

### ObjectRefHandle
Weak/re-resolvable handle to ObjectReference.

### ActorHandle
Handle to Actor.

### Handle resolution
Convert handle to smart/reference pointer when object is currently available.

### Raw pointer lifetime
Unsafe across cell unload/delete unless object ownership guarantees validity.

## Form lookup

### LookupForm
Resolve FormID through TESDataHandler/form registry.

### LookupByID
Form lookup by current full FormID.

### LookupByEditorID
Runtime EditorID lookup where engine/fix framework makes it available.

### LookupForm<type>
Typed lookup with runtime form cast.

### plugin-local FormID lookup
Resolve local form ID against named plugin file.

### GetFormFromFile
Papyrus/native lookup pattern resolving form by plugin + local ID.

## Thread/context rules

### Main thread
Primary game simulation/update thread.

### UI thread/task
Menu work may need UI task scheduling.

### Render thread
Graphics pipeline thread; avoid arbitrary game-state mutation.

### Background worker
Appropriate for isolated computation/file I/O if game objects are not touched unsafely.

### Thread affinity
Native function/class may only be safe from one engine thread.

### Game-lock ownership
Engine structures use internal locks; callbacks/hooks can deadlock if plugin acquires locks in conflicting order.

## Retrieval guidance

When troubleshooting native code, map the issue first:
- form/plugin data -> TESDataHandler/TESForm;
- actor AI -> Actor/AIProcess/ProcessLists;
- animation -> BSAnimationGraphManager/BShkbAnimationGraph;
- UI -> UI/Scaleform/Input;
- save -> SerializationInterface/BSSaveDataSystemUtility;
- camera/input -> PlayerCamera/PlayerControls/ControlMap;
- world/cell -> TES/TESObjectCELL;
- rendering/NIF -> NiAVObject/BSGeometry/shader classes;
- physics -> bhk/hkp classes.

## Sources

- CommonLibSSE-NG class hierarchy: https://ng.commonlib.dev/hierarchy.html
- CommonLibSSE-NG: https://github.com/alandtse/CommonLibSSE-NG
- SKSE64: https://github.com/ianpatt/skse64

## Provenance note

CommonLib class layouts and available methods are reverse engineered. Treat symbol existence as version/library evidence; verify runtime support before assuming every member/function is stable across SE/AE/GOG/VR.
