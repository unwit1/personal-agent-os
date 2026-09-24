# Skyrim Plugin Record Schema — Quests, Aliases, Dialogue, and Scenes

Imported: 2026-09-24
Status: field-level schema deepening

## QUST

Major structures:
- EDID: EditorID.
- VMAD: quest script + fragment + alias script metadata.
- FULL: journal/display name.
- DNAM: quest flags, priority, type and related data.
- ENAM/PNAM/QNAM/etc.: event/story-manager relationships depending schema.
- INDX blocks: quest stages.
- QSDT/QSTA/CNAM: stage metadata and log/fragment data.
- QOBJ: objectives.
- NNAM: objective text.
- QTGL: objective targets.
- ALST: Reference Alias definitions.
- ALLS: Location Alias definitions.
- alias flags, fill type, conditions and dependencies.
- Story Manager event data.

### Stage
A stage is identified by index and can contain one or more log entries/fragments.

### Alias
Each alias has a stable alias ID inside QUST and a fill strategy.

### Reference Alias
Can be:
- Specific Reference;
- Unique Actor;
- Create Reference;
- Find Matching Reference;
- From Event;
- External Alias;
- Forced by script.

### Location Alias
Can resolve from specific location, event, reference location or matching-location logic.

Patch semantics:
- Copying only stage data while discarding aliases/VMAD can break quest.
- Alias IDs are API-like; scripts/fragments refer to them.
- Stage fragments are generated script metadata, not plain text.
- Quest priority/start flags can change dialogue/package behavior globally.

## DIAL — Dialogue Topic

Key concepts:
- topic subtype/type;
- quest ownership;
- branch/topic grouping;
- subtype-specific metadata;
- linked INFO children.

Patch semantics:
- DIAL itself may look simple while actual response logic lives in INFO.
- Do not diagnose dialogue from DIAL winner alone.

## INFO — Topic Info / dialogue response

Major data:
- parent DIAL;
- conditions;
- speaker;
- response text;
- prompt;
- flags;
- emotion type/value;
- response metadata;
- VoiceType/voice asset resolution through speaker;
- linked topics;
- favor/said-once/random/end-conversation flags;
- Papyrus fragment metadata.

Patch semantics:
- Conditions are usually the highest-value conflict area.
- Forwarding one mod's response text while replacing another mod's conditions can make lines fire in unintended contexts.
- Voice files are named from plugin/FormID/VoiceType conventions and must correspond to final INFO identity.

## Dialogue branches

### Branch
Quest-owned grouping of related dialogue topics.

### Blocking branch
Can monopolize dialogue selection according to priority/conditions.

### Normal branch
Participates in ordinary selection.

### Topic priority
Quest/branch/topic ordering interacts with conditions.

## SCEN — Scene

Major structures:
- actors/aliases;
- phases;
- actions;
- dialogue actions;
- package actions;
- timer actions;
- start/stop conditions;
- flags;
- scene fragments.

Patch semantics:
- Alias IDs referenced by scene actions must remain valid.
- Editing QUST aliases can silently break SCEN action targets.
- Scenes are stateful at runtime; established saves may already be mid-phase.

## SMQN / SMBN / SMEN and Story Manager nodes

Story Manager record families describe:
- event trees;
- branching conditions;
- quest candidate selection;
- random/priority behavior.

Patch semantics:
- Story Manager conflict can stop a quest from ever starting even when QUST record itself is fine.

## DLBR / DLVW and dialogue views

Editor organization records used by CK to lay out dialogue graphs. They can matter to authoring/editor usability even when game runtime behavior is primarily DIAL/INFO/QUST.

## VMAD in quests/dialogue

VMAD may contain:
- attached scripts;
- properties;
- quest fragments;
- stage fragment metadata;
- alias scripts;
- TopicInfo fragment metadata.

Do not strip VMAD as “noise.”

## Voice asset identity

Typical path:
`Sound/Voice/<PluginName.ext>/<VoiceType>/<InfoFormID>_<response>.fuz`

Exact filename rules/tool output should be generated from CK/voice tools rather than manually guessed for release.

## Quest conflict workflow

1. Compare DNAM/start/priority.
2. Compare aliases by alias ID and semantic role.
3. Compare stages/objectives.
4. Inspect VMAD.
5. Inspect Story Manager nodes.
6. Inspect DIAL/INFO conditions.
7. Verify voice files.
8. Test quest lifecycle on fresh save.
9. Test update path separately if mid-save support is promised.

## Sources

- TES5Edit meta QUST definitions
- Creation Kit Quest/Dialogue/Scene documentation
- xEdit record schemas
## Native quest state and event enums — CommonLibSSE-NG

Sources:
- `TESQuest.h` blob `00297a304022c9d4b4b1a6666f026b7715e97d5c`
- `QuestEvents.h` blob `da65a10b3e5e7c254cc047b6007f737235dd0566`
- `QuestObjectiveStates.h` blob `9afd1a6c1aad142647cb4f396d77e6e825881dd1`

