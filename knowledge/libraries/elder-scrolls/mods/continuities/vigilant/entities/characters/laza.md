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

## Exact VIGILANT book texts recovered

The user-supplied VIGILANT 1.8.2 ESM now provides the exact prose of all four Laza books:

- `books/020DB22F-laza.txt`
- `books/021E7B13-laza-and-the-white-owl.txt`
- `books/021E7B14-laza-and-the-gray-owl.txt`
- `books/021E7B15-laza-and-the-black-owl.txt`

This resolves the previous exact-text gap.

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


## Laza as a name / mantle

The exact `BOOK 020DB22F` text begins:

> Take on the name of Laza and become an immortal hunter.

It then instructs the reader to:
- chase the Stone;
- hunt the souls of those burned by the Stone;
- crush the Stone;
- bring peace to captive souls and the Old Forest.

This is strong direct evidence that **Laza can function as an assumed name, role, or mantle**, not only as one ordinary personal name.

That matters because Kahkaankrein, when asked about Laza, says:

> They were mortal children who served Kyne with us.

and describes them herding sheep outside Kyne's garden.

Current ontology should therefore distinguish:
1. **the original/surviving Laza figure** in the Blood Matron/Owl story;
2. **the name/mantle “Laza”** that can be taken on;
3. possible plural Laza-associated shepherd/hunter bearers.

Do not force all occurrences into one body.

## Exact White Owl text

The White Owl tells the weeping Laza:
- a shepherd can become a wolf by laying down the staff;
- a wolf can become the wind by abandoning its fangs;
- the wind can reach those Laza lost;
- but becoming the **wind of Order** causes the fangs to return and makes the traveler a wolf again.

This directly links:
- shepherd identity;
- wolf transformation;
- wind/Order;
- grief for lost people.

## Exact Gray Owl text

The Gray Owl meets Laza at the edge of the **Old Forest**.

It tells Laza to:
- blind the right eye, thereby blinding the eyes of the sky;
- blind the left eye, thereby blinding the eyes of the forest;
- blind both eyes so no one can catch Laza, at the price that Laza can catch no one;
- avoid the smell of blood;
- follow the Owl's call;
- reach the bottom of the **fountain of Kyne**.

This gives direct VIGILANT text for the Gray Owl route.

## Exact Black Owl text

The Black Owl meets Laza at the **fountain of Kyne** after Laza has bloody eye sockets.

It tells Laza to:
- plunge a dagger into the fountain;
- wash away the Nedic maiden's blood;
- lose the shepherd's staff;
- grow fangs;
- taint the fountain;
- remove Kyne;
- move one step closer to those Laza lost.

This directly frames the culmination as:
**shepherd → blinded seeker → wolf / corrupted Kyne-fountain state.**

## Kahkaankrein corroboration

Kahkaankrein independently says:
- Laza were mortal children/shepherds outside Kyne's garden;
- the Owl deceived Kyne's dragons;
- a blood curse later destroyed the dragons' wings/lives.

The exact Laza/Owl books and Kahkaankrein testimony now form a strong VIGILANT-internal narrative network rather than relying on later GLENMORIL texts.

## Revised Owl-source hierarchy

For the Laza sequence, source priority is now:

1. exact VIGILANT Laza/Owl books;
2. direct VIGILANT Jhunal and Kahkaankrein testimony;
3. later GLENMORIL/UNSLAAD continuation evidence;
4. supplementary a123999 commentary.

The later Vicn material remains useful but no longer substitutes for missing VIGILANT prose.
