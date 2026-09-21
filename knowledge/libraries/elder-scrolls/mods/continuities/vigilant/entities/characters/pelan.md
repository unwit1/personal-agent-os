# Pelan

- Continuity: `tes.mod.vigilant`
- Identity link: **Pelan = Inquisitor Pepe / Bishop Pelan** — high confidence within VIGILANT
- Primary active dossier: [Inquisitor Pepe](inquisitor-pepe.md)
- Named relic tradition:
  - `ARMO 02500DDC` / **Pelan's Mask** — craftable/leveled relic; not structurally worn by Pepe
  - `WEAP 020EA4C2` / **Staff of St. Pelan** — carried by Archpriest Centius; not structurally wielded by Pepe
- Major documentary sources:
  - `BOOK 020CB0DF` / *The Eight Saints of Cyrod*
  - `BOOK 0251D5CB` / *Petition to House Tharn, Vol. 11*
  - `BOOK 0251D5CC` / *Petition to House Tharn, Vol. 23*
  - `BOOK 0251D5CD` / *Petition to House Tharn, Vol. 68*
  - `BOOK 0251D5CE` / *Petition to House Tharn, Vol. 77*

## Identity with Inquisitor Pepe

The strongest explicit evidence is Giant Knight Ritho's response when asked about Pepe:

- Ritho identifies Pepe as **"bishop Pelan"**.

The wider ESM strongly reinforces that identification:

- *The Eight Saints of Cyrod* says Pelan found Marukh in the jungles of Colovia.
- Pepe later says he met Marukh in the **jungles of Colovia** and recounts going there after hearing of the Imga prophet.
- the saint text says Pelan lived for thousands of years and gradually became less human.
- Pepe repeatedly speaks from a first-person perspective spanning millennia and describes waiting for thousands of years.
- Arasil says Pepe was once a priest of the Eight Divines and changed after returning from the Colovian jungle.
- named items explicitly preserve the name **Pelan**.

Together these make Pelan and Pepe a high-confidence single identity cluster rather than merely two similar Alessian figures.

## Saint tradition

`BOOK 020CB0DF` describes Pelan as a figure of unknown origin who found Marukh deep in the Colovian jungles.

It says Pelan:
- became Marukh's most trusted servant;
- was entrusted with Marukh's relics after the prophet's death;
- received a blessing of St. Alessia that extended his life for thousands of years;
- gradually became less and less human.

The exact nature of that transformation is not explained in the saint text.

## Petition to House Tharn

The four extracted *Petition to House Tharn* volumes provide a much richer Pelan voice than the saint book.

Across Vols. 11, 23, 68, and 77, Pelan argues with **Amicus** over the direction of the Alessian Order. The preserved exchanges show Pelan:

- defending Belharza's legitimacy through the Amulet of Kings;
- objecting to the Order's attempt to rewrite Belharza, Morihaus, and historical memory;
- defending the citizenship and role of elves, minotaurs, giants, and other non-human peoples in Alessia's rebellion and Empire;
- rejecting the increasingly exclusionary and exterminatory program of the Order;
- objecting to mass executions and the rejection of "Prisoner" figures;
- insisting that the Order still has the Word/doctrines rather than naked authority;
- discovering with Amicus that the Seventy-Seven Doctrines themselves are no longer remembered coherently;
- recalling a blood-covered cliff and Marukh returning in a contradictory, corpse-like state;
- acknowledging that the Stone "chose" him.

These texts make Pelan a participant in VIGILANT's internal debate over manufactured history, authority, free will, racial exclusion, and the Stone.

They should still be treated as in-universe documents rather than neutral historical transcription.

## Transformation chronology

A focused raw-record pass materially clarifies the saint text's claim that Pelan became “less and less human.”

### Early memory forms remain human

- `NPC_ 0212BF48` / `zzzCHInquisitorPepeMemory` is used in *The Grand Inquisitor* and uses a normal master-game humanoid race.
- `NPC_ 0205ADFD` / `zzzCHInquisitorPepeMemory2` is used in *Adabal*, templates from the earlier memory form, and remains humanoid.

In *Adabal*, the Pepe dialogue branch has him agree to hide/get rid of the Stone and swear on Mara's name.

### Memory 6 is visibly transformed

- `NPC_ 0206A230` / `zzzCHInquisitorPepeMemory3` is used in *Remains of the Miracle*.
- this form switches to `RACE 020818A6` / **Alessian Sleeper Race**;
- it uses Pepe's custom Sleeper body/skin and templates from the present-day Pepe identity.

`INFO 0206B54F` has Pepe explicitly acknowledge that he has **changed considerably**.

Later in the same conversation he says:
- centuries have passed;
- he held the Stone for too long;
- he is now an empty shell without a soul;
- the interrogator should learn from the monster standing before them.

This is the strongest direct evidence currently available for the Pelan→Pepe transformation.

### Physical implementation

Present-day `NPC_ 02081E46` / **Inquisitor Pepe** uses:
- `RACE 020818A6` / **Alessian Sleeper Race**;
- `ARMO 02108EB1` / `zzzCHSkinPepe`;
- `ARMA 02108EB0` / `zzzCHNakedPepeAA`;
- model `actors\AoM\ep4\Alessian\Pepe.nif`.

The Alessian Sleeper Race uses a Hagraven skeleton and animation project:
- `Actors\Hagraven\Character Assets\skeleton.nif`
- `Actors\Hagraven\HagravenProject.hkx`

The race is shared with other Alessian Sleeper/Inquisitor forms, so this is best understood as a broader Alessian Sleeper transformation class rather than a body type unique to Pepe.

### Longevity versus corruption

The saint text attributes Pelan's millennial lifespan to Alessia's blessing.

Pepe's own Memory 6 testimony attributes his soulless/monstrous condition to having held the Stone too long.

Lorekeeper should preserve both claims without forcing them into a single mechanism.

A full reconstruction is preserved at:

`analysis/pelan-pepe-transformation.md`

## Pepe continuity

Pepe's later dialogue adds the long aftermath:

- he remembers meeting Marukh in Colovia;
- he remembers Mary/Moura's execution and other Alessian crimes;
- he describes centuries and millennia of waiting;
- he becomes a cynical guide in Coldharbour;
- in Aetherius-related material he increasingly expresses regret and warns the player to stop.

The name shift from **Pelan** to **Pepe** is not yet explained by a dedicated record in the ESM, but the identity link itself is explicit through Ritho.

## Reliability note

Pelan/Pepe is simultaneously:
- saint biography subject;
- participant in reconstructed historical documents;
- memory-scene actor;
- present-tense Coldharbour guide;
- confessor and unreliable narrator.

Lorekeeper should therefore preserve individual claims by source and era rather than flattening all of his testimony into one objective timeline.

## Canon boundary

Pelan's identity as Pepe, his role in finding Marukh, his millennia-long survival, the House Tharn conversations, and his later Coldharbour history are VIGILANT-continuity claims unless separately corroborated by licensed Elder Scrolls sources.
