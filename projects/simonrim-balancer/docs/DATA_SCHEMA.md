# Data Snapshot Schema

The data/snapshots/<date>/ directory represents immutable evidence for a specific set of mod versions.

Expected snapshot files:

| File | Purpose |
| --- | --- |
| snapshot_manifest.json | versions, counts, scope |
| mods.csv | one row per ingested mod/version |
| source_files.csv | package file inventory |
| plugins.csv | plugin metadata, masters, record counts |
| record_type_counts.csv | counts by plugin/type |
| records.csv | one row per Bethesda record |
| subrecords.csv | one row per subrecord |
| records_full.jsonl | raw subrecord payloads encoded as base64 |
| relations.csv | deterministic FormID edges |
| spells.csv | normalized spell projection |
| effects.csv | spell/scroll/enchantment effect instances |
| magic_effects.csv | magic-effect projection |
| perks.csv | perk projection |
| settings.csv | GMST/GLOB values |
| weapons.csv | basic weapon projection |
| armor.csv | basic armor projection |
| bsa_inventory.csv | BSA member inventory |
| scripts.csv | Papyrus script inventory |
| script_properties.csv | Papyrus properties |
| script_members.csv | Papyrus events/functions |
| configs.csv | parsed INI/TOML/JSON values |
| fomod_options.csv | installer choices and file mappings |
| text_sources_*.jsonl | extracted author-supplied text evidence |

## Stable identifiers

Until master-aware FormID resolution is implemented, use the compound key:

snapshot / plugin / FormID

Do not assume a raw FormID is globally unique across plugins.

## Provenance rule

Every derived mechanic or future rule must retain enough information to trace back to at least one of:
- plugin + FormID + subrecord
- source artifact path + hash
- script path + hash
- config path + key
- installer option
