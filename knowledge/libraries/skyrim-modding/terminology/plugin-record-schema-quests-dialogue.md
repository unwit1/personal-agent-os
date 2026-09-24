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
