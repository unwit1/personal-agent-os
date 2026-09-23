# Observed Patterns — Initial Pass

These are descriptive observations, not approved Simonrim design rules.

The generated observed-pattern table only promotes groups with at least three samples into the compact review list, and every row remains status=observed_pattern with approved_rule=false.

## Perk grammar

Across the supplied files there are 1,006 decoded perk effects:

- 875 entry-point effects
- 121 ability effects
- 10 quest/stage effects
- 62 distinct entry points
- 9 entry functions

Adamant.esp alone contains 653 decoded perk effects. Frequent entry-point uses include spell magnitude, incoming spell magnitude, combat-hit spell application, spell duration, and spell cost. The source tables retain parameter ranges, condition counts, priorities, and exact samples rather than normalizing away outliers.

## Magic / spell profiles

The current pass produces 953 spell profiles and 294 descriptive numeric groups, grouped by source plugin, magic skill, minimum skill level, casting type, delivery, and primary-effect archetype.

MysticismMagic.esp contributes 451 spell profiles. Its primary-effect minimum-skill values prominently use 0/25/50/75/100 bands. Separately, the author-provided Slower Spell Unlocks installer text states vendor unlock thresholds of 25/50/75 and the master quest at 90. These are different concepts and must not be conflated.

## Conditions as feature grammar

Adamant perk behavior heavily depends on conditions such as HasPerk, EPMagic_SpellHasKeyword, GetBaseActorValue, HasKeyword, equipped-item type, and magic-skill checks. Equivalent gating and anti-stacking logic therefore belongs to a feature's design evidence, not merely its visible description or multiplier.

## Promotion policy

Before an observed pattern can become a rule candidate, check whether samples represent one mechanic, whether identical forwards or compatibility/reversion modules polluted the sample, whether scripts/configs add hidden behavior, whether named exceptions exist, and whether the pattern persists across versions.
