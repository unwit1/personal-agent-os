# Jhunal

- Continuity: `tes.mod.vigilant`
- Historical role: Atmoran mage associated with Marukh and the Alessian Order
- Speaking form: `NPC_ 0225B23C` / `zzzCHJhunalOwl` — **Jhunal the Owl**
- Fragment form: `NPC_ 0225B23F` / `zzzCHEncJhunalFission` — **Piece of Jhunal**
- Major location: `CELL 02259C5B` / **Jhunal's Library**
- Major relics:
  - `ARMO 020CB0AB` — **Jhunal's Silver Ring**
  - `ARMO 020CB0AE` — **Jhunal's Golden Ring**
  - `ARMO 023B3500` — **Arcana of Jhunal**
  - `ALCH 020E2595` — **Bone of Jhunal**
  - `KEYM 0225B235` — **Jhunal's Library Key**

## Saint tradition

`BOOK 020CB0DF` / *The Eight Saints of Cyrod* describes Jhunal as a mage from Atmora who was banished from Skyrim and later joined Marukh's Alessian Order.

The book credits him with:
- extensive knowledge of magical runes;
- helping Marukh's influence spread through eastern Cyrodiil;
- creating a secret arcana called **Marukh's Torch**, said to be capable of burning an entire city;
- refusing to give that art to the Alessian Order and being exiled;
- passing the knowledge to his disciple **Cosmas**, who later used it at Malada and Pailune.

The same text claims later Alessian histories credited Cosmas rather than Jhunal because Jhunal had been expelled. That is a VIGILANT-specific historiographic claim, not neutral base-canon history.

## Jhunal the Owl

Seven INFO records resolve uniquely to **Jhunal the Owl**.

His testimony says:
- the **Black Worm** learned secret arts from him, then used Jhunal as a test subject and tore him into pieces;
- it took Jhunal hundreds of years to recover to his current size;
- he used **Laza** to harvest dragons;
- he attempted to tear out a dragon's soul;
- he wanted a dragon soul because he hoped to become a dragon;
- black souls are the essence of men, elves, and the Hist, a striving he calls the **Will to Shezarr**;
- the red Stone is a false imitation of Lorkhan's blood that can distort souls and interfere with the Tower.

These are Jhunal's own metaphysical claims, not objective narration.

## Jhunal's Library

The ESM physically places all of the following inside `CELL 02259C5B` / **Jhunal's Library**:

- `ACHR 0225B23D` — **Jhunal the Owl**
- `ACHR 0225B241` — **Piece of Jhunal**
- `ACHR 0225B242` — **Piece of Jhunal**
- `ACHR 0225B243` — **Piece of Jhunal**

The three separate fragment actors give literal implementation support to Jhunal's statement that he was torn into pieces.

The side quest `QUST 0251FD3E` / **Bald Man-Ape** assigns its `MapLib` alias to `REFR 0225B236`, the map marker named **Jhunal's Library**. Saklas asks the player to locate the Library before the Forces of Order mine it.

Saklas says that while examining the souls/memories of Alessian priests, the name **Jhunal** repeatedly appeared. He finds it significant that Jhunal is both the name of an old Nord deity and apparently the name of a First Era person.

## The corpse/relic cache in Marukh's Underground Priory

A separate container record, `CONT 020CB0DC`, is simply named **Jhunal**.

Its placed reference `REFR 020CB0DD` is physically located in **Marukh's Underground Priory** (`CELL 02101AA1`).

The container holds:
- **Bone of Jhunal**
- **Jhunal's Library Key**
- **Jhunal's Silver Ring**
- **Beacon of Magnus**

This is the strongest environmental evidence for a historical Jhunal relic-cache/body tradition distinct from the later Owl form in the Library.

The **Bone of Jhunal** magic effect describes it as the bone of **"Jhunal, the sorcerer of the Elder Wood"** and increases Magicka.

The repeated use of the same Bone base item in several unrelated death-item lists should not be read as multiple independent historical bones. The body/container in Marukh's priory is the contextually strongest placement.

## Silver and Golden Knowledge

### Silver Ring

`ARMO 020CB0AB` carries the enchantment **Jhunal's Silver Knowledge**.

Its effect text says:

