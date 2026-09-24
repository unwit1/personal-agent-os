# Skyrim Modding Terminology — Papyrus Event Registration, SKSE ModEvents, and Messaging

Imported: 2026-09-24
Status: sourced deep-ingestion pass 24

## Event-driven Papyrus

### Event
Callback invoked by engine/framework when something happens.

### Registration
Script instance asks engine/SKSE to receive a category of future events.

### Unregistration
Script removes registration so callbacks stop.

### Persistent registration
Registration serialized with script/save state where supported.

### Re-registration
Script restores registrations after lifecycle event/update/version migration when needed.

### Duplicate registration
Registering repeatedly can cause duplicate callbacks for some event systems or unnecessary state depending on API.

### Unregister on cleanup
Remove registrations when quest/effect/alias stops if registration outlives desired lifecycle.

## Update events

### RegisterForUpdate
Registers recurring real-time update event.

### RegisterForSingleUpdate
Schedules one real-time update callback.

### RegisterForUpdateGameTime
Registers recurring game-time update.

### RegisterForSingleUpdateGameTime
Schedules one game-time update.

### UnregisterForUpdate
Stops real-time update.

### UnregisterForUpdateGameTime
Stops game-time update.

### OnUpdate
Receives real-time update.

### OnUpdateGameTime
Receives game-time update.

### Real time
Wall-clock/game-running seconds affected by pause behavior.

### Game time
In-game calendar hours/days affected by timescale/sleep/wait.

## Menu events

### RegisterForMenu
Registers for menu open/close notifications by menu name.

### UnregisterForMenu
Stops menu notifications.

### OnMenuOpen
SKSE event when named menu opens.

### OnMenuClose
SKSE event when named menu closes.

### Menu name
Exact engine UI identifier such as InventoryMenu, MapMenu, ContainerMenu.

### Menu registration typo
Wrong string silently prevents callback.

## Animation events

### RegisterForAnimationEvent
Registers script to receive named animation graph event from actor/reference.

### UnregisterForAnimationEvent
Stops one event registration.

### UnregisterForAllAnimationEvents
Clears registrations for receiver/reference.

### OnAnimationEvent
Callback receiving source and event name.

### Animation event source
Actor/ObjectReference emitting event.

### Event-name mismatch
Behavior/animation sends name different from script registration.

### Event loss after 3D reload
Some animation-event registration scenarios need lifecycle-aware re-registration depending on source/reference and engine behavior.

## LOS events

### RegisterForLOS
Register for line-of-sight gain/loss between viewer/target.

### UnregisterForLOS
Remove LOS registration.

### OnGainLOS
Callback when line of sight gained.

### OnLostLOS
Callback when lost.

### LOS polling replacement
Use event registration instead of frequent GetLOS polling where appropriate.

## Sleep/wait events

### RegisterForSleep
Register for player sleep start/stop.

### OnSleepStart
Receives start time/duration context.

### OnSleepStop
Receives end event.

### RegisterForTrackedStatsEvent
Listen for tracked game statistic changes.

### OnTrackedStatsEvent
Receives stat name/new value.

## Key/control events

### RegisterForKey
Listen for physical key scan code.

### UnregisterForKey
Stop key.

### OnKeyDown
Key press callback.

### OnKeyUp
Key release callback.

### RegisterForControl
Listen for mapped Skyrim control rather than physical key.

### OnControlDown
Mapped control pressed.

### OnControlUp
Mapped control released.

### Physical key vs control
Control respects user bindings/device mapping; scan code is fixed physical keyboard-style identity.

## SKSE ModEvent

### ModEvent
String-named broadcast channel supplied by SKSE/PapyrusUtil-like ecosystem.

### RegisterForModEvent
Script subscribes to named mod event and callback function.

### UnregisterForModEvent
Remove subscription.

### SendModEvent
Convenience function broadcasting event name/string/float/form args.

### ModEvent.Create
Construct event handle for multi-step payload.

### PushString
Add string payload.

### PushFloat
Add float payload.

### PushForm
Add Form payload.

### Send
Dispatch constructed event.

