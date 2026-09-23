# Simonrim Expansion Ingestion — 2026-09-23

This append-only ingestion extends the Simonrim Balancer beyond the original Adamant / Hand to Hand / Blade and Blunt / Mysticism snapshot without rewriting that immutable source snapshot.

## Supplied mods

Adamant - Bard Addon 1.1.0; Aetherius 2.15.1; Apothecary 1.3.9; Apprentice 1.1.0; Arena 1.2.0; Artificer 1.0.11; Candlehearth 1.1.1; Crusader 0.6; Gourmet 1.2.0; Manbeast 2.1.1; Mercantile 1.0.0; Pilgrim 1.3.1; Power Attack Speed Perks 1; Scion 2.2.2; Sorcerer 1.1.0; Starfrost 2.0.0; Stormcrown 1.1.17.

## Raw/source checkpoint

- 17 mods
- 53 plugin source occurrences
- 51 unique plugin binaries by SHA-256
- 9,769 plugin record occurrences
- 289,053 subrecords
- 68 record types
- 0 parser-error files
- 12 BSAs / 898 BSA members
- 239 PSC source occurrences, 202 unique by hash
- 2,046 decoded configuration values
- 55 FOMOD options

The two duplicate plugin occurrences are retained as installer provenance and hash-deduplicated for logical comparisons.

## Semantic completion

**Complete for the supplied expansion archives.**

- all 68 record types have an explicit treatment
- 0 unmapped record types
- 8,988 semantic gameplay records
- 216 typed support/routing records
- 236 keyword identity records
- 276 presentation/navigation inventory records
- 53 plugin headers/provenance records
- 935/935 VMAD payloads decoded with zero failures
- 187 exact supplied parent-plugin comparisons
- 156 deterministic semantic parent comparisons
- 363 repeated observed implementation profiles
- 42 explicit author/FOMOD evidence statements
- 405 review candidates
- 93 first-pass review families
- approved rules: 0

See `EXPANSION_SEMANTIC_ANALYSIS_2026-09-23.md` and the compact checkpoint under `data/ingestions/2026-09-23-simonrim-expansion-01/`.

## Evidence boundary

The remaining work is no longer another parsing pass over these 17 archives. External baseline bodies—primarily Skyrim/Update/DLC/Creation masters—and cross-snapshot candidate consolidation are the next dependencies.

No newly observed behavior is an approved Simonrim rule.