### QuestFlag

| Flag | Bit/value |
|---|---|
| StopStart | -1 special value |
| Enabled | 1 << 0 |
| Completed | 1 << 1 |
| AddIdleToHello | 1 << 2 |
| AllowRepeatStages | 1 << 3 |
| StartsEnabled | 1 << 4 |
| DisplayedInHUD | 1 << 5 |
| Failed | 1 << 6 |
| StageWait | 1 << 7 |
| RunOnce | 1 << 8 |
| ExcludeFromExport | 1 << 9 |
| WarnOnAliasFillFailure | 1 << 10 |
| Active | 1 << 11 |
| RepeatsConditions | 1 << 12 |
| KeepInstance | 1 << 13 |
| WantDormant | 1 << 14 |
| HasDialogueData | 1 << 15 |

These flags mix authored quest configuration with runtime quest state. Do not assume every bit should be copied from one override into another without determining whether it is plugin data, runtime data, or save state.

### Quest type

| ID | Type |
|---:|---|
| 0 | None |
| 1 | Main Quest |
| 2 | Mages Guild |
| 3 | Thieves Guild |
| 4 | Dark Brotherhood |
| 5 | Companions Quest |
| 6 | Miscellaneous |
| 7 | Daedric |
| 8 | Side Quest |
| 9 | Civil War |
| 10 | DLC01 Vampire |
| 11 | DLC02 Dragonborn |

### Quest stage flags

- `StartUpStage = 1 << 1`
- `ShutDownStage = 1 << 2`
- `KeepInstanceDataFromHereOn = 1 << 3`

### Quest objective flags

- `ORWithPrevious = 1 << 0`
- `NoStatsTracking = 1 << 1`

### Quest objective runtime state

| ID | State |
|---:|---|
| 0 | Dormant |
| 1 | Displayed |
| 2 | Completed |
| 3 | Completed + Displayed |
| 4 | Failed |
| 5 | Failed + Displayed |

### Quest target flag

`CompassMarkerIgnoresLocks = 1 << 0`.

A quest target also has its own conditions, alias ID, and teleport path. Objective display state alone does not prove the target reference resolved successfully.

## Story Manager / QuestEvent IDs

| ID | Event | Native signature comment |
|---:|---|---|
| 0 | Kill Actor | KILL |
| 1 | Assault Actor | ASSU |
| 2 | Change Location | CLOC |
| 3 | Script | SCPT |
| 4 | Actor Dialogue | ADIA |
| 5 | Actor Hello | AHEL |
| 6 | Activate Actor | AFAV |
| 7 | Player Add Item | AIPL |
| 8 | Player Remove Item | REMP |
| 9 | Craft Item | CRFT |
| 10 | Pick Lock | LOCK |
| 11 | Infection | INFC |
| 12 | Cure | CURE |
| 13 | New Voice Power | NVPE |
| 14 | Dead Body | DEAD |
| 15 | Skill Increase | SKIL |
| 16 | Increase Level | LEVL |
| 17 | Change Relationship Rank | CHBR |
| 18 | Intimidate NPC | INTM |
| 19 | Bribe NPC | BRIB |
| 20 | Flatter NPC | FLAT |
| 21 | Player Gets Favor | PRFV |
| 22 | Pay Fine | PFIN |
| 23 | Jail | JAIL |
| 24 | Served Time | STIJ |
| 25 | Escape Jail | ESIA |
| 26 | Trespass | TRES |
| 27 | Crime Gold | ADCR |
| 28 | Arrest | ARRT |
| 29 | Cast Magic | CAST |

`QuestEvent::None = -1`.

## Quest save ChangeFlags

Current CommonLib exposes:
- `QuestFlags = 1 << 1`
- `QuestScriptDelay = 1 << 2`
- `QuestAlreadyRun = 1 << 26`
- `QuestInstanceData = 1 << 27`
- `QuestRuntimeData = 1 << 28`
- `QuestObjectives = 1 << 29`
- `QuestScript = 1 << 30`
- `QuestStages = 1 << 31`

These are direct evidence for why an established save can retain quest state that no longer matches a changed plugin default.

## Native quest runtime structures

Current `TESQuest` keeps runtime collections/maps for:
- instance text/data;
- aliases and resolved alias-reference map;
- executed and waiting stages;
- objectives;
- quest and Story Manager conditions;
- branched dialogue/topics;
- scenes;
- text Globals;
- current stage;
- already-run state;
- start event data;
- promoted references.

### Diagnostic consequence

When a quest works on a new game but not an established save, compare:
1. QUST static fields;
2. save Quest ChangeFlags;
3. alias maps;
4. current/executed/waiting stages;
5. objective states;
6. instance data;
7. Story Manager start-event data;
8. attached Papyrus state.

Do not attempt to “fix” an established quest solely by forwarding a winning QUST record.

