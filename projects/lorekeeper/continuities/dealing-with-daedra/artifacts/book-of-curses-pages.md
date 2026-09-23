# Book of Curses — physical pages

Continuity: tes.mod.dealing-with-daedra
Primary arc: Vampire Master / Book of Curses
Dialogue manager: QUST 0550C6B0

The six collectible curse pages are implemented as named ACTI records rather than ordinary readable BOOK records. Their actual placed REFR records allow the page-to-location mapping to be recovered deterministically from the ESP.

| Page | ACTI | Placed REFR | Verified cell |
|---|---|---|---|
| Page of Agony | 055117BA `dealspageactagony` | 055117C7 | Anise's Cellar (000DDF7C / AnisesCabin01) |
| Page of Despair | 055117BB `dealspageactdespair` | 055117C6 | Drelas' Cottage (000DEBCD / DrelasCottage01) |
| Page of Vulnerability | 055117BD `dealspageactvulne` | 055117C8 | Harmugstahl (0005F536 / Harmugstahl01) |
| Page of Binding | 055117BE `dealspageactbindgin` | 055117C9 | Rannveig's Fast (00015229 / RannveigsFast01) |
| Page of Petrification | 055117BC `dealspageactpetrify` | 055117DD | Southfringe Sanctum/Avalanche cell (00020C32 / SouthfringeAvalanche), Bashnag's base |
| Page of Unlife | 055117BF `dealspageactunlife` | 055117CA | Ansilvund Burial Chambers (0001F358 / Ansilvund02) |

This corrects an ambiguity that cannot be solved from dialogue order alone: the Master often says only "the next page" rather than naming the curse. The placement records establish the exact identity.

## Collection route

The Master's dialogue sends the player through the same physical chain:
- first to Anise southwest of Riverwood (INFO 0553A0F6);
- then Drelas northwest of Whiterun (05534FCE);
- then Harmugstahl north of Karthwasten (0553A0D5);
- then Rannveig's Fast west of Drelas' cottage (0553A0D6);
- then Bashnag's mountain base south-southeast of Helgen (0553A0D7);
- finally Ansilvund northeast of Shor's Stone (0553A0D8).

The Master says he was selected as a participant in the Book of Curses game and received the book's spine rather than a page. He locates the other pieces by scrying on paper remnants attached to the spine (0553A0D2).

## Related spell-tome records

Separate BOOK records exist for several curse teachings:
- 0532F8CB — Book of Curses: Agony;
- 053349FA — Book of Curses: Despair;
- 053349F5 — Book of Curses: Debilitation;
- 0532F8D0 — Book of Curses: Binding;
- 053349D9 — Book of Curses: Petrification;
- 054FD090 — Book of Curses: Completed.

Do not confuse these BOOK records with the six physical page activators above. The page placement layer is the authoritative source for which curse-page is found at which site.

## Narrative significance

The page distribution deliberately crosses unrelated vanilla and modded occult sites. The game-master Dremora has therefore turned multiple independent dangerous actors into competing custodians/participants in one artifact contest rather than creating a single dungeon devoted to the book.
