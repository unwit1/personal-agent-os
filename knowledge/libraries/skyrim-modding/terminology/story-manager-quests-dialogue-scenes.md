# Skyrim Modding Knowledge — Story Manager, Quest Startup, Dialogue, Scenes, and Event-Driven Content

Imported: 2026-09-24
Status: sourced encyclopedia pass 4

This module expands quest/dialogue knowledge into Skyrim's event-driven Story Manager and content-startup architecture.

## Story Manager

### Story Manager
Creation Kit system that receives engine gameplay events and evaluates configured node trees to start/select quests or other content.

### Story Manager Event
Engine event category such as Change Location, Kill Actor, Actor Dialogue and other supported event types.

### Event Data
Forms/values supplied with a Story Manager event and exposed to node/quest conditions.

### Change Location Event
Story Manager event fired when an actor—typically the player—enters a new Location. Event data includes actor, old Location and new Location.

### Kill Actor Event
Story Manager event associated with an actor being killed and exposing relevant killer/victim context where supported.

### Actor Dialogue Event
Event used by Story Manager to select ambient/radiant dialogue content based on actors and event conditions.

### Quest Node
Story Manager node containing one or more quests/candidate child nodes selected when an incoming event reaches it.

### Branch Node
Story Manager node grouping/evaluating child nodes according to configured selection semantics.

### Random Node
Node choosing among eligible children/quests according to Story Manager randomization settings.

### Stacked Node
Node evaluating child entries in order/stack-style behavior.

### Node conditions
Conditions tested before an event proceeds through a Story Manager node.

### Quest conditions
Conditions tested for a candidate quest before it can start from Story Manager.

### Shares Event
Story Manager option allowing an event to continue/be considered by additional eligible branches rather than being exclusively consumed by one result, depending on node semantics.

### Do All Before Repeating
Random-node behavior intended to cycle through eligible choices before repeating prior selections.

### Num Quests to Run
Node setting controlling how many candidates may be started for one event where supported.

### Story Manager quest
Quest designed to be started by event-node evaluation rather than Start Game Enabled or direct script call.

### Event data alias fill
Quest aliases can be configured to fill from Story Manager event data, allowing the started quest to capture the actor/location/object that caused the event.

### From Event alias
Alias fill mode populated from a field in the Story Manager event.

### Story Manager condition context
Condition subject/reference semantics are evaluated against event/node context; conditions that work in ordinary quest state may not have the same available references before aliases fill.

## Quest startup

### Start Game Enabled
Quest configured to start automatically during game initialization.

### Run Once
Quest flag preventing normal re-start after completion/stop where applicable.

### Allow repeated stages
Quest behavior/settings controlling whether setting an already-run stage is allowed to execute stage fragments again.

### Stop Quest
End current quest instance; stopped quests may retain saved stage/history data and can be restarted depending on flags/design.

### Reset Quest
Quest reset operation clearing/reinitializing portions of quest state. It should not be treated as a generic repair command.

### Start()
Papyrus quest start request.

### Stop()
Papyrus quest stop request.

### SetStage()
Advance/set a stage; triggers applicable stage fragments and quest logic.

### GetStage()
Read current highest/current stage value according to quest semantics.

### IsRunning()
Query whether quest is currently active/running.

### IsCompleted()
Query quest completion state.

### Quest priority
Priority used when resolving dialogue/package/quest interactions. It is not plugin load order.

### Quest type
Creation Kit classification such as side quest, miscellaneous, favor, etc., influencing UI/organizational behaviors.

## Aliases and fill timing

### Alias fill
Process resolving a quest alias to a reference/location/collection.

### Fill on quest start
Aliases generally resolve as the quest starts according to fill rules and dependencies.

### Alias fill order
Some aliases depend on earlier aliases; ordering/dependency must be designed so required references exist when evaluated.

### Find Matching Reference
Search-based fill against conditions.

### Find Matching Location
Location search fill.

### External Alias Reference
Alias filled from an alias in another quest.

### From Event
Alias filled from Story Manager event data.

### Create Reference to Object
Alias fill creates a new runtime object/reference from a base form.

### Alias Ref Type
Alias searches can select a Location Ref Type from a Location context.

### Allow Reserved
Alias setting allowing reference selection despite reservation by other quests under applicable rules.

### Reserve reference
Quest/alias system prevents conflicting radiant quests from independently selecting the same protected actor/reference.

### Essential while aliased
Alias flags can change actor essential/protected behavior for duration of alias occupancy.

### Stores Text
Alias flag enabling alias-derived text replacement tokens in quest/dialogue text.

### Alias replacement text
Dynamic quest/dialogue text resolving alias actor/location/object names at runtime.

### Clear alias
Alias loses current reference when quest/reset/lifecycle clears it; alias script lifecycle must account for this.

## Dialogue structures

### Dialogue Quest
Quest owning dialogue topics/branches and supplying aliases/conditions.

### Dialogue Branch
Grouping of dialogue topics representing a conversation branch/entry path.

### Starting Topic
Topic used to enter a dialogue branch.

### Topic / DIAL
Container for one or more INFO responses.

