# Non-dialogue scene action record

Normalized representation for non-dialogue actions extracted directly from Skyrim `SCEN` records in `Glenmoril.esm`.

## Source binding

The completeness manifest records the source plugin and SHA-256 for the corpus. The exact imported source is:

- plugin: `Glenmoril.esm`
- SHA-256: `5669018c81acf13147ff489f486963ecc3c57515a73ed9afd210c7ede85e1cc8`

## Common columns

- `scene_source_id`
- `scene_editor_id`
- `quest_source_id`
- `quest_editor_id`
- `action_index`
- `actor_alias_id`
- `actor_alias_name`
- `start_phase`
- `end_phase`
- `flags`

Package actions additionally preserve:
- `package_source_id`
- `package_editor_id`
- `package_record_type`

Timer actions additionally preserve:
- `timer_seconds`

## Resolution rules

The owning quest is the trailing scene `PNAM`. The action `ALID` is resolved against that quest's QUST alias table (`ALST`/`ALLS` + `ALID`). Package-action `PNAM` values are retained as exact FormID-derived source IDs and joined to local `PACK` records when the target is defined in GLENMORIL.

`SNAM` is context-sensitive in SCEN actions: the first pre-`ENAM` value is the start phase, while a type-2 timer action may contain a second post-`ENAM` `SNAM` interpreted as a float duration in seconds.

The CSV columns are the exact decoded structural fields required by the previous checkpoint. They are structural evidence, not plot interpretation. Do not promote chronology solely from a package name or timer; combine action ordering with package targets, scripts, scene phases, and corroborating text.