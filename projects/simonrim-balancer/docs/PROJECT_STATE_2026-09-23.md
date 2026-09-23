# Simonrim Balancer — Project State — 2026-09-23

## Source-ingestion state

**Complete for both supplied ingestion slices.**

### Core slice
- Adamant 6.0.4
- Hand to Hand 2.0.2
- Blade and Blunt 4.0.3
- Mysticism 2.5.0
- 6,009 plugin records
- 53 record types
- 0 unmapped record types

### Expansion slice
- Adamant - Bard Addon 1.1.0
- Aetherius 2.15.1
- Apothecary 1.3.9
- Apprentice 1.1.0
- Arena 1.2.0
- Artificer 1.0.11
- Candlehearth 1.1.1
- Crusader 0.6
- Gourmet 1.2.0
- Manbeast 2.1.1
- Mercantile 1.0.0
- Pilgrim 1.3.1
- Power Attack Speed Perks 1
- Scion 2.2.2
- Sorcerer 1.1.0
- Starfrost 2.0.0
- Stormcrown 1.1.17
- 9,769 plugin record occurrences
- 68 record types
- 0 unmapped record types
- 53 plugin source occurrences / 51 unique plugin binaries
- 289,053 subrecords
- 12 BSAs / 898 members
- 239 PSC source occurrences / 202 unique source hashes
- 2,046 decoded configuration values
- 55 FOMOD options

Across the two slices the project now carries **15,778 plugin record occurrences** from 21 named Simonrim/core-addon sources, while retaining slice provenance rather than flattening versions or installer variants.

## Expansion semantic coverage

Every expansion record has an explicit treatment:

- 8,988 semantic gameplay records
- 216 typed support / routing records
- 236 keyword identity records
- 276 presentation / navigation inventory records
- 53 plugin headers / provenance records
- 0 unmapped types

Major typed coverage includes encounter zones, races, ingestibles/ingredients, artifacts/equipment, spells/magic effects, perks, crafting, leveled lists, containers, shouts/words, NPCs, AVIF perk trees, quests/dialogue, factions, world placement, survival/vampire/werewolf behavior, staff/scroll infrastructure and suite integration patches.

Behavior layer:
- 935 / 935 VMAD payloads decoded
- 1,121 script attachments
- 3,953 typed properties
- 386 fragments
- 83 quest aliases
- 690 attachments joined to supplied PSC source
- 0 VMAD failures

Internal expansion delta layer:
- 187 exact supplied parent-plugin comparisons
- 125 raw modifications / 62 raw-identical forwards
- 156 deterministic semantic comparisons
- 99 semantic modifications / 57 semantic-identical forwards
- 342 sibling-override pairs kept separate from parent-child deltas

## Architecture state

Implemented evidence pipeline:

raw source → deterministic decoding → canonical Form resolution → typed relationships → exact deltas where baselines exist → observed patterns → rule candidates → review families

Important separation rules:
- AVIF tree lines are UI topology, not PERK prerequisites; PERK CTDA remains authoritative for gating.
- Strong evidence that a behavior exists is separate from evidence that it generalizes.
- Optional modules, compatibility patches, reversion plugins and alternate variants retain narrow scope.
- Missing external baselines reduce generalizability instead of being guessed.
- Presentation/navigation data cannot independently create balance rules.
- Empty/placeholder implementation records are preserved rather than counted as decoder failures.

## Candidate layer

Core slice:
- 273 review candidates
- 149 first-pass review families

Expansion slice:
- 405 review candidates
- 363 repeated implementation profiles
- 42 non-boilerplate author/FOMOD statements
- 93 first-pass review families
- 52 multi-candidate families
- 32 cross-mod families

Current source-scoped review inventory: **678 candidates**.

The core and expansion family indexes are intentionally not simply added together as a canonical suite-wide family count. Cross-snapshot consolidation remains a separate deduplication/synthesis pass.

**Approved rules: 0.**

## Remaining evidence boundaries

These are now evidence dependencies, not unfinished parsing of the supplied archives:

- The original core slice still has 1,619 overrides whose Skyrim/DLC baselines were not supplied.
- The expansion slice has 3,409 records whose canonical origin is outside the expansion slice. Most point to Skyrim/Update/DLC/Creation masters; a small number point to other compatibility targets.
- Native DLL/PDB behavior not shipped as source remains inventory-only unless separately reverse engineered.
- Binary presentation/runtime assets are retained as provenance rather than converted into design laws.

## Next dependency

The highest-value next ingestion is matching Skyrim.esm, Update.esm, Dawnguard.esm, HearthFires.esm, Dragonborn.esm and required Creation master record bodies. That will allow exact vanilla/DLC → Simonrim deltas across both slices.

After baseline expansion:
1. recompute exact vanilla/DLC/Creation → Simonrim deltas;
2. consolidate the 273 core and 405 expansion candidates into a single deduplicated suite review graph;
3. attach exceptions/counterexamples and compatibility-scope evidence;
4. promote only narrowly scoped, human-reviewed rules;
5. expose selective MCP/API queries;
6. test the system against external target mods.
