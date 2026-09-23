# Distribution / Crafting / Item Decoder — 2026-09-23

This checkpoint models the gameplay-distribution layer of Adamant 6.0.4, Hand to Hand 2.0.2, Blade and Blunt 4.0.3, and Mysticism 2.5.0.

## Deterministic coverage

- LVLI: 389 leveled lists, 2,791 entries.
- COBJ: 181 crafting recipes, 383 input rows.
- SCRL: 305 scrolls, 744 effect instances.
- BOOK: 303 books; all 303 are spell tomes in this supplied corpus.
- FLST: 36 form lists, 590 members.
- DUAL: 26 dual-cast data records.
- Decode failures: 0.

## Exact imported-baseline comparisons

81 records have an exact prior imported Simonrim baseline:
- 23 LVLI
- 55 SCRL
- 3 FLST

73 are semantically modified and 8 are identical forwards.

### LVLI

All 23 exact-baseline LVLI records are materially changed.

- MysticismJumpSpells adds four optional spell/scroll entries to Mysticism lists.
- MysticismSurvivalSpells adds four optional spell/scroll entries.
- MysticismSlowerUnlocks changes fifteen spell-tome/scroll/staff lists from unconditional availability to a 100% chance-none value controlled by school-specific Globals. The existing entries are preserved.

This is implementation evidence about optional-module distribution; it is not automatically a universal Simonrim distribution rule.

### FLST

All three exact-baseline Hand to Hand form-list overrides are materially changed:
- Alteration list: +2 members.
- Lockpicking list: +12 / -10 members.
- Pickpocket list: +7 / -3 members.

These lists track the skill/perk-tree remapping performed by Hand to Hand and should be analyzed together with the AVIF graph and PERK condition evidence.

### SCRL

47 of 55 exact Adamant-vs-Mysticism scroll overrides are materially changed; 8 are identical forwards.

Across the 47 modified scrolls:
- 107 effect tuples are added.
- 32 effect tuples are removed.
- 84 effect conditions are added.
- 49 effect conditions are removed.
- Some scroll headers also change spell cost or spell flags.

The semantic delta compares effect identity + magnitude + area + duration and normalized CTDA conditions, while raw source bytes remain the authoritative evidence.

## Guardrails

- Leveled-list order, FormList order, effect order, and semantic membership are all preserved separately.
- Recipe CTDA conditions remain first-class evidence.
- A distribution record being overridden does not by itself imply authorial balance intent; optional modules and compatibility layers are classified separately.
- No observation in this checkpoint is an approved design rule.
