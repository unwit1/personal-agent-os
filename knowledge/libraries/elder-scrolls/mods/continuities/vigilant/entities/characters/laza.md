# Laza

- Continuity: `tes.mod.vigilant`
- Role: Coldharbour/Alessian-era figure associated with dragon hunting and the Owl tradition
- Main-quest linkage: bound as **Laza of Order** in `QUST 0212F24E` / **Coldharbour**
- Dedicated source book: `BOOK 020DB22F` / **Laza**
- Owl-cycle books:
  - `BOOK 021E7B13` — **Laza and the White Owl**
  - `BOOK 021E7B14` — **Laza and the Gray Owl**
  - `BOOK 021E7B15` — **Laza and the Black Owl**

## Structural role

The Coldharbour main-quest reconstruction identifies **Laza of Order** as one of the named aliases bound into VIGILANT's principal Coldharbour quest, alongside Inquisitor Pepe, Menta Na, Abbot Cosmas, and a Marukh form. This establishes Laza as part of the implemented main-quest cast rather than only a name preserved in books.

The current repository extraction does not yet preserve Laza's NPC FormID or a complete direct-dialogue dossier, so those identifiers should remain open rather than inferred.

## Jhunal's testimony

**Jhunal the Owl** directly says that he used Laza as a shepherd to harvest dragons. Jhunal characterizes Laza as simple and obedient and places him inside Jhunal's own attempt to acquire dragon souls and ultimately become a dragon.

This is strong first-person evidence for a Jhunal–Laza relationship, but it remains Jhunal's testimony. It does not by itself establish every detail of the separate Owl-cycle texts.

## The Laza book cluster

VIGILANT implements at least four explicitly Laza-named books:

1. **Laza** (`020DB22F`)
2. **Laza and the White Owl** (`021E7B13`)
3. **Laza and the Gray Owl** (`021E7B14`)
4. **Laza and the Black Owl** (`021E7B15`)

Their physical distribution is substantial rather than unique-item placement.

**Laza** is placed in:
- Abandoned House (`020B54AA`)
- Narfin's Inquisition Court (`020DD5ED`)
- Bourlor's House (`020B0F6B`)
- Pond House (`0216E303`)
- Temple of Stendarr (`02025091`)

All three Owl-cycle books are placed in the same four locations:
- Underground Lake (`020C09BA`)
- Slums Second Floor (`020EE812`)
- Pond House (`0216E303`)
- Martha's House (`020B1BDB`)

That repeated distribution makes the Laza/Owl material a deliberately circulated textual motif inside Coldharbour.

## The Owl problem

The current evidence supports a strong relationship between Laza and an **Owl** figure or tradition. Jhunal is himself explicitly named **Jhunal the Owl**, and he admits exploiting Laza for dragon hunting.

However, Lorekeeper should not automatically identify the **White Owl**, **Gray Owl**, and **Black Owl** of the three book titles with Jhunal, with one another, or with any single fixed entity until the exact texts and any relevant dialogue/scene evidence are persisted and compared.

Current classification:

**ESM layer:** high-confidence Laza ↔ Owl manipulation/dragon-hunting cluster; color-coded identities are not directly resolved by the currently persisted plugin extraction.

**Supplementary layer:** a123999 identifies Jhunal the Owl with the Gray Owl and provides lower-provenance comment-thread identifications for the White and Black Owls.

## Supplementary background layer

The supplementary VIGILANT background article by **a123999** adds two important claims:

- **Laza is the sole survivor of the incident in which the nomads were slain by Lamae.**
- **Jhunal the Owl is the Gray Owl** and deceived Laza into attacking Kyne's Garden and catching dragons.

Source:
- `sources/supplementary/a123999-vigilant-backgrounds.md`

This upgrades the Gray Owl identity at the supplementary-commentary layer while preserving the ESM-only uncertainty.

The same article's later comment thread gives lower-provenance Owl identifications:
- Black Owl = Orlando the Knowledgeable / a tentacle of Hermaeus Mora;
- White Owl = a familiar of Julianos;
- Gray Egg = the Gray Owl.

Because those statements occur in comments rather than the article body, Lorekeeper should store them as **supplementary commentary**, not as direct plugin fact, until exact Laza/Owl book texts or stronger records are recovered.

## Source-state warning

The repository currently preserves the four Laza BOOK records' titles and physical placements, plus Jhunal's direct testimony and Laza's Coldharbour quest-role linkage. The exact prose of the four Laza books has not yet been persisted into the browsable `books/` corpus.

Accordingly, this dossier records only claims supported by the currently preserved structural evidence. A later exact-text pass should expand the chronology, speaker roles, color symbolism, and any contradictions among the four texts.

## Canon boundary

Laza's relationship to Jhunal, the color-coded Owl cycle, and the dragon-harvesting narrative are VIGILANT continuity material. They should not be promoted into base Elder Scrolls canon without independent licensed-source corroboration.


## Cross-Vicn Laza/Owl continuation

Later Vicn works provide direct continuation evidence for the color-coded Owl sequence.

### GLENMORIL exact texts

GLENMORIL preserves:
- `The Three Owls`
- `Laza and the Owls`

The latter directly sequences Laza through:
1. White Owl;
2. Gray Owl;
3. Black Owl.

The Gray Owl directs Laza toward **Kyne's Spring**, while the Black Owl instructs him to plunge his dagger into the Spring and frames the resulting corruption/transformation as bringing him closer to those he lost.

These are **GLENMORIL texts**, not recovered copies of the missing VIGILANT books.

### UNSLAAD corroboration

UNSLAAD's **Jhunal the Gray / Gray Owl** directly lists **Laza** among failed experiments.

This independently supports:
- VIGILANT Jhunal's claim that he used Laza;
- the dragon-experiment thread;
- the continuity of Laza as an Owl/Jhunal experimental subject.

### Revised color identity map

Cross-Vicn direct evidence later gives:
- White Owl → **Jhunal the White**
- Gray Owl → **Jhunal the Gray**, with Orlando-family entanglement
- Black Owl → **Jhunal the Black**

These should be treated as strong continuity evidence, not silently substituted for the missing VIGILANT book texts.

Detailed bridge:
- `analysis/vicn-owl-continuity-bridge.md`
