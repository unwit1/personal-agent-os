# Slave Trader note trail

Continuity: `tes.mod.vigilant`

Primary records:
- `020B0822` — Slave Trader's Note 1
- `020B0823` — Slave Trader's Note 2
- `020B0824` — Slave Trader's Note 3
- `020B0825` — Slave Trader's Note 4
- `020B0826` — Slave Trader's Note 5
- `020B0827` — Slave Trader's Note 6
- `020B0828` — Slave Trader's Note 7
- `020C8FCE` — Slave Trader's Note 8

Direct actor:
- `NPC_ 020CAA71` / **Slave Trader**
- dossier: `entities/characters/slave-trader.md`

## Exact eight-note sequence

1. **Note 1**
   - “A body in sarcophagus.”

2. **Note 2**
   - “A miserable bard. A poor storyteller with a boring tale.”

3. **Note 3**
   - “The morning did not come for Gideon.”

4. **Note 4**
   - “Bravil burned.”

5. **Note 5**
   - “Gilverdale sank twice.”

6. **Note 6**
   - “Gathering firewood, yesterday and today. What will we burn tomorrow?”

7. **Note 7**
   - “The shepherd is dead, and the wolf set free.”

8. **Note 8**
   - quotes the opening of *Elegy Written in a Country Churchyard*, ending with the world being left “to darkness and to me.”

The notes read as compressed observations/waypoints rather than commercial records.

## Direct placement and acquisition map

The restored canonical VIGILANT ESM now resolves all eight routes.

### Note 1 — Mathmalatu Priory

- placed as `REFR 020B082A`
- cell: `CELL 0207FB11` / **Mathmalatu Priory**

The text's sarcophagus image strongly aligns with the opening Coldharbour sarcophagus sequence.

### Note 2 — Slave Trader's House

- placed as `REFR 020B0829`
- cell: `CELL 020B07D1` / **Slave Trader's House**

This is the clearest fixed-location anchor tying the note series to the named Slave Trader's own environment.

### Note 3 — Temple of Mara

- placed as `REFR 020C8445`
- cell: `CELL 020C62F3` / **Temple of Mara**

### Note 4 — Imperial Prison Sewers

- placed as `REFR 02121AA0`
- cell: `CELL 020F4D2F` / **Imperial Prison Sewers**

### Note 5 — Malatar Mansion

- placed as `REFR 02121AA1`
- cell: `CELL 021038CB` / **Malatar Mansion**

### Note 6 — Sir Ralvas

`BOOK 020B0827` is directly carried by:

- `NPC_ 020BCF1E` / **Sir Ralvas**

Ralvas is the direct Knight actor in **Knight of Zenithar**.

This means Note 6 is not an unplaced/unused book: it is a character-held clue.

The exact reason Ralvas possesses it remains unresolved.

### Note 7 — Marukh death-item list

`BOOK 020B0828` is directly included in:

- `LVLI 020E76B2` / `zzzCHDeathItemMarukhu`

That leveled list is assigned as the death-item list of:

- `NPC_ 0211D025` / **Marukh**

The list also contains:
- *The Illusion of Death*
- Nail of St. Dulsa
- several external/master items.

Therefore Note 7 participates in Marukh's direct loot/death-item system.

Do not infer from this alone that Marukh authored the note.

### Note 8 — dead Slave Trader

`BOOK 020C8FCE` is directly carried by:

- `NPC_ 020CAA71` / **Slave Trader**

The actor is placed as:
- `ACHR 020CAA72`
- in **Chapel of Arkay Cemetery**
- using **Bone Human Race**
- with ragdoll/dead-state data.

This makes Note 8 the strongest endpoint in the sequence:
**the named Slave Trader's remains carry the final Slave Trader note in a cemetery.**

## The sarcophagus survivor

In the Coldharbour main quest, Inquisitor Pepe tells the player:

> Fools climb out from this sarcophagus every day. I don't remember all of them.
>
> No, wait. There was another one who was still alive like you. I believe he was a slave trader.
>
> But his eyes burned like fire. Yours are as cold as ice.

When asked where that slave trader went, Pepe answers:

> I don't know and I don't care.

The direct actor record is not mechanically referenced by this INFO, so the safest identity relation remains:

**fiery-eyed sarcophagus survivor ↔ very strong candidate for NPC 020CAA71 / Slave Trader**

rather than a formally encoded alias link.

## Sir Henrik and Slave Trader's House

The restored ESM strengthens the trail through **Knight of Julianos**.

Henrik says:

> I don't quite remember. There was something about a slave trader and cheap booze...

and later:

> When I woke up again, he was no longer there. What a bastard, to lock me up in this hole...

The quest contains:

- `PACK 02126606`
- `zzzCHsq07HenikStaySlaverHouse`

This directly links Henrik's implementation to **Slave Trader's House**.

Thus the Slave Trader thread intersects:
- the note route;
- the Knights of the Nine;
- captivity/imprisonment;
- the Coldharbour sarcophagus cycle.

## Note 6 — firewood

Note 6's “firewood” wording directly resonates with:
- *Judgement*;
- Mary/Moura's execution;
- *The Grand Inquisitor*;
- *A Vision in Malada* stanza 5.

