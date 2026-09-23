# Cursed Tome arc — small batch 03: page activation mechanics

Continuity: `tes.mod.dealing-with-daedra`

This batch follows only the six physical page activators and the hidden holding perks they apply.

## Common activator script

All six physical page ACTI records use:

`dealsgenericactivatorspellplusmessage`

On activation the script:
1. casts its configured `TempleBlessing` spell on the activator;
2. shows a common page-removal message.

Each page's configured spell has two effects:
- advance the vampire/Book-of-Curses quest;
- apply a page-specific hidden "holding page" effect.

## Page → hidden effect → perk → curse

| Page ACTI | Page | Holding MGEF / perk | Curse spell granted |
|---|---|---|---|
| `055117BA` | Agony | `054FD093` -> perk `054FD06C` | `0535D2A0` Curse of Agony |
| `055117BB` | Despair | `054FD092` -> perk `054FD06B` | `0535D2A5` Curse of Despair |
| `055117BD` | Vulnerability | `054FD094` -> perk `054FD06D` | `054FD05F` Curse of Vulnerability |
| `055117BE` | Binding | `054FD097` -> perk `054FD06F` | `0535D2A1` Curse of Binding |
| `055117BC` | Petrification | `054FD096` -> perk `054FD06E` | `0535D2A3` Curse of Petrification |
| `055117BF` | Unlife | `055117B6` -> perk `055117B5` | all six physical-page curses |

## Why the sixth page is special

The Unlife page does not apply the standalone `dealsunlifecursesperk` (`054FD070`).

Instead its hidden effect applies `deals6cursesperk` (`055117B5`), whose six Ability entries are:

- Curse of Vulnerability — `054FD05F`
- Curse of Binding — `0535D2A1`
- Curse of Agony — `0535D2A0`
- Curse of Despair — `0535D2A5`
- Curse of Unlife — `054FD05E`
- Curse of Petrification — `0535D2A3`

This mechanically confirms the physical contest's six-curses set.

## Debilitation correction strengthened

`Curse of Debilitation` (`0535D2A7`) is absent from the six-page perk.

Therefore Debilitation is not merely a mislabeled Vulnerability page: it belongs to a different/full-book curse layer analyzed separately.

## Evidence quality

This is direct implementation evidence from ACTI VMAD properties, SPEL effect lists, MGEF associated-perk fields, and PERK Ability entries.
