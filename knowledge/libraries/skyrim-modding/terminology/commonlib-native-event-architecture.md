# CommonLib Native Event Sources, Sinks, and Gameplay Event Architecture

Imported: 2026-09-24
Upstream: `alandtse/CommonLibSSE-NG` branch `ng`
Sources:
- `include/RE/B/BSTEvent.h` blob `b3aabb35abb6f75772fac087c6386c8f033be6b2`
- `include/RE/S/ScriptEventSourceHolder.h` blob `97b9a9e988d1c8d814ab6c14ccb5753d0207845f`
- `include/RE/Q/QuestEvents.h` blob `da65a10b3e5e7c254cc047b6007f737235dd0566`
Status: reverse-engineered event architecture

## BSTEventSource<T>

Bethesda's typed native event producer. A source coordinates sinks interested in payload type `T`.

### AddEventSink
Registers a `BSTEventSink<T>`.

### RemoveEventSink
Unregisters it.

### SendEvent
Dispatches a payload through the source.

## BSTEventSink<T>

Typed native listener interface whose `ProcessEvent` receives event data.

### BSEventNotifyControl
Return control used by event processing/continuation according to source implementation.

## ScriptEventSourceHolder

CommonLib's current reverse-engineered holder exposes many gameplay event sources, including:

- TESActivateEvent
- TESActiveEffectApplyRemoveEvent
- TESActorLocationChangeEvent
- TESBookReadEvent
- TESCellAttachDetachEvent
- TESCellFullyLoadedEvent
- TESCombatEvent
- TESContainerChangedEvent
- TESDeathEvent
- TESEnterBleedoutEvent
- TESEquipEvent
- TESFastTravelEndEvent
- TESFormDeleteEvent
- TESFurnitureEvent
- TESGrabReleaseEvent
- TESHitEvent
- TESInitScriptEvent
- TESLoadGameEvent
- TESLockChangedEvent
- TESMagicEffectApplyEvent
- TESMoveAttachDetachEvent
- TESObjectLoadedEvent
- TESOpenCloseEvent
- TESPlayerBowShotEvent
- TESQuestInitEvent
- TESQuestStageEvent
- TESQuestStartStopEvent
- TESResetEvent
- TESResolveNPCTemplatesEvent
- TESSleepStopEvent
- TESSpellCastEvent
- TESSwitchRaceCompleteEvent
- TESTopicInfoEvent
- TESTrackedStatsEvent
- TESUniqueIDChangeEvent
- TESWaitStopEvent

Other event families have their own managers/sources and are not necessarily members of this one holder.

## Quest event layer

`QuestEvents.h` defines additional native quest-event structures/helpers. Keep these distinct from:
- Papyrus Quest events;
- Story Manager events;
- SKSE ModEvents;
- powerofthree Papyrus Extender event callbacks.

They can describe the same gameplay moment through different dispatch and payload layers.

## Event-layer taxonomy

### Engine BSTEvent
C++ typed source/sink event.

### Papyrus script event
VM callback delivered to script instance.

### SKSE MessagingInterface message
Native plugin lifecycle/inter-plugin message.

### SKSE Papyrus ModEvent
String-named VM broadcast.

### Animation graph event
String event from behavior/animation graph.

### Story Manager event
Event data evaluated by Story Manager nodes.

### Framework event
Provider-specific event extensions such as po3 extended hit/weather/quest events.

## Registration and lifetime rules

1. Native sinks must not outlive their valid registration/lifetime relationship.
2. Event callback thread/context matters; arbitrary engine state may not be thread-safe.
3. Do not assume every event source exists before its owning subsystem initializes.
4. Papyrus registration and BSTEventSink registration are independent.
5. Similar names do not imply identical payloads: native `TESHitEvent`, Papyrus `OnHit`, and po3 `OnHitEx` are different interfaces.
6. Prefer a suitable event source over high-frequency polling.
7. Keep high-frequency handlers small and defer expensive processing.

## Coverage

The companion `sources/commonlib-event-header-manifest.md` inventories **93** event-related headers in this CommonLib source snapshot, spanning gameplay, UI, input, animation, Havok, quest and VR event types.
