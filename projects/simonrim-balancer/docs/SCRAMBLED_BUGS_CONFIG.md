# Adamant Scrambled Bugs Configuration — 2026-09-23

The exhaustion audit found one loose runtime config that was present in the source inventory but absent from the first behavioral-config table: `module scrambled/SKSE/Plugins/ScrambledBugs.json`.

The file contains C-style comments, so it is decoded by stripping comments and parsing the resulting JSON while preserving the original source text and SHA-256 separately.

## Results

- Leaf configuration entries: 40
- Boolean entries enabled: 32
- Boolean entries disabled: 7
- Numeric entries: 1
- `fixes.quickShotPlaybackSpeed = 2.0`

Notable enabled patches/fixes include:
- actor-value percentage calculation
- enchantment cost persistence
- kill-camera perk-entry-point correction
- left-hand power-attack stamina calculation
- magic-effect flag scaling
- Quick Shot handling
- training-menu cost correction
- weapon charge handling
- perk-entry-point multiple-spell application and source/target casting
- accumulating-magnitude behavior
- multiple-enchantment-effect improvement
- leveled-character correction
- lockpicking/scroll/staff experience
- poison resistance
- power-attack stamina requirements
- reflect damage

Explicitly disabled options include commanded-actor/team-mate difficulty multiplier inheritance, restrictive soul-gem patches, already-caught pickpocketing, automatic best-ammunition equip, and steep-slope movement.

These are package runtime dependencies/configuration choices. They are **not** automatically promoted into Simonrim design rules.

After this correction the behavioral configuration channel contains 169 decoded entries across 9 non-FOMOD configuration files. Installer XML remains modeled separately through the FOMOD option inventory.
