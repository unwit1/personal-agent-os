# Dulsa — VIGILANT continuity

- Continuity: `tes.mod.vigilant`
- Licensed-lore substrate: the name **Dulsa** appears in the official ESO text *The Illusion of Death*
- VIGILANT role: Marukh's beloved / pregnant sacrifice victim in the *Adabal* memory
- Speaking NPC form: **none identified**
- Corpse/container: `CONT 0205AE05` / `zzzCHDulsaCorpseContainer` — **St. Dulsa**
- Associated location: `CELL 0204C45B` / **St. Dulsa's Charnel**
- Associated key: `KEYM 0205186B` / **St. Dulsa's Key**
- Associated relic:
  - `ALCH 020E2597` — **Nail of St. Dulsa**
  - `ACTI 020EA2BA` — relic pickup form
  - `STAT 020EA2BE` — relic display/static form

## Licensed-lore substrate

VIGILANT embeds `BOOK 0212905F` / *The Illusion of Death*, an official ESO text.

That text says Marukh had “toyed with the ape-maiden Dulsa” before his Century of Penance.

This establishes **Dulsa as a pre-existing Elder Scrolls name associated with Marukh**.

It does **not** establish the VIGILANT-specific additions that:
- Dulsa was Marukh's beloved;
- she was pregnant by him;
- Alessia ordered her sacrifice;
- she and the unborn child were killed to restore Adabal;
- she was later venerated as **St. Dulsa**.

Those are VIGILANT-continuity extensions.

The exact ESM copy is preserved at:

`books/0212905F-the-illusion-of-death.txt`

## Adabal memory

`QUST 0205AE03` / **Adabal** contains a location alias named:

- `MemoryDulsa`

This alias points to:
- `LCTN 02383674` / `zzzCHMemDulsa` — **Memory**

The associated memory cell is:
- `CELL 0205426A` / `zzzCHMemoryDulsa` — **Cliffs of Colovia**

Important correction: **MemoryDulsa is a location alias, not a Dulsa actor alias.**

No NPC form named Dulsa is identified in the plugin.

The Cliffs of Colovia cell contains Marukh and other memory actors, but no placed Dulsa actor and no separate unborn-child actor.

## Marukh's address to Dulsa

Marukh's memory dialogue directly addresses Dulsa.

He says:
- seventy-seven secret rituals are nearly complete;
- the lost Stone of Al-Esh will be restored;
- Dulsa's blood and the blood of the child in her belly are required;
- Al-Esh commanded the act;
- the Stone showed him a hero who would defeat the Aldmeri;
- he is willing to sacrifice Dulsa and **his child** for that vision.

He later asks forgiveness from:
- Dulsa;
- his **nameless child**.

This makes the pregnancy and Marukh's claimed paternity explicit within the VIGILANT memory testimony.

## The unborn child

No name is given.

No NPC, creature, activator, corpse, or inventory object has been identified as the child itself.

Current entity model:

**unnamed unborn child of Dulsa and Marukh — dialogue/testimony entity only**

The child should not be conflated with:
- Julius Bruiant;
- the Child of Oblivion;
- generic child models elsewhere in the ESM;
- later “children” used metaphorically in other quests.

## St. Dulsa's Charnel

The ESM contains:
- `CELL 0204C45B` / **St. Dulsa's Charnel**

Inside it is:
- `REFR 0205AE06`
- base `CONT 0205AE05` / **St. Dulsa**

The container uses:

`Clutter\AoM\Cross\crucifixion01.nif`

So VIGILANT physically represents Dulsa as crucified remains.

The container contains:
- one `ALCH 020E2597` / **Nail of St. Dulsa**

Its VMAD uses `CHHasaamaCorpseScript` and points directly to:
- `QUST 0205AE03` / **Adabal**
- stage **10**

This strongly links Dulsa's charnel/corpse to the Adabal memory machinery.

The external Papyrus body is missing, so the exact runtime action at stage 10 should not yet be asserted.

## Eye of Marukh trigger

The same Charnel also contains:
- `REFR 02098541`
- base `ACTI 0209853C` / `zzzCHEyeOfMarukhTrigger`

The placed trigger points to:
- `QUST 0205AE03` / **Adabal**

The base trigger references:
- `MISC 02071CE2` / **Eye of Marukh**
- `MESG 0209853D` / “Eye of Marukh is reacting to something...”

This further supports the Charnel as a **memory-access / memory-framing site** for the Dulsa/Adabal sequence.

## Nail of St. Dulsa

`ALCH 020E2597` is the collectible **Nail of St. Dulsa**.

Its magic effect:
- `MGEF 020E2591` / **Increase Perk Points**

contains the description that the nail is one of those said to have killed **Dulsa and her unborn child** and grants one perk point.

This is the strongest direct in-game statement of the child's death.

Combined with the crucified corpse model, VIGILANT presents Dulsa's death as a nailing/crucifixion-like execution.

### Relic reuse caution

The Nail is also reused through:
- several death-item leveled lists;
- scripted relic-pickup activators in multiple Coldharbour locations;
- static relic displays.

Therefore every Nail pickup is **not** a separate literal murder nail.

The Nail contained inside Dulsa's own crucified corpse in **St. Dulsa's Charnel** is the strongest context-specific instance.

## Charnel access

`KEYM 0205186B` / **St. Dulsa's Key** is used by a locked door inside the Charnel.

The actor reference `CHBossRenaldRef` in the same cell uses a generic `CHAddKeyOnDeath` script whose key property is **St. Dulsa's Key**.

Its current base NPC displays as **Aredhel**, despite the legacy/internal reference name `Renald`.

This should be treated as encounter/access implementation, not historical evidence connecting Aredhel/Renald to Dulsa.

## Later contradictory memory

In *Temptation of Marukh*, the structurally Molag-Bal memory-tail speaker uses Marukh-like first-person memories and says:

- he regrets that he cannot see his beloved Dulsa again;
- he wishes her a happy life.

That conflicts with the preceding *Adabal* memory in which Marukh knowingly sacrifices Dulsa.

Because the same quest later explicitly offers memory modification, this contradiction is evidence of **memory contamination/manipulation**, not proof that Dulsa survived.

## Saint status

VIGILANT consistently uses:
- **St. Dulsa**
- **St. Dulsa's Charnel**
- **St. Dulsa's Key**
- **Nail of St. Dulsa**

This establishes a later saint/relic tradition around Dulsa.

She is not one of the eight figures listed in *The Eight Saints of Cyrod*, so this is a separate cultic/commemorative status.

## Current classification

**Dulsa as a historical name associated with Marukh:** established licensed substrate.

**Dulsa as Marukh's beloved pregnant partner:** VIGILANT memory testimony.

**Marukh as father of the unborn child:** explicit VIGILANT testimony.

**Dulsa/child sacrifice for Adabal:** strong VIGILANT memory claim, reinforced by relic/environmental evidence.

**Crucified St. Dulsa corpse + murder nail:** strong structural/environmental VIGILANT implementation.

**Exact historical sequence:** still memory-dependent and therefore not omniscient fact.

## Canon boundary

The VIGILANT-specific pregnancy, sacrifice, crucifixion/relic tradition, saint status, and Adabal role must remain tagged `tes.mod.vigilant`.
