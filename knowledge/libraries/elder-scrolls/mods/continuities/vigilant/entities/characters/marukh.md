# Marukh — VIGILANT continuity

- Continuity: `tes.mod.vigilant`
- NPC form: `0205ADEF` / `zzzCHMarukhMemory`
- Memory quests: *Adabal* and *Temptation of Marukh*

## Adabal

Marukh says he is carrying out seventy-seven secret rituals intended to restore the lost Stone of Al-Esh. He tells Dulsa that the ritual requires her blood and the blood of her unborn child. He describes the Stone as showing him a hero who will defeat the Aldmeri and bring peace, while admitting he cannot tell whether the vision is future or past.

Marukh later calls Adabal both miracle/emperor and "bread for the starving," then asks forgiveness from Dulsa and his nameless child. The phrase intersects strongly with Molag Bal's hunger/bread/salvation imagery elsewhere in VIGILANT, but that is a thematic link rather than proof of identity.

## Temptation

A Molag Bal memory-tail form appears in *Temptation of Marukh*, narrating thirst, memory loss, the Stone swallowing souls, and a confrontation in which submission and filling the Stone with souls are presented as escape. Memory alteration is explicitly mentioned, so the sequence carries strong reliability flags.

## Adabal state sequence

A focused record-level reconstruction is preserved at:

`analysis/marukh-adabal-ritual-sequence.md`

The ESM gives three same-model item states:

- `0205AE01` / **Red Stone** — alias `Adabal` in *Adabal*;
- `0206F543` / **Red Soul Gem** — alias `Stone` in *Temptation of Marukh*;
- `021353DF` / **Adabal** — late-game item physically carried by Molag Bal.

All three use `Clutter\AoM\Adabal.nif`.

The late-game transition is particularly strong structurally:

- Molag Bal carries `021353DF` / **Adabal**;
- his Aetherius actor is placed in Sancremor Angasel;
- `zzzCHAdabalSetTrigger` is placed in the same cell;
- that trigger references the exact Adabal item, sets the **Aetherius** quest to stage 40, and links to the Aetherius portal effect.

This makes the Molag Bal → Adabal → Aetherius-gate relationship structural rather than purely testimonial.

### Memory contradiction

The memory sequence is not a clean chronology.

*Remains of the Miracle* says the Stone had already been filled with millions of souls and stolen by Molag Bal.

The following *Temptation of Marukh* memory shows the **Red Soul Gem** still unfilled, while its `MolagBal` alias speaks in a Marukh-like personal voice and later offers to modify memory.

Lorekeeper should therefore preserve the contradiction as evidence of manipulated memory rather than “fixing” it into a single timeline.

## Evidence anchors

- `INFO 0205AE0A`–`0205AE15` — Marukh in *Adabal*
- `INFO 020708C9`–`020708DA`, `02073202`–`0207320A` — associated Molag Bal/memory-tail material

## Canon boundary

VIGILANT's Marukh/Adabal narrative remains mod continuity unless independently corroborated.
