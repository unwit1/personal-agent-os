# The Eight Saints of Cyrod — mapping pass 1

Continuity: `tes.mod.vigilant`  
Primary source: `BOOK 020CB0DF` / **The Eight Saints of Cyrod**

This page was built in small passes and now covers all eight saints named in the source.

## Sard

The saint text describes Sard as Alessia's former handmaiden, later servant of Belharza and Marukh, with one red and one blue eye and supernatural youth attributed to Alessia's blessing. It says that after Marukh died Sard rapidly aged to ash, leaving only jewel-like eyes.

The ESM independently implements:
- **Sard's Charnel** (`02109458`);
- **Sard's Ossuary** (`0210CDFD`);
- **Sard's Red Eye Ring** (`020EB827`);
- **Sard's Blue Eye Ring** (`020EB828`);
- **Ashes of St. Sard** (`020E2592`);
- **Sard's Charnel Key** (`0210A8E5`).

The door graph directly connects the Charnel and Ossuary. More significantly, both eye rings are stored in the **Vena Petilius** treasure container, and that container is physically placed inside **Sard's Ossuary**. The same container also carries **Ashes of St. Sard**.

No Sard NPC form or direct dialogue has been found in the current ESM inventory.

Current classification: **high-confidence saint → charnel/ossuary/relic identity cluster**. The red/blue jewel-eye ending of the saint biography is directly environmentalized by the two named eye rings in Sard's own ossuary.

Other red-eye imagery in VIGILANT remains unlinked unless structural evidence connects it to Sard.

## Moura / Mary

The saint text explicitly states that Moura's true name was **Mary** and describes her as a High Rock healer who cured plague/vampiric corruption before the Alessian Order executed her during the Thrassian plague.

The ESM now gives this identity cluster much stronger structural support:

- `NPC_ 020F9649` / **Mary the Dark Maiden** is assigned to alias **Mara** in `QUST 0212C4F4` / *The Grand Inquisitor*.
- The same NPC base is the **Shoggoth Mother** boss in `QUST 024F69C0`.
- `ACHR 020F964C` places Mary the Dark Maiden in **Bed of Corruption**.
- `BOOK 0212A7B4` is *Fragment of the Stone: Mary the Dark Maiden*.
- a separate `NPC_ 022A0679` / **Mary** is used in *Pelinal the Bloody* and placed in **Burosel**.
- Sir Caius, Ja'zhan, Pope Megus, Pepe, and Atima preserve different pieces of Mary's healing, burning, recurrence, and “children” tradition.

*The Grand Inquisitor* is especially important because Pepe addresses the Mary-the-Dark-Maiden actor as **Mara** while condemning her to the stake. That makes the Moura/Mary/Mara linkage structural, not merely thematic.

Current classification: **high-confidence Moura = Mary = the Mara-role identity cluster**, with multiple later memory/Coldharbour manifestations. The exact mechanism connecting saint, memory victim, Shoggoth Mother, and later Mary forms remains unresolved and should not be flattened into a simple resurrection chronology.

Rumors that Mary literally consorted with Molag Bal or biologically birthed the monsters remain attributed claims, not established fact.

## Jhunal

The saint text presents Jhunal as an Atmoran mage who joined Marukh, spread rune knowledge through eastern Cyrodiil, created **Marukh's Torch**, refused to surrender it to the Order, and was exiled. It says he later died and his secret passed to Cosmas.

The ESM deliberately complicates that endpoint:

- **Jhunal the Owl** (`NPC_ 0225B23C`) is a surviving speaker.
- Three **Piece of Jhunal** actors (`0225B23F`) are placed alongside him inside **Jhunal's Library**.
- Jhunal says the Black Worm tore him to pieces and that recovering took hundreds of years.
- a separate **Jhunal** corpse/container in **Marukh's Underground Priory** carries **Bone of Jhunal**, **Jhunal's Library Key**, and **Jhunal's Silver Ring**.
- **Jhunal's Golden Ring** is inside **Jhunal's Egg** in the Golden Sanctuary; Pope Megus says the Owl gave him that egg as a vessel intended for blood, flesh, bones, and new life.
- **Arcana of Jhunal** is carried by **Burnt Casimir** in the Prayer Hall, in the same storyline where Sir Berich blames Jhunal's stolen eternal fire-rune knowledge for destructive consequences.
- `BOOK 0218B1BA` / *The Art of the Ayleids* is explicitly authored by Jhunal and discusses flesh art.
- Saklas's *Bald Man-Ape* quest has a dedicated Jhunal's Library map-marker alias and later places an “owled” Saklas form inside the Library.

