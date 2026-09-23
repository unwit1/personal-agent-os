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

## Weapon grammar

All 216 supplied WEAP records now have the TES5/SSE 100-byte DNAM structure decoded with zero failures. The review layer exposes animation type, governing skill, base damage, speed, reach, stagger, range, weapon flags, critical data, enchantment/equip references, keywords, and sound-detection level.

The decoder emits 21 plugin/animation/skill numeric groups, of which 18 have at least three examples. These are descriptive observations, not approved rules. The simple_damage_speed_product field is explicitly a comparison metric, not true in-game DPS.

Exact imported-master comparison currently exposes 18 weapon field deltas. Adamant repeatedly adds Update.esm:ADA117 to Mysticism-derived bound weapons, and two imported Mysticism two-handed bound-weapon records increase stagger from about 1.10 to 1.15. These remain implementation facts until reviewed as rule candidates.


## Enchantment grammar

All 269 supplied ENCH records now have the documented TES5/SSE 36-byte ENIT structure decoded with zero failures. The review layer exposes enchantment cost, enchantment amount, manual-calculation and duration-extension flags, cast/delivery/enchantment type, charge time, base enchantment and worn-restriction references, effect composition, and effect-level conditions.

The decoder emits 36 descriptive numeric/structural groups; 27 have at least three examples. These are observations, not approved rules.

Exact imported-master comparison exposes 58 enchantment field changes, all in Adamant overrides of imported Skyrim/Dragonborn/Mysticism records: 55 change effect count and 3 change bound-weapon enchantment flags from ManualCalc to ManualCalc + ExtendDurationOnRecast. Effect-count changes are implementation evidence and require effect/condition-level review before any generalization.

An estimated auto-calc cost is retained only as a diagnostic from the documented MagicItem formula. It is not a normative balance metric because stored values, manual-calculation flags, zero-cost helper effects, rounding, and runtime semantics create material residuals in this snapshot.
