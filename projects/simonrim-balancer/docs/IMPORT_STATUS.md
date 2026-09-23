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
- Weapons: 216
- Enchantments: 269
- Combat styles: 62
- Movement types: 12
- Actor-value / perk-tree records: 25

## Master-aware resolution / deltas

- Forms resolved: 5,988; FormID slot-resolution failures: 0
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

- MGEF DATA: 1,648 / 1,648, 0 failures
- CTDA: 8,229 / 8,229, 0 failures
- PERK headers: 625 / 625; 1,006 effect entries; 4,035 perk conditions
- WEAP: 216 / 216, 21 baseline groups, 18 observed patterns, 18 exact imported-baseline deltas
- ENCH: 269 / 269, 870 effects, 36 baseline groups, 27 observed patterns, 58 exact imported-baseline deltas
- CSTY: 62 / 62, 12 descriptive groups, 7 observed patterns, 62 external Skyrim baselines
- MOVT: 12 / 12, 8 exact movement profiles, 3 observed movement patterns, 12 external Skyrim baselines
- AVIF: 25 / 25, 297 perk-tree nodes, 283 graphical tree edges, 0 missing targets, 0 unreachable nodes, 0 cycles
  - 7 exact imported Adamant baselines for add-on graph deltas
  - all 7 exact-baseline add-ons add nodes and change edges; 4 also remove nodes
  - 18 external Skyrim baselines unavailable in the current snapshot

## Observed-pattern layer

- Spell profiles: 953; spell numeric baseline groups: 294
- Perk entry-point baseline groups: 148
- Spell/perk observed-pattern rows: 179
- Weapon observed-pattern rows: 18
- Enchantment observed-pattern rows: 27
- Combat-style observed-pattern rows: 7
- Movement observed-pattern rows: 3
- Combined observed patterns: 234
- Approved design rules: 0

## Important semantic guardrail

AVIF tree connections are graphical/UI topology, not perk prerequisites. Actual perk gating remains in PERK CTDA conditions. The balancer stores those systems separately and will overlay them later rather than treating a tree line as a gameplay requirement.

## Preserved but not fully semantically decoded yet

- VMAD property values/attachments and fragments
- quests/story-manager structures
- additional record-specific structures

Uncertain structures remain raw evidence instead of being promoted into balance facts.