Current classification: **high-confidence Jhunal identity cluster with deliberate bodily fragmentation and unresolved ontology**. The saint's “death,” corpse/relic cache, surviving Owl, and literal Pieces should remain layered evidence rather than being forced into a single resurrection chronology.

The ESM does not yet prove that **Marukh's Torch**, the Prayer Hall fire rune, and **Arcana of Jhunal** are exactly the same magical object or technique.

## Nenyond

The saint text describes Nenyond as an eastern Cyrodiilic lord and comparatively moderate Marukhati Selective who spent his fortune constructing an underground priory. He and Manthar disappeared after Dawn Era ruins were discovered beneath it; Silorn later vanished while searching for them, after which the ruins were sealed.

The ESM independently implements:
- **Nenyond's Underground Priory** (`0210EBFD`);
- **Funeral Temple** (`021114AF`);
- **Nenyond's Key** (`0212D026`);
- a direct door relationship between the priory and Funeral Temple.

No Nenyond NPC form or first-person dialogue has been found in the current VIGILANT inventory.

Current classification: **VIGILANT-specific saint biography with strong location corroboration but weak personal/first-person evidence**.


## Manthar

The saint text describes Manthar as a sorcerer/architect of the Alessian Order who built priories with Nenyond and disappeared beside him while exploring Dawn Era ruins beneath Nenyond's foundation.

The ESM independently implements:
- **Sorcerer Manthar** (`NPC_ 021146D9`) as the Bone Lord boss form;
- a summon version (`0213B503`);
- **Conjure Sorcerer Manthar** (`MGEF 0213B504`);
- a placed boss reference in **Funeral Temple** (`CELL 021114AF`).

Because Funeral Temple directly connects to Nenyond's Underground Priory, Manthar's encounter placement strongly reinforces the saint-text geography.

Current classification: **high-confidence historical→boss identity cluster; transformation mechanism unresolved**.

## Silorn

The saint text says Silorn helped found the Marukhati Selectives, entered the Nenyond ruins searching for Nenyond and Manthar, and that only his skin returned.

A raw-record pass sharpens the environmental implementation:

- `CONT 020D1A66` / **Abbot Silorn** uses the model `Hangedman01.nif`, is placed in **Funeral Temple**, and contains **Hide of Abbot Silorn**.
- `ACTI 02113B04` / **Abbot Silorn** uses `Hangedman01Movable.nif`; two of these hanging-body activators are placed in Funeral Temple.
- `ALCH 020E2593` / **Hide of Abbot Silorn** is the collectible relic.
- the previously noted `NPC_ 02114115` / **Abbot Silorn** is internally `zzzCHInvisibleSpotter` and links into a SightJacker setup, so it is better classified as technical scene machinery than as a resurrected Silorn.
- **Silorn's Priory** and its two keys remain a separate institutional location on the Underground Lake/Wellspring route.

The Hide relic also has reusable pickup placements in several unrelated Coldharbour interiors, so those copies are gameplay relic placements rather than multiple literal pieces of Silorn.

Current classification: **high-confidence saint → returned-skin tradition → Funeral Temple hanging-remains/relic implementation**. The exact mutilation/return mechanism remains unresolved.

## Caliburn

The saint text describes Caliburn as a founder of the Marukhati Selectives and one of its most fanatical members. It says he brought Marukh's holy body to **Malada**, attempted to open a gate to **Aetherius**, failed, and vanished with hundreds of followers.

The ESM independently implements:
- **Arch-Selective Caliburn** (`NPC_ 0211C369`) as a boss;
- a summon version (`0211E0A2`);
- a placed boss reference (`ACHR 0211C36A`) in **Malada Ageasel** (`CELL 0211BC4B`);
- *Fragment of the Stone: Arch-Selective Caliburn* (`BOOK 0211E0A5`).

Current classification: **high-confidence saint→Malada boss/Stone-fragment identity cluster**. The exact failed-Aetherius mechanism remains unresolved.

## Pelan

The saint text says Pelan found Marukh in the Colovian jungles, became his most trusted servant and relic-keeper, and survived for thousands of years under Alessia's blessing while becoming progressively less human.

VIGILANT gives a strong explicit identity link: Giant Knight Ritho calls Pepe **"bishop Pelan."**

That identification is independently reinforced because:
- Pepe says he met Marukh in the Colovian jungle;
- Pepe speaks of waiting for thousands of years;
- Arasil says Pepe changed after returning from the Colovian jungle;
- the plugin contains **Pelan's Mask** and **Staff of St. Pelan**;
- four *Petition to House Tharn* volumes preserve Pelan arguing against the Alessian Order's increasingly exclusionary, revisionist, and violent program.

Current classification: **high-confidence Pelan = Inquisitor Pepe identity cluster**, while individual historical claims remain source- and memory-dependent.
