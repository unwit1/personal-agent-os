# Simonrim Balancer

A provenance-aware Skyrim gameplay design and balance knowledge project.

The project imports the actual implementation of Simonrim mods, separates raw evidence from interpretation, learns version-scoped design patterns, and will use reviewed rules to analyze or design features for other mods. It is intentionally not a single balance score.

## Current evidence — 2026-09-23

The project now has two provenance-preserving ingestion slices.

### Core slice
Adamant 6.0.4, Hand to Hand 2.0.2, Blade and Blunt 4.0.3 and Mysticism 2.5.0.

### Expansion slice
Adamant Bard Addon 1.1.0, Aetherius 2.15.1, Apothecary 1.3.9, Apprentice 1.1.0, Arena 1.2.0, Artificer 1.0.11, Candlehearth 1.1.1, Crusader 0.6, Gourmet 1.2.0, Manbeast 2.1.1, Mercantile 1.0.0, Pilgrim 1.3.1, Power Attack Speed Perks 1, Scion 2.2.2, Sorcerer 1.1.0, Starfrost 2.0.0 and Stormcrown 1.1.17.

Across both slices there are 15,778 plugin record occurrences. The expansion alone adds 9,769 records, 289,053 subrecords, 239 PSC source occurrences, 2,046 decoded config values, 55 installer options and complete explicit treatment for all 68 record types encountered.

Expansion behavioral coverage includes 935/935 VMAD payloads, 1,121 script attachments, 3,953 typed properties, 386 fragments and 83 quest aliases with zero VMAD failures.

No design rules have been auto-approved. The architecture explicitly separates:

raw → decoded → projected → observed_pattern → rule_candidate → review_family → approved_rule → exception

## Implemented analysis stages

- lossless plugin/subrecord ingestion
- source/BSA/Papyrus/config/FOMOD inventory
- canonical FormID resolver
- imported-master override/delta engine
- exact magic/spell/perk/equipment/item decoders
- encounter-zone, race, crafting/distribution and delivery decoders
- VMAD script/property/fragment/alias decoding
- quest/dialogue/world-placement support
- semantic Form relationships
- module/reversion/compatibility semantics
- observed-pattern generation
- candidate and review-family synthesis

See `docs/PROJECT_STATE_2026-09-23.md`, `docs/EXPANSION_INGESTION_2026-09-23.md`, `docs/EXPANSION_SEMANTIC_ANALYSIS_2026-09-23.md`, and `docs/NEXT_STEPS.md`.

## Core design principle

Every recommendation should remain traceable to a mod/version and concrete plugin/Form/script/config/installer evidence, distinguish direct evidence from observed patterns and approved rules, preserve counterexamples/exceptions, and state its intended scope.

## Repository role

This project is staged as a self-contained folder inside the private Personal Agent OS repository. The folder is intentionally portable so it can later become a dedicated simonrim-balancer repository without changing its internal model.
