# Data Snapshot Files

The data/snapshots/<date>/ directory contains immutable raw evidence plus reproducible derived projections for a specific set of mod versions.

## Key layers

### Raw / first pass
- snapshot_manifest.json — versions, counts, scope
- mods.csv / source_files.csv / plugins.csv / record_type_counts.csv
- records.csv / subrecords.csv / records_full.jsonl
- relations.csv
- spells.csv / effects.csv / magic_effects.csv / perks.csv
- settings.csv / weapons.csv / armor.csv
- bsa_inventory.csv
- scripts.csv / script_properties.csv / script_members.csv
- configs.csv / fomod_options.csv / text_sources_*.jsonl

### Resolution / delta
- resolved_forms.csv — canonical origin/object identity and baseline status
- resolved_relations.csv — canonical relation targets
- resolved_effects.csv — canonical MGEF targets
- override_chains.csv — multiple imported versions of a Form
- override_deltas.csv — exact raw subrecord deltas
- override_field_deltas.csv — typed field differences
- resolution_summary.json

### Exact semantic decoding
- magic_effects_full.csv
- conditions.csv
- semantic_relations.csv
- high_value_decoder_summary.json
- perks_full.csv
- perk_effects.csv
- perk_conditions.csv
- perk_semantic_relations.csv
- perk_decoder_summary.json

### Intent / module evidence
- module_semantics.csv
- explicit_design_evidence.csv

### Observed patterns
- spell_profiles.csv
- spell_numeric_baselines.csv
- perk_entry_point_baselines.csv
- condition_function_summary.csv
- semantic_relation_summary.csv
- observed_patterns.csv
- design_profile_summary.json

## Stable identifiers

Canonical Form identity is:

<origin plugin>:<lower 24-bit object id>

A precise source occurrence remains:

<snapshot>/<source plugin>/<raw FormID>

The canonical key identifies the logical Form; the source occurrence identifies one concrete implementation/version.

Every derived mechanic or future rule must remain traceable to plugin/Form/subrecord, source artifact hash/path, script/config evidence, or installer evidence. Statistical summaries never replace their sample rows.
