# Scene dialogue action record

Normalized representation for a dialogue action extracted from a Skyrim `SCEN` record.

## Fields

- source_plugin
- scene_source_id
- scene_editor_id
- quest_source_id
- action_index
- action_type
- actor_alias_id
- linked_dial_source_id
- start_phase
- end_phase
- flags
- raw_subrecord_evidence
- resolution_status

## Join path

`SCEN dialogue action → actor_alias_id → QUST alias → reference/NPC`

and independently:

`SCEN dialogue action → linked_dial_source_id → DIAL → child INFO records`

The resulting INFO records must still be filtered by their own conditions. Existing Skyrim dialogue-import tooling explicitly documents this behavior. citeturn0search5

## Important ordering rule

Do not reorder INFO records casually. xEdit documents that effective INFO order inside a DIAL matters to game selection behavior and can depend on PNAM chains and file ordering. citeturn0search2
