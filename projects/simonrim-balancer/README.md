# Simonrim Balancer

A provenance-aware Skyrim gameplay design and balance knowledge project.

The project imports the actual implementation of Simonrim mods, separates raw evidence from interpretation, learns version-scoped design patterns, and will use reviewed rules to analyze or design features for other mods. It is intentionally not a single balance score.

## Current snapshot — 2026-09-23

| Mod | Version |
| --- | --- |
| Adamant | 6.0.4 |
| Hand to Hand | 2.0.2 |
| Blade and Blunt | 4.0.3 |
| Mysticism | 2.5.0 |

Current evidence includes 21 plugins, 6,009 records, 81,523 subrecords, 11,676 first-pass relations, 3,951 effect instances, 1,648 fully decoded MGEFs, 8,229 decoded conditions, 625 decoded perks with 1,006 effect entries, Papyrus/config/FOMOD evidence, master-aware override chains, and the first descriptive spell/perk baselines.

No design rules have been auto-approved. The architecture explicitly separates:

raw → decoded → projected → observed_pattern → rule_candidate → approved_rule → exception

## Implemented analysis stages

- lossless plugin/subrecord ingestion
- source/BSA/Papyrus/config/FOMOD inventory
- canonical FormID resolver
- imported-master override/delta engine
- exact MGEF DATA decoder
- exact CTDA decoder
- exact PERK effect-entry decoder
- semantic FormID relationships
- module/reversion/compatibility semantics
- spell design profiles and numeric baselines
- perk entry-point baselines

See docs/ARCHITECTURE.md, docs/RESOLUTION_AND_DELTAS.md, docs/SCHEMA_PROVENANCE.md, docs/OBSERVED_PATTERNS.md, docs/IMPORT_STATUS.md, and docs/NEXT_STEPS.md.

## Core design principle

Every recommendation should remain traceable to a mod/version and concrete plugin/Form/script/config/installer evidence, distinguish direct evidence from observed patterns and approved rules, preserve counterexamples/exceptions, and state its intended scope.

## Repository role

This project is staged as a self-contained folder inside the private Personal Agent OS repository. The folder is intentionally portable so it can later become a dedicated simonrim-balancer repository without changing its internal model.
