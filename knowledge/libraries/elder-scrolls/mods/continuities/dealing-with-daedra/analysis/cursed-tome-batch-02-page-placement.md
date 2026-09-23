# Cursed Tome arc — small batch 02: exact page placement

Continuity: `tes.mod.dealing-with-daedra`

This batch resolves only the six physical page activators and their six placed references.

## Exact placement

| Location | Cell | Placed REFR | Page ACTI | Page name |
|---|---|---|---|---|
| Anise's Cabin cellar | `000DDF7C` / `AnisesCabin01` | `055117C7` | `055117BA` | Page of Agony |
| Drelas' Cottage | `000DEBCD` / `DrelasCottage01` | `055117C6` | `055117BB` | Page of Despair |
| Harmugstahl | `0005F536` / `Harmugstahl01` | `055117C8` | `055117BD` | Page of Vulnerability |
| Rannveig's Fast | `00015229` / `RannveigsFast01` | `055117C9` | `055117BE` | Page of Binding |
| Southfringe / Bashnag's base | `00020C32` / `SouthfringeAvalanche` | `055117DD` | `055117BC` | Page of Petrification |
| Ansilvund Burial Chambers | `0001F358` / `Ansilvund02` | `055117CA` | `055117BF` | Page of Unlife |

The ACTI records themselves supply the names through their FULL fields:
- `055117BA` — `dealspageactagony` — Page of Agony
- `055117BB` — `dealspageactdespair` — Page of Despair
- `055117BC` — `dealspageactpetrify` — Page of Petrification
- `055117BD` — `dealspageactvulne` — Page of Vulnerability
- `055117BE` — `dealspageactbindgin` — Page of Binding
- `055117BF` — `dealspageactunlife` — Page of Unlife

## Important correction

The six physical contest pages are **Agony, Despair, Vulnerability, Binding, Petrification, and Unlife**.

A separate BOOK record exists as `053349F5`, **Book of Curses: Debilitation**, but it is not one of these six placed page activators.

The earlier artifact summary that substituted Debilitation for Vulnerability should therefore be treated as incomplete until the Debilitation BOOK/spell relationship is analyzed separately.

## Method

This mapping comes from direct ESP structure:
1. read the six ACTI records and their FULL names;
2. locate REFR records whose NAME field points to those ACTI FormIDs;
3. retain the enclosing Cell-Children GRUP FormID;
4. resolve those cells against the plugin's overridden CELL records.

No page-location assignment in this table is inferred from quest order.
