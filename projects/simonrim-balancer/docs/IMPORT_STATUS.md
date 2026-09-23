# Import Status — 2026-09-23

## Imported versions

- Adamant 6.0.4
- Hand to Hand 2.0.2
- Blade and Blunt 4.0.3
- Mysticism 2.5.0

## Raw / source inventory

- Source files: 73
- Plugins: 21
- Records: 6,009 (5,988 non-header Forms)
- Subrecords: 81,523
- Original deterministic relations: 11,676
- Effect instances: 3,951
- BSA members: 476
- Papyrus source files: 115
- Papyrus properties: 279
- Config values: 129
- FOMOD options: 20
- Spells: 953
- Magic effects: 1,648
- Perks: 625
- Weapons: 216 total WEAP records
- Enchantments: 269 ENCH records
- Combat styles: 62 CSTY records
- Movement types: 12 MOVT records

## Master-aware resolution / deltas

- Forms resolved: 5,988
- FormID slot-resolution failures: 0
- Relations resolved: 11,676; failures: 0
- Effect references resolved: 3,951; failures: 0
- New local Forms: 3,832
- Overrides: 2,156
- Exact imported-master baselines: 537
- External/unimported baselines: 1,619
- Canonical Forms with multiple imported versions: 567
- Imported override-chain rows: 1,145
- Exact-baseline changed overrides: 484
- Exact-baseline identical forwards: 53
- Typed field deltas currently emitted: 311

## Exact high-value decoders

- MGEF DATA: 1,648 / 1,648 decoded, 0 failures
- CTDA: 8,229 / 8,229 decoded, 0 failures
- Condition functions observed: 84
- MGEF/CTDA semantic relations added: 9,937
- PERK headers: 625 / 625 decoded
- PERK effect entries: 1,006 / 1,006 decoded, 0 failures
  - Entry Point: 875
  - Ability: 121
  - Quest + Stage: 10
- PERK conditions: 4,035 decoded
- PERK semantic relations added: 2,803
- WEAP/DNAM: 216 / 216 decoded, 0 failures
  - 21 descriptive weapon baseline groups
  - 18 observed weapon patterns with sample size >= 3
  - 18 exact imported-baseline weapon field deltas
- ENCH/ENIT: 269 / 269 decoded, 0 failures
  - 870 effect rows
  - 101 effect-level conditions
  - 36 descriptive enchantment baseline groups
  - 27 observed enchantment patterns with sample size >= 3
  - 58 exact imported-baseline enchantment field deltas
- CSTY: 62 / 62 decoded, 0 failures
  - 12 descriptive combat-style groups
  - 7 observed combat-style patterns with sample size >= 3
  - 62 external Skyrim baselines unavailable in current snapshot
- MOVT: 12 / 12 decoded, 0 failures
  - 8 exact movement profiles
  - 2 repeated profiles with sample size >= 3
  - 3 movement observed-pattern rows including the complete-domain INAM sentinel observation
  - 12 external Skyrim baselines unavailable in current snapshot
- Distinct perk entry points observed: 62
- Distinct perk entry functions observed: 9

## Observed-pattern layer

- Spell design profiles: 953
- Spell numeric baseline groups: 294
- Perk entry-point baseline groups: 148
- Spell/perk observed-pattern rows with sample size >= 3: 179
- Weapon observed-pattern rows with sample size >= 3: 18
- Enchantment observed-pattern rows with sample size >= 3: 27
- Combat-style observed-pattern rows with sample size >= 3: 7
- Movement observed-pattern rows: 3
- Combined observed patterns with sample size >= 3: 234
- Approved design rules: **0** (promotion remains review-gated)

## Deterministic decoding implemented

- Bethesda record/group and compressed-record structure
- subrecords including `XXXX` extended sizes
- EDID/FULL/DESC and raw payload preservation
- SPEL/SPIT, EFID/EFIT, GMST, GLOB
- complete MGEF/DATA for current TES5/SSE layout
- complete WEAP/DNAM 100-byte TES5/SSE layout for all supplied weapon records
- WEAP critical data, enchantment charge, equip/enchantment refs, keywords, and sound detection
- ENCH ENIT fields, base/worn references, effect composition, and effect condition counts
- CSTY general/melee/close-range/long-range/flight fields and flags
- MOVT SPED directional/rotational movement fields and INAM thresholds
- CTDA + observed condition function semantics
- PERK headers, effect entries, parameters and condition tabs
- basic WEAP/DATA and ARMO/DATA
- BSA inventory / uncompressed author text extraction
- Papyrus source/property/member inventory
- INI/TOML/JSON key/value extraction
- FOMOD options and normalized module semantics
- master-aware Form identity and imported override chains

## Preserved but not fully semantically decoded yet

Raw bytes remain available for:

- AVIF perk-tree geometry/connections
- VMAD property values/attachments and fragments
- quests/story-manager structures
- additional record-specific structures

Uncertain structures remain raw evidence instead of being promoted into balance facts.
