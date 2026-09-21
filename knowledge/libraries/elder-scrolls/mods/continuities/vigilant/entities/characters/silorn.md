# Silorn

- Continuity: `tes.mod.vigilant`
- Historical role: founder of the Marukhati Selectives; seeker of Nenyond and Manthar
- Primary post-disappearance representation: hanging corpse / returned-hide relic
- Technical NPC form: `NPC_ 02114115` / `zzzCHInvisibleSpotter` — display name **Abbot Silorn**
- Associated locations:
  - `CELL 02239B51` / **Silorn's Priory**
  - `CELL 021114AF` / **Funeral Temple**
- Associated relic: `ALCH 020E2593` — **Hide of Abbot Silorn**

## Saint tradition

`BOOK 020CB0DF` / *The Eight Saints of Cyrod* describes Silorn as one of the founders of the **Marukhati Selectives**.

The text says:
- Marukh's prophecy foretold Silorn saving a drowning baby from Lake Rumare;
- Silorn later entered the ruins beneath Nenyond's priory looking for the missing **Nenyond** and **Manthar**;
- after several days, only Silorn's **skin** returned to the surface;
- the underground priory and excavated ruins were then sealed.

This gives Silorn a direct narrative bridge between the Selectives and the Nenyond/Manthar disappearance.

## Funeral Temple remains

The strongest ESM representation of Silorn after his disappearance is not the NPC form. It is the hanging-remains setup in **Funeral Temple**.

### Named corpse/container

`CONT 020D1A66` / `zzzCHAbbotSilornCorpse`:
- display name: **Abbot Silorn**
- model: `Clutter\AoM\Hangman\Hangedman01.nif`
- contains `ALCH 020E2593` / **Hide of Abbot Silorn**

Its placed reference `020D1A68` is inside the Funeral Temple.

### Hanged-man activators

`ACTI 02113B04` / `zzzCHFobbidenHangman`:
- display name: **Abbot Silorn**
- model: `Clutter\AoM\Hangman\Hangedman01Movable.nif`
- script: `CHForbiddenHangmanScript`

Two references of this activator are placed in the Funeral Temple.

Together, these records make the saint book's “only his skin returned” motif an explicit environmental sequence involving named hanging remains and the Hide relic.

## The InvisibleSpotter form

`NPC_ 02114115` has the display name **Abbot Silorn**, but its EditorID is `zzzCHInvisibleSpotter`.

Its placed reference `ACHR 0243A499` is also in Funeral Temple and links into a `zzzCHSightJacker` setup.

Because it:
- is explicitly an invisible spotter;
- has no unique dialogue;
- is not quest-owned as a normal Silorn character;
- is integrated with technical linked-reference machinery near the hanging-body setup;

Lorekeeper should treat it as **technical scene support**, not as evidence that Silorn survives or resurrects as an autonomous NPC.

This corrects the earlier, looser interpretation of the record as a “Silorn actor manifestation.”

## Hide of Abbot Silorn

`ALCH 020E2593` / **Hide of Abbot Silorn** grants an **Increase Stamina** effect.

The plugin also contains:
- `ACTI 020EA2BB` / `zzzCHRelicHideSilorn` — scripted relic trigger;
- `STAT 020EA2C1` / `zzzCHStaticRelicSilornLeather` — visible Silorn leather relic model.

The trigger awards the Hide relic through `CHAddRelicTriggerScript`.

### Reused relic placements

Paired Silorn-leather static/trigger placements occur in:
- Prison Tower;
- Slave Trader's House;
- Eastern Sewers;
- Old Temple of the Eight Divines;
- Fort Welkynd.

Therefore those five pickups are best treated as a **reusable gameplay relic system**, not five independent literal fragments of Silorn's historical skin.

The **Funeral Temple corpse containing the Hide** remains the strongest context-specific link to the saint biography.

## Silorn's Priory

The ESM separately implements:
- `CELL 02239B51` — **Silorn's Priory**
- `KEYM 020AEFE2` — **Silorn's Priory Key**
- `KEYM 0223B11C` — **Silorn's Priory Prison Key**

The traversal graph links Silorn's Priory to the Underground Lake/Wellspring route.

This is Silorn's own institutional site and should remain distinct from the Funeral Temple in Nenyond's complex.

## Current interpretation

The best-supported reconstruction is:

**Silorn enters the Nenyond ruins → later tradition says only his skin returned → Funeral Temple displays named hanging remains of Abbot Silorn → the named corpse contains Hide of Abbot Silorn.**

The ESM strongly supports the returned-skin motif but does not explain who mutilated Silorn, who arranged the remains, or whether the displayed body is literal history versus Coldharbour reconstruction.

A deeper record-level analysis is preserved at:

`analysis/silorn-returned-skin.md`

## Evidence limits

No INFO records currently resolve uniquely to Silorn.

The executable bodies of `CHForbiddenHangmanScript`, `CHSightJackScript`, and related external Papyrus scripts are not present in the ESM, so their exact runtime behavior cannot yet be asserted.

## Canon boundary

Silorn's Selective membership, prophetic rescue, search for Nenyond and Manthar, returned-skin fate, hanging-remains implementation, and relic system are `tes.mod.vigilant` material unless independently corroborated by licensed TES sources.