### INFO
Individual dialogue response record with speaker conditions, response text, scripts/fragments and links.

### Shared Info
Reusable INFO response linked/referenced by other dialogue contexts.

### Prompt
Player-facing text for a selectable dialogue choice.

### Response Text
NPC spoken/subtitle line.

### Goodbye
INFO flag ending dialogue after the response.

### Say Once
INFO setting preventing repeated use under applicable dialogue state.

### Random
INFO flag/selection behavior allowing eligible random response selection.

### Random End
Marks end of a random-response group.

### Favor level
Dialogue relationship/favor state requirements associated with relevant dialogue categories.

### Link To
Dialogue flow link directing conversation to subsequent topic(s).

### Invisible Continue
Dialogue continuation mechanism progressing to another response without a normal player choice.

### Topic Info Fragment
CK-generated Papyrus function executed when an INFO response runs.

### Begin fragment
Papyrus fragment triggered as dialogue response starts.

### End fragment
Fragment triggered after dialogue response completes.

### Speaker
Actor/reference selected to say an INFO.

### VoiceType validation
CK/dialogue export checks whether matching VoiceType audio is available/generated.

## Scenes

### Scene
Quest-owned orchestration of actors, dialogue and actions over phases.

### Scene actor
Quest alias assigned a role in the scene.

### Phase
Horizontal/time/progression section of a scene.

### Action
Unit attached to one actor/phase, such as dialogue, package, timer or script.

### Dialogue action
Scene action causing actor to speak configured dialogue.

### Package action
Scene action making actor execute a package for the action duration.

### Timer action
Scene action delaying/controlling phase progression.

### Start scene
Begin orchestration if owning quest/aliases/conditions are valid.

### Stop scene
Terminate scene and its actions.

### Scene fragment
Papyrus code associated with scene begin/end/phase lifecycle.

### Phase fragment
Fragment executed at phase start/end.

### Scene interruption
Combat, package changes, unloaded actors, alias clearing or other game state can interrupt/block expected scene progression.

### Scene package
Temporary AI behavior supplied by scene action rather than actor base package stack.

## Conditions and event-driven design

### Condition list
Ordered rows of native condition functions joined through AND/OR logic.

### OR flag
Condition row grouping where alternatives can satisfy an expression.

### Subject
Reference/context on which a condition function operates.

### Target
Alternate condition reference context where supported.

### Run On
Condition setting selecting Subject, Target, Reference, Combat Target, Linked Reference, Quest Alias, Event Data or other supported context.

### Event Data condition
Condition function resolves against Story Manager event inputs rather than a pre-filled quest alias.

### GetInCurrentLoc
Location hierarchy condition useful for determining whether an actor/reference belongs to a Location or child Location.

### GetIsID
Checks exact form/base identity.

### GetInFaction
Tests faction membership.

### GetStageDone
Tests whether a specific quest stage has run.

### GetQuestRunning
Tests quest running state.

### HasKeyword
Tests keyword membership on forms supporting it.

### GetIsVoiceType
Tests speaker/actor voice category.

## Common failure patterns

### Story Manager quest never starts
Potential causes:
- wrong event;
- node conditions false;
- quest conditions false;
- run-on/event-data context wrong;
- quest already running/completed/run-once;
- required aliases cannot fill;
- node selection semantics;
- competing/reserved references.

### Quest starts but alias empty
Fill rule/condition/dependency failed after selection.

### Dialogue never appears
Check owning quest running, branch/topic/INFO conditions, speaker/alias, priority, blocking scenes/packages and VoiceType—not just response text.

### Scene hangs
One actor cannot enter action/package, is unloaded/dead/in combat, alias wrong, navmesh path fails, or action end condition never completes.

### Fragment changed but behavior persists
Existing saved quest/script instance or old PEX winner can retain/execute different state than expected.

## Design rules encoded for Agent OS

1. Use Story Manager for world/player event-driven content rather than permanent polling when a suitable event exists.
2. Conditions needed before quest start must use event/node context, not aliases that do not exist yet.
3. Alias fill failure can prevent downstream scene/dialogue logic even when quest record itself is valid.
4. Quest priority is runtime content arbitration, not plugin priority.
5. Dialogue troubleshooting must traverse Quest → Branch → Topic → INFO → conditions → speaker/VoiceType → assets.
6. Scene failures combine quest aliases, AI packages, navmesh and dialogue; inspect all participating layers.
7. Do not restart/reset quests on important saves as a generic diagnostic action.
8. Store radiant/event quest tests with exact trigger event and expected alias values.
9. Prefer native conditions over constant Papyrus polling when the engine can evaluate the needed state directly.
10. Capture Story Manager/quest lifecycle facts in mod documentation so patches do not accidentally disable event eligibility.

## Sources
- Creation Kit Wiki Change Location Event: https://ck.uesp.net/wiki/Change_Location_Event
- Creation Kit Wiki scripting/quest reference: https://ck.uesp.net/wiki/Category:Scripting
- Creation Kit Wiki video/tutorial index: https://ck.uesp.net/wiki/Video_Tutorials
