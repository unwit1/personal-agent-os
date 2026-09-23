# Cursed Tome arc — small batch 04: completed Book and expanded curse set

Continuity: `tes.mod.dealing-with-daedra`

This batch resolves four core implementation records:
- `BOOK 054FD090` — Book of Curses: Completed
- `SPEL 054FD08E` — The Book of Curses
- `MGEF 0550219B` — hidden full-book holding effect
- `PERK 054FD069` — full-book all-curses perk

It also compares the standalone Debilitation tome `BOOK 053349F5`.

## Completed Book chain

Reading **Book of Curses: Completed** teaches `SPEL 054FD08E`, **The Book of Curses**.

That spell applies hidden effect `0550219B`, whose associated perk is `054FD069` (`dealsallcursesperk`).

The full-book perk contains **12 Ability entries**:

1. `0535D2A5` — Curse of Despair
2. `054FD067` — Curse of Rage
3. `054FD063` — Curse of Draining
4. `0535D2A0` — Curse of Agony
5. `0535D2A1` — Curse of Binding
6. `054FD05F` — Curse of Vulnerability
7. `054FD05E` — Curse of Unlife
8. `054FD061` — Curse of Exhaustion
9. `0535D2A3` — Curse of Petrification
10. `054FD075` — Curse of Mortality
11. `0535D2A7` — Curse of Debilitation
12. `054FD065` — Curse of Obedience

## Six page curses vs expanded full-book curses

The six physically scattered pages grant:
- Agony
- Despair
- Vulnerability
- Binding
- Petrification
- Unlife

The completed Book adds six more:
- Rage
- Draining
- Exhaustion
- Mortality
- Debilitation
- Obedience

This explains why **Debilitation** appears in the BOOK catalog but not among the six placed page activators.

## Standalone Debilitation tome

`BOOK 053349F5`, **Book of Curses: Debilitation**, has BOOK data configured to teach `SPEL 0535D2A7`, **Curse of Debilitation**, directly.

It is therefore a separate spell tome representing one curse from the expanded full-book repertoire, not the physical Vulnerability page.

## Curse economy

All twelve full-book curse spell descriptions use the same broader design language: the caster pays through Health or Health/Stamina rather than ordinary Magicka, and many warn that casting can kill the caster.

The completed artifact therefore broadens the six-page life-force curse system into a larger curse tradition rather than merely combining the six page effects.
