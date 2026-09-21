# Order of Diagna — VIGILANT continuity

- Continuity: `tes.mod.vigilant`
- Type: Yokudan/Redguard martial tradition represented through multiple Coldharbour figures
- Main VIGILANT-linked figures: Gaiden Shinji, Aredhel, Judo of the Order of Diagna
- Major analysis: `analysis/diagna-coldharbour-cluster.md`

## Distributed implementation

VIGILANT does not present the Order of Diagna as one clean active faction questline.

Instead, the tradition appears through several separate implementations:

1. **Gaiden Shinji** — major named character in the Coldharbour Arena.
2. **Aredhel** — later figure equipped by Gaiden and wearing the Blade of Diagna set.
3. **Judo of the Order of Diagna** — named Soul-Shriven enemy variant using Knight of Diagna equipment.
4. crafting conditions that mechanically link the Aredhel/Pitier and Judo encounter branches.

This is best modeled as a **Diagna tradition cluster** rather than proof of one contemporaneous squad.

## Gaiden Shinji

Gaiden is the narrative center of the cluster.

He:
- appears as a persistent named figure in the Arena;
- has unique dialogue and follower machinery;
- searches for a sword lost when Yokuda sank;
- expresses interest in Diagna;
- says he gave Aredhel a sword and armor.

His lost sword remains unidentified.

## Aredhel

Aredhel appears in St. Dulsa's Charnel and participates in **Pitier**.

He wears the **Blade of Diagna** armor family and carries Aredhel's Sword.

Gaiden's statement that he supplied Aredhel with sword and armor is strongly consistent with that equipment.

However, the ESM does not prove that Aredhel became a formal historical member of the Order.

## Judo

`NPC_ 0251653B` / **Judo of the Order of Diagna** is structurally a named **Soul-Shriven** variant.

He:
- belongs to the Soul-Shriven faction;
- uses Soul-Shriven abilities/templates;
- is spawned through the Feral Soul-Shriven system;
- appears in the Arena District;
- wears the **Knight of Diagna** set;
- carries two Akaviri Black Katanas;
- has no unique resolved dialogue.

This makes Judo evidence that the Diagna tradition is preserved in Coldharbour encounter ecology, but not a second Gaiden-like narrative protagonist.

## Two distinct armor traditions

VIGILANT implements two related but separate equipment families:

### Knight of Diagna
Used by Judo.

### Blade of Diagna
Used by Aredhel.

Their crafting conditions overlap:
- Judo's death can unlock Knight of Diagna crafting;
- completing Pitier can also unlock Knight gear;
- Pitier completion unlocks Blade gear and the playable Akaviri Black Katana.

This mechanical bridge links the cluster without making Judo and Aredhel the same character.

## Gaiden's lost sword

Judo's Akaviri Black Katana uses legacy Renald asset naming, but no dialogue connects it to Gaiden's lost Yokudan sword.

Do not encode:
- Akaviri Black Katana = Gaiden's lost sword;
- Judo = keeper of Gaiden's sword;
- Aredhel's Sword = the lost Yokudan sword;

without future evidence.

## Institutional ontology

Current safe model:

**Order of Diagna → historical/martial tradition represented through multiple Coldharbour identities and equipment systems.**

VIGILANT's Coldharbour forms may represent:
- literal survivors;
- soul-shriven remnants;
- reconstructed historical identities;
- or dream/Oblivion manifestations.

The ESM does not force one explanation for all members.

## Relationship map

- **Gaiden → associated with → Diagna**
- **Gaiden → gives equipment to → Aredhel**
- **Aredhel → wears → Blade of Diagna**
- **Judo → named as → Order of Diagna**
- **Judo → implemented as → Soul-Shriven**
- **Judo → wears → Knight of Diagna**
- **Pitier completion → unlocks → Diagna crafting families**

## Canon boundary

Gaiden Shinji and the Order of Diagna originate in established Elder Scrolls lore.

The specific Aredhel/Judo relationships, Coldharbour encounter ecology, equipment split, and crafting bridges are VIGILANT-continuity implementation.