> All spells last twice as long.

The Silver Ring is stored in the Jhunal body/cache in Marukh's Underground Priory.

### Golden Ring

`ARMO 020CB0AE` carries **Jhunal's Golden Knowledge**.

Its effect text says Illusion spells work on targets of twice the normal level.

The Golden Ring is stored in `CONT 02224F3D` / **Jhunal's Egg**. The Egg is physically placed as `REFR 02224FF1` in the **Golden Sanctuary** (`CELL 02224E78`).

Jhunal's Egg also contains the **Staff of Prophet Marukh** and **Sword of Prophet Marukh**, making it a broader relic cache rather than proof that the ring was literally laid there by the historical Jhunal.

## Arcana of Jhunal and the flame of Magnus

`ARMO 023B3500` / **Arcana of Jhunal** carries the enchantment **Arcane Fire**.

Its magic-effect description calls it a:

> Concealed rune of Jhunal.

The rune illuminates the wearer's surroundings.

The Arcana is not placed in Jhunal's Library. It is carried by `CONT 023B3504` / **Burnt Casimir**, whose reference `023B3507` is in the **Prayer Hall** (`CELL 020CF815`).

That placement aligns strongly with Sir Berich's dialogue:

- Berich identifies a fire rune as one of the **Wisdoms of Magnus** that Jhunal stole from Saarthal.
- he says the flame burns forever;
- he claims Jhunal tried to use it to drag down Magnus;
- he says **Casimir got too close to the flame of Magnus**, and the flame took hold of him.

The ESM therefore creates a direct environmental triangle:

**Jhunal's rune/Arcana → Burnt Casimir → Berich's flame-of-Magnus testimony.**

This corroborates the association, but Berich's claim that Jhunal stole the knowledge from Saarthal remains character testimony.

## Dragon-soul implementation

Jhunal the Owl's death-item leveled list, `LVLI 0225B244`, includes a **Dragon Soul Stone** among its possible drops.

This is suggestive because Jhunal explicitly says he sought a dragon soul in order to become a dragon.

Because the item is part of a leveled death list rather than a unique scripted relic, Lorekeeper records this as **supporting implementation/thematic evidence**, not proof that Jhunal successfully possessed a dragon soul.

## The Art of the Ayleids

`BOOK 0218B1BA` / **The Art of the Ayleids** is explicitly credited **“by Jhunal.”**

The surviving excerpt discusses Ayleid flesh-art and the torture of Nedic captives. Because the text is authored in-universe by Jhunal, it provides a separate documentary voice from both *The Eight Saints of Cyrod* and Jhunal the Owl's present-tense dialogue.

The ESM places copies in four distinct locations:

- **Bruiant Mansion South Wing** (`0204A8B9`)
- **Slave Trader's House** (`020B07D1`)
- **Prison Tower** (`020F9C21`)
- **Fort Welkynd** (`020E2693`)

The distribution shows that VIGILANT treats Jhunal's writing as a circulated historical/reference text rather than a unique manuscript confined to his Library.

Exact decoded source text is preserved at:

`books/0218B1BA-the-art-of-the-ayleids.txt`

Its contents should be treated as **Jhunal's authored account/analysis**, not automatically as objective confirmation of every described Ayleid practice.

## Identity model

VIGILANT does not preserve Jhunal as one simple body in one place. His identity is distributed across:

1. the historical saint biography;
2. a body/relic cache in **Marukh's Underground Priory**;
3. the active **Jhunal the Owl** in **Jhunal's Library**;
4. three literal **Piece of Jhunal** actors;
5. rings and magical knowledge caches in multiple locations;
6. **Arcana of Jhunal** tied environmentally to Casimir and the flame of Magnus;
7. Saklas's claim that Jhunal's name persists inside Alessian souls/memories.

Current classification: **high-confidence Jhunal identity/relic network; exact continuity between historical body, Owl, fragments, and distributed relics remains ontologically unresolved.**

## Canon boundary

VIGILANT's First Era Jhunal, Marukh's Torch, relationship to Cosmas, theft-of-Saarthal claim, Owl/fragments, dragon-soul experiments, relic network, and metaphysical theories remain `tes.mod.vigilant` material unless separately corroborated by licensed TES sources.