Its carrier being **Sir Ralvas** is now structural fact.

That does not prove the note refers to Mary specifically.

## Note 7 — shepherd and wolf

Note 7 says:

> The shepherd is dead, and the wolf set free.

The restored ESM now gives substantially stronger Laza context elsewhere:

- the exact Laza book says one may **take on the name of Laza**;
- the White Owl describes shepherd → wolf → wind;
- Kahkaankrein calls Laza mortal children/shepherds outside Kyne's garden;
- Jhunal says he used Laza as an obedient shepherd.

Because Note 7 is in **Marukh's death-item list**, its final referent remains deliberately ambiguous.

Strong motif connection:
**Note 7 ↔ Laza shepherd/wolf transformation language**

Unresolved:
- whether “the shepherd” is one specific Laza;
- whether “the wolf” is Laza, Molag Bal, another figure, or a symbolic state;
- why Marukh carries this note.

## Note 8 — cemetery endpoint

Note 8 is the opening of Thomas Gray's *Elegy Written in a Country Churchyard*.

Its direct placement on the dead Slave Trader in **Chapel of Arkay Cemetery** gives the literary quotation a concrete environmental function.

This strongly supports:
- finality;
- death;
- cemetery endpoint;
- a self-conscious end to the note itinerary.

a123999's supplementary background article says the Slave Trader's life ended with writing a poem.

The ESM's Note 8-on-corpse placement is highly compatible with that statement.

## Funeral grave implementation clue

Three grave activators in the same cemetery are:

- `ACTI 020CAA73` / `zzzCHSlaverTomb01` — **Johan's Grave**
- `ACTI 020CAA74` / `zzzCHSlaverTomb02` — **Simon's Grave**
- `ACTI 020CAA75` / `zzzCHSlaverTomb03` — **Tlass' Grave**

They are the graves Martha seeks in **Funeral**.

The internal **SlaverTomb** naming creates a direct implementation-level connection to the Slave Trader namespace.

The narrative meaning is not yet explicit.

Do not infer:
- Slave Trader = Johan / Simon / Tlass;
- Martha is the Slave Trader's family;
- the Slave Trader built the graves.

This is a high-value unresolved implementation clue.

## A Vision in Malada — stanza 9

Stanza 9 remains mapped to the fiery-eyed Slave Trader with medium confidence.

The new direct source strengthens that mapping because:
- a concrete Slave Trader NPC exists;
- Note 1 begins at the sarcophagus motif;
- Pepe explicitly remembers a fiery-eyed slave trader coming through the sarcophagus;
- Note 8 ends on the Slave Trader's cemetery remains.

Still unresolved:
- the exact stanza-8 brother killed by the Slave Trader;
- direct proof that the Slave Trader carried the Stone;
- exact gate/event referenced by the prophecy.

## LST cross-work clue

The actor EditorID is:

`zzzCHlstSlaveTrader`

The **lst** fragment is compatible with a123999's supplementary statement that this Slave Trader is the soul/protagonist of Vicn's earlier *LST Bravil Underground*.

This is meaningful implementation evidence, but not enough by itself to import the whole LST protagonist biography as direct VIGILANT fact.

## Current model

The direct source now supports:

**a named Slave Trader emerges in the same sarcophagus cycle described by Pepe, leaves/is associated with an eight-note itinerary through Coldharbour locations and characters, intersects Sir Henrik and the Knights, and ends as dead Bone-Human remains in the Chapel of Arkay Cemetery carrying Note 8.**

The notes appear to catalogue prior calamities, transformations, and recurring Vicn/VIGILANT events.

Whether they are:
- chronological travel notes;
- memories from repeated lives;
- prophecy confirmations;
- cross-work recollections

remains open.

## Reliability

High-confidence direct:
- exact eight note texts;
- placements for Notes 1–5;
- Note 6 held by Sir Ralvas;
- Note 7 in Marukh's death-item list;
- Note 8 held by the named dead Slave Trader;
- Slave Trader NPC, house, outfit, race, cemetery placement;
- Pepe's fiery-eyed slave-trader testimony;
- Henrik's Slave Trader/house connection.

Strong but not formally alias-linked:
- Pepe's fiery-eyed sarcophagus survivor = the named Slave Trader NPC.

Supplementary:
- Slave Trader = prior *LST Bravil Underground* protagonist/soul;
- his life ends through writing the final poem.

## Remaining questions

1. What exactly connects the Slave Trader to the `SlaverTomb` Johan/Simon/Tlass graves?
2. Why does Sir Ralvas carry Note 6?
3. Why is Note 7 part of Marukh's death items?
4. Which events exactly correspond to Gideon, Bravil, and Gilverdale in this itinerary?
5. Does the actor's `lst` EditorID encode a formal cross-mod identity bridge beyond the supplementary commentary?
6. Can scripts/stages establish a direct identity link between the sarcophagus survivor and `NPC_ 020CAA71`?

## Canon boundary

The Slave Trader note sequence, fiery-eyed sarcophagus survivor, cemetery endpoint, and associated cross-work hints are Vicn/VIGILANT continuity material.
