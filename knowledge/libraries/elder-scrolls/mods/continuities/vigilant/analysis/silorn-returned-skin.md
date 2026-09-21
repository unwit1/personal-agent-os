# Silorn and the returned skin

Continuity: `tes.mod.vigilant`

Primary source: user-provided `Vigilant.esm`

This pass asks whether VIGILANT treats Silorn as a surviving/undead person, a corpse, a relic, or a technical scene object after *The Eight Saints of Cyrod* says that only his skin returned from the ruins beneath Nenyond's priory.

## Historical starting point

`BOOK 020CB0DF` / *The Eight Saints of Cyrod* says Silorn:

- helped found the Marukhati Selectives;
- entered the ruins beneath Nenyond's priory searching for **Nenyond** and **Manthar**;
- failed to return normally;
- after several days, only his **skin** returned to the surface;
- the underground priory and excavated ruins were sealed afterward.

That is the only direct narrative explanation of Silorn's fate in the extracted book corpus.

## Funeral Temple corpse

The strongest physical implementation is:

- `CONT 020D1A66`
- EditorID: `zzzCHAbbotSilornCorpse`
- display name: **Abbot Silorn**
- model: `Clutter\AoM\Hangman\Hangedman01.nif`
- placed reference: `REFR 020D1A68`
- location: **Funeral Temple** (`CELL 021114AF`)

The corpse/container inventory includes:

- `ALCH 020E2593` — **Hide of Abbot Silorn**

This is direct record-level evidence that VIGILANT represents Silorn's remains as a hanging corpse/container carrying the named Hide relic.

The corpse reference is enable-parented to `REFR 02113B07`, but no quest or scene directly references the corpse record in the ESM. The runtime reason for its enable state therefore remains unresolved without external script context.

## Hanged Abbot Silorn activators

A second base record reinforces the hanging-body presentation:

- `ACTI 02113B04`
- EditorID: `zzzCHFobbidenHangman`
- display name: **Abbot Silorn**
- model: `Clutter\AoM\Hangman\Hangedman01Movable.nif`
- script: `CHForbiddenHangmanScript`

Two references of this activator are placed inside **Funeral Temple**:

- `REFR 02113B05`
- `REFR 021146CE`

Thus the ESM contains multiple explicitly named hanging-body representations of Silorn in the same complex that holds the named corpse/container.

The script body is external, so the exact animation/interaction logic cannot be asserted from the ESM alone.

## The “Abbot Silorn” NPC is technical, not strong resurrection evidence

The plugin also contains:

- `NPC_ 02114115`
- EditorID: `zzzCHInvisibleSpotter`
- display name: **Abbot Silorn**
- placed reference: `ACHR 0243A499`
- location: **Funeral Temple**

This record initially looks like a surviving actor form, but the internal implementation argues against reading it as a normal resurrected Silorn.

The NPC:

- is explicitly an **InvisibleSpotter** by EditorID;
- carries generic death/linked-reference/karma scripts;
- links to `ACTI 02114111` / `zzzCHSightJacker`;
- has no unique dialogue;
- is not quest-owned as a Silorn character;
- is spatially positioned near the scripted hanging-body setup.

Current interpretation: this is most likely **technical scene machinery used to support viewing/targeting the Silorn hanging-body sequence**, not evidence that Silorn survives as an autonomous NPC.

Lorekeeper should therefore downgrade the old “Silorn actor manifestation” inference.

## Hide of Abbot Silorn relic

The collectible relic is:

- `ALCH 020E2593`
- display name: **Hide of Abbot Silorn**
- effect: `MGEF 020E258F` / **Increase Stamina**

There is also:

- `ACTI 020EA2BB`
- EditorID: `zzzCHRelicHideSilorn`
- display name: **Hide of Abbot Silorn**
- script: `CHAddRelicTriggerScript`
- property: `RelicPotion -> 020E2593`

A matching static visual exists:

- `STAT 020EA2C1`
- EditorID: `zzzCHStaticRelicSilornLeather`
- model: `Clutter\AoM\Relics\SilornLeather.nif`

## Relic pickups are distributed, not unique to Silorn's tomb

Five paired static/trigger placements use the Silorn leather relic system in different Coldharbour interiors:

- **Prison Tower** (`020F9C21`)
- **Slave Trader's House** (`020B07D1`)
- **Eastern Sewers** (`020D6B49`)
- **Old Temple of the Eight Divines** (`020CB07C`)
- **Fort Welkynd** (`020E2693`)

Each pair combines the Silorn leather static with the scripted trigger that awards the Hide relic.

This matters for interpretation. The collectible Hide is implemented as a reusable relic-placement mechanic across several locations, so every Hide pickup should **not** be treated as another literal piece of Silorn's historical skin.

The Funeral Temple corpse carrying the Hide is the strongest context-specific implementation of the saint story.

## Silorn's Priory

Separate from the Funeral Temple, the plugin implements:

- `CELL 02239B51` — **Silorn's Priory**
- `KEYM 020AEFE2` — **Silorn's Priory Key**
- `KEYM 0223B11C` — **Silorn's Priory Prison Key**

The door/traversal graph places Silorn's Priory on the Underground Lake/Wellspring route.

This is Silorn's own institutional site, while the Funeral Temple is the Nenyond-complex site where his post-disappearance remains are represented.

The two should not be collapsed into one location.

## Current reconstruction

The strongest ESM-supported sequence is:

**historical Silorn enters the Nenyond ruins → saint text says only his skin returns → Funeral Temple contains named hanging-body/corpse representations of Abbot Silorn → the corpse contains Hide of Abbot Silorn**

That is much stronger than a resurrection reading.

## What remains unresolved

The ESM does not establish:

- what physically stripped Silorn's skin;
- whether the hanging corpse is literally his original body, a reconstructed body, or Coldharbour memory/environmental symbolism;
- who hung/displayed the remains;
- why multiple hanged-man representations exist in the Funeral Temple;
- the exact behavior of `CHForbiddenHangmanScript` or `CHSightJackScript`;
- whether the “skin returned” event happened exactly as the saint book records it.

Those questions require external Papyrus/PEX files, additional environmental interpretation, or deliberate acceptance of ambiguity.

## Current classification

**High-confidence historical Silorn → returned-skin tradition → Funeral Temple hanging-remains/relic implementation.**

The named `zzzCHInvisibleSpotter` NPC should be treated as **technical scene support**, not as independent evidence of a living or resurrected Abbot Silorn.
