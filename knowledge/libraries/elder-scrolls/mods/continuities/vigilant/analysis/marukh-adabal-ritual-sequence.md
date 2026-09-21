# Marukh / Adabal ritual sequence

Continuity: `tes.mod.vigilant`

Primary source: user-provided `Vigilant.esm`

This page reconstructs VIGILANT's red-Stone/Adabal sequence while preserving an important limitation:

**the Coldharbour memory quests are not a clean chronological inventory history.**

The ESM deliberately mixes:
- physical item-state changes;
- retrospective testimony;
- role-swapped memory actors;
- explicitly altered memories;
- later quest machinery.

## Shared object family

Three inventory objects use the same model:

`Clutter\AoM\Adabal.nif`

### Early memory form
- `MISC 0205AE01`
- EditorID: `zzzCHAdabalMemory`
- name: **Red Stone**

### Later memory form
- `MISC 0206F543`
- EditorID: `zzzCHAdabalMemory2`
- name: **Red Soul Gem**

### Late-game item
- `MISC 021353DF`
- EditorID: `zzzCHAdabal`
- name: **Adabal**

The common model and naming establish a high-confidence **Adabal object cluster**.

They do not by themselves prove a perfectly linear physical transformation from one record into the next.

## Memory 5 — Adabal

`QUST 0205AE03` / **Adabal** assigns alias:

- `Adabal` → `MISC 0205AE01` / **Red Stone**

So the Stone discussed in the quest is structurally the Red Stone object.

### Seventy-Seven rituals

Marukh says:

- seventy-seven secret rituals are nearly complete;
- their purpose is to restore the lost Stone of Al-Esh;
- the final secret requires the blood of **Dulsa** and her unborn child.

In `INFO 0205AE0E`, Marukh says his mission is to:
- wash the Stone with blood;
- place it in the Tower.

He says the Stone showed him a hero who would defeat the Aldmeri and bring peace, but admits he cannot tell whether the vision is of the future or the past.

This makes the sacrifice a response to **Stone-provided revelation**, not a neutral historical ritual description.

### Aftermath

Marukh later calls Adabal:
- a miracle;
- an emperor;
- bread for the starving.

He then asks forgiveness from Dulsa and the unnamed child.

The Pepe branch of the same quest asks that the Stone be hidden where no one can find it; Pepe agrees.

At this point the ESM still uses the **Red Stone** object.

## Memory 6 — Remains of the Miracle

`QUST 0206A23B` / **Remains of the Miracle** does not expose a Stone inventory alias.

Instead it provides retrospective testimony from the transformed Pepe.

### Filling through mass death

`INFO 0206B553` says:
- a war spilled the blood of tens of thousands;
- the Stone was finally filled;
- after wars and plagues it must contain millions of souls.

Pepe says the Stone is no longer in their world.

### Molag Bal theft

`INFO 0206B555` says:

- **Molag Bal** descended on their Tower on the day of an eclipse;
- he stole the Stone.

`INFO 0206B557` then calls it a **fake Adabal**.

### Pelan/Pepe corruption

The same interrogation has Pepe say:
- he held the Stone too long;
- he is now an empty shell without a soul;
- he is a monster.

This ties prolonged possession of the Stone to Pepe's own degraded condition in his testimony.

## Memory 7 — Temptation of Marukh

`QUST 0206F53C` / **Temptation of Marukh** assigns alias:

- `Stone` → `MISC 0206F543` / **Red Soul Gem**

The object uses the same `Adabal.nif` model as the earlier Red Stone.

That is the strongest structural evidence for a changed state:

**Red Stone → Red Soul Gem**

within the memory corpus.

However, the quest's narrative makes a simple chronological reading unsafe.

## The Molag Bal memory-tail problem

The quest alias:

- `MolagBal` → `NPC_ 020708BB` / `zzzCHMolagBalInMemoryTail`

The early wandering monologue in this quest is explicitly spoken by that NPC through `ANAM`.

Yet the speaker:
- mourns **Dulsa**;
- speaks as the exhausted wanderer associated with Marukh's story;
- describes touching the Stone and feeling his soul sucked out.

This means VIGILANT structurally assigns **Molag Bal's memory-tail actor** to dialogue that behaves like Marukh's personal memory.

That is direct evidence of identity/memory contamination.

### Soul-gem state

The same speaker says:
- touching the Stone caused burning emptiness, as if the soul was being sucked out;
- the Stone had swallowed thousands of souls;
- it was **still not filled**;
- captured souls were violently swirling inside it.

This directly conflicts with the previous memory's claim that the Stone had already been completely filled with millions of souls.

The contradiction should be preserved.

## Alessia command inside the manipulated memory

The same quest assigns:

- `Alessia` → `NPC_ 020708BE` / **Alessia**

Her dialogue tells Marukh:

- fill the Stone;
- restore the lost Adabal;
- place it in the Tower.

This closely echoes Marukh's own instructions from Memory 5.

But because this quest explicitly contains memory-role contamination, the apparition's instruction remains **memory testimony**, not unquestioned divine command.

## Molag Bal offers memory modification

Later in *Temptation of Marukh*, the Molag Bal branch says:
- there is only one escape;
- submit to him;
- fill the Stone with souls.

If accepted, he says he will modify the victim's memory.

This makes explicit memory alteration part of the quest's own causal machinery.

Therefore the memory sequence cannot safely be flattened into:

**ritual A happened, then B, then C**

without reliability qualifiers.

## Late-game Adabal

The ESM later creates:

- `MISC 021353DF` / **Adabal**

This item still uses:

`Clutter\AoM\Adabal.nif`

Its direct structural references are unusually focused.

### Molag Bal carries Adabal

`NPC_ 0212339D` / **Molag Bal** contains:

- one `MISC 021353DF` / **Adabal**

in his inventory.

The same Molag Bal base is:
- assigned to alias `Molag` in `QUST 021363DB` / **Aetherius**;
- physically placed as `ACHR 021233A2` in `CELL 02121AA2` / **Sancremor Angasel**.

This directly corroborates Pepe's earlier testimony that Molag Bal took the Stone, at least at the level of the later playable object.

## Adabal Set trigger

The ESM contains:

- `ACTI 021353E1`
- EditorID: `zzzCHAdabalSetTrigger`
- name: **Set**
- script: `CHAdabalSetTrigScript`

Its VMAD properties include:

- `StageTo = 40`
- `Adabal = MISC 021353DF`
- `myQuest = QUST 021363DB` / **Aetherius**
- `LinkCustom01` keyword

The placed trigger:

- `REFR 021353E2`

is in the **same Sancremor Angasel cell** as Molag Bal.

Its linked-reference data points through `LinkCustom01` to:

- `REFR 021342BB`

whose base is:

- `ACTI 021342BC` / `zzzCHFXAetheriusPortal`

The portal uses a Sovngarde-style portal effect and an `CHAetheriusGateScript`.

This gives a strong structural chain:

**Molag Bal carries Adabal → Adabal-specific trigger expects that exact item → trigger advances Aetherius to stage 40 → trigger is linked to the Aetherius portal system.**

The external Papyrus body is missing, so the exact item-removal/placement calls cannot yet be stated.

## Static Adabal in the same tower cell

The same cell also contains:

- `STAT 021353D1` / `zzzCHAdabalStatic`
- placed as `REFR 021353D2`

The static uses:

`Clutter\AoM\AdabalStatic.nif`

and is enable-parented to a nearby marker.

This strongly suggests a visual/set-piece representation associated with the Aetherius gate sequence.

Again, exact enable timing requires the external script layer.

## Stone-Fire is related but not a clean physical handoff

VIGILANT also contains:

- `ACTI 0208CA88`
- EditorID: `zzzCHAdabalACT`
- name: **Stone-Fire**
- model: `Clutter\AoM\AdabalStatic.nif`

Two placed references exist:

### Memory placement
- `REFR 0208CA89`
- `CELL 02088A8D` / **Sancremor Angasel**
- location record: `zzzCHMemoryMolag`

### Good Aetherius placement
- `REFR 02098547`
- `CELL 021353E4` / **Aetherius**

However, both references run `CHHasaamaCorpseScript` and point to:

- `QUST 02080E91` / **The Nameless Bard**

at different quest stages.

Therefore these Stone-Fire activators are entangled with the **Nameless Bard memory machinery**, not simply the Aetherius quest's Adabal item handoff.

They support visual/metaphysical recurrence of the Stone, but should not be used as proof of a single uninterrupted physical object chronology.

## Best-supported sequence

### Structural layer

1. *Adabal* quest uses **Red Stone** as its Adabal alias.
2. *Temptation of Marukh* uses **Red Soul Gem** as its Stone alias.
3. Red Stone, Red Soul Gem, and late-game Adabal all share the same `Adabal.nif` model.
4. Late-game Molag Bal physically carries **Adabal**.
5. An Adabal-specific trigger in Molag Bal's Aetherius tower cell requires the same Adabal FormID and advances the Aetherius quest.
6. That trigger links directly into the Aetherius portal system.

### Testimony layer

Marukh/Pelan/Pepe memories claim that:
- blood sacrifice restores the Stone;
- wars and plagues fill it with souls;
- Molag Bal steals it;
- prolonged possession degrades the holder;
- the restored Adabal should be placed in a Tower.

### Manipulation layer

*Temptation of Marukh* simultaneously shows:
- Molag Bal occupying a Marukh-like memory voice;
- contradictory Stone-fill states;
- an Alessia apparition giving commands;
- explicit memory modification.

So the memory testimony is intentionally unstable.

## Current Lorekeeper model

Recommended object relations:

- `Red Stone (0205AE01) --memory_state_of--> Adabal cluster`
- `Red Soul Gem (0206F543) --memory_state_of--> Adabal cluster`
- `Adabal (021353DF) --late_game_item_of--> Adabal cluster`
- `Molag Bal --carries--> Adabal`
- `Adabal Set Trigger --requires/references--> Adabal`
- `Adabal Set Trigger --advances--> Aetherius stage 40`
- `Adabal Set Trigger --links_to--> Aetherius portal`
- `Stone-Fire --symbolic/interactive representation_of--> Adabal cluster`

Do not currently assert:

- every memory Stone is literally the same uninterrupted physical object;
- the Red Soul Gem necessarily occurs chronologically after the fully filled Stone testimony;
- Alessia objectively commanded the ritual;
- Molag Bal's memory-tail monologue is a reliable Marukh autobiography;
- Stone-Fire in Good Aetherius is simply the physical Adabal after the portal event.

## Canon boundary

The historical **Chim-el-Adabal** and Tower/Stone concepts have licensed TES roots.

This specific sequence of:
- seventy-seven restoration rituals;
- Dulsa/unborn-child sacrifice;
- wars/plagues filling the Stone;
- Molag Bal stealing it;
- Pelan's corruption;
- memory manipulation;
- Adabal opening/participating in the Aetherius gate;

belongs to `tes.mod.vigilant` unless independently corroborated.