### Callback name
Papyrus function/event name invoked on receiver.

### Event namespace
Prefix event names with mod/project ID to reduce collisions.

### Event collision
Two unrelated mods use same generic ModEvent name.

### Loose coupling
Producer does not require hard Papyrus property/reference to every consumer.

### Broadcast
All registered listeners receive event.

### No listener
Event can be sent with nobody registered; should be harmless.

## Crosshair events

### RegisterForCrosshairRef
Listen for changes to current crosshair reference.

### OnCrosshairRefChange
Callback when targeted reference changes.

### Context UI
QuickLoot/activation frameworks use crosshair state to display actions/info.

## Camera events

### RegisterForCameraState
Listen for first/third/mount/etc. camera state transitions.

### OnPlayerCameraState
Callback with old/new camera states.

### Camera enum
Numeric state identifiers should be version/documentation scoped.

## NiNode/update events

### RegisterForNiNodeUpdate
SKSE event around actor 3D/node rebuilds.

### OnNiNodeUpdate
Callback used by RaceMenu/equipment-display/body systems to reapply node data.

### Node rebuild
Race/equipment/3D reload invalidates cached node transforms/pointers.

## Quest/story events

### Story event
Engine event capable of launching Story Manager quests.

### Papyrus story event
OnStory* callbacks delivered to quests/scripts in relevant context.

### SendStoryEvent
Explicitly invoke Story Manager event.

### ModEvent vs Story Event
ModEvent is arbitrary mod-to-mod/script broadcast; Story Event participates in Skyrim's Story Manager/quest-start system.

## Native SKSE messaging

### SKSE message
C++ plugin-to-plugin/lifecycle message described in native API.

### Papyrus ModEvent
VM-level message to script instances.

### Bridge
Native plugin can dispatch Papyrus ModEvent to expose state to scripts.

### Callback thread
Native event callback may occur on game/main or framework-defined thread; do not assume Papyrus/native APIs are thread-safe everywhere.

## Registration lifecycle

### OnInit registration
Common initial subscription point for script instance.

### OnPlayerLoadGame
SKSE Papyrus event often used to refresh state after save load.

### Quest start registration
Quest script registers when quest begins.

### Quest stop cleanup
Unregister before/when quest ends for long-lived global registrations.

### ActiveMagicEffect lifecycle
Register in OnEffectStart and unregister in OnEffectFinish when subscription should only live while effect active.

### Alias lifecycle
Quest alias scripts may register when filled/initialized and clean up when cleared/quest stops.

### Save migration registration
Maintenance/version script verifies required registrations after update rather than assuming old save state is ideal.

## Failure modes

### Event never fires
Wrong registration target/name, lifecycle registration never executed, source lacks event or underlying behavior doesn't emit it.

### Event fires twice
Duplicate listeners/duplicate script instances/repeated registrations.

### Event keeps firing after feature disabled
Registration persists and was not unregistered.

### Event callback missing
RegisterForModEvent names a callback function that no longer exists after script update.

### Stale event name
Producer changed event name/version.

### Event storm
High-frequency event emitted to many listeners, producing VM pressure.

### Heavy handler
Callback performs expensive scan/work instead of queuing minimal state update.

## Diagnostic rules

1. Verify registration occurred before debugging event source.
2. Log exact event/control/menu/animation names.
3. Prefer event-driven logic to frequent polling when a reliable event exists.
4. Clean up global registrations when script lifecycle ends.
5. Namespace ModEvent names.
6. Keep event handlers cheap; schedule heavier work deliberately.
7. Distinguish Papyrus ModEvents, animation events, Story Manager events and native SKSE messages.
8. Re-test registrations on established save after script class/lifecycle changes.

## Sources

- Creation Kit Wiki Papyrus scripting/event API index: https://ck.uesp.net/wiki/Category:Scripting
- SKSE64 PluginAPI messaging: https://github.com/ianpatt/skse64/blob/master/skse64/PluginAPI.h
- CommonLibSSE-NG event/message interfaces: https://github.com/alandtse/CommonLibSSE-NG
