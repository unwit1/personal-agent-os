# Normalized dialogue row

Canonical row emitted by the GLENMORIL dialogue resolver.

```yaml
source_plugin: Glenmoril.esm
quest_source_id:
scene_source_id:
scene_editor_id:
scene_action_index:
actor_alias_id:
actor_alias_name:
dial_source_id:
dial_editor_id:
info_source_id:
info_order:
previous_info_source_id:
prompt:
response_number:
response_text:
conditions: []
speaker_candidates: []
speaker_source_id:
resolution_method:
confidence:
```

## Rules

- `speaker_source_id` is populated only when one speaker is structurally resolved.
- Multiple valid speakers remain in `speaker_candidates`.
- INFO conditions and their order are retained.
- RNAM is preserved as `prompt`.
- PNAM is normalized as `previous_info_source_id`.
- multiple responses in one INFO produce separate response rows while retaining the same INFO source ID.

This row format is canonical; character prose pages are derived views.
