# Silorn

- Continuity: `tes.mod.vigilant`
- Historical role: founder of the Marukhati Selectives; seeker of Nenyond and Manthar
- NPC form: `NPC_ 02114115` / `zzzCHInvisibleSpotter` — **Abbot Silorn**
- Placed reference: `ACHR 0243A499`
- Associated location: `CELL 02239B51` / **Silorn's Priory**
- Associated relic: `ALCH 020E2593` — **Hide of Abbot Silorn**

## Saint tradition

`BOOK 020CB0DF` / *The Eight Saints of Cyrod* describes Silorn as one of the founders of the **Marukhati Selectives**.

The text says:
- Marukh's prophecy foretold Silorn saving a drowning baby from Lake Rumare;
- Silorn later entered the ruins beneath Nenyond's priory looking for the missing **Nenyond** and **Manthar**;
- after several days, only Silorn's **skin** returned to the surface;
- the underground priory and excavated ruins were then sealed.

This gives Silorn a direct narrative bridge between the Selectives and the Nenyond/Manthar disappearance.

## VIGILANT implementation

The ESM preserves the skin motif unusually literally:

- `ALCH 020E2593` — **Hide of Abbot Silorn**;
- `ACTI 020EA2BB` — an activator also named **Hide of Abbot Silorn**;
- `CONT 020D1A66` — a container/corpse record named **Abbot Silorn** that contains the Hide relic.

Silorn also has:
- `NPC_ 02114115` — **Abbot Silorn**;
- `ACHR 0243A499` — a placed Silorn actor in **Funeral Temple**;
- `CELL 02239B51` — **Silorn's Priory**;
- `KEYM 020AEFE2` — **Silorn's Priory Key**;
- `KEYM 0223B11C` — **Silorn's Priory Prison Key**.

The Coldharbour traversal graph links **Silorn's Priory** to the Underground Lake route, while the placed Abbot Silorn reference occurs in the same Funeral Temple/Nenyond complex where Sorcerer Manthar is placed.

## Interpretation

Unlike Manthar, Silorn is not implemented primarily as a named boss identity. His strongest motif is the **returned skin/hide** from the saint story, which the ESM turns into a literal relic and corpse/container implementation.

That makes the “only his skin returned” episode one of the clearest examples of *The Eight Saints of Cyrod* being translated directly into environmental/gameplay objects.

## Evidence limits

No INFO records currently resolve uniquely to Abbot Silorn, so his motives and exact fate should not be expanded beyond the saint text and structural records.

## Canon boundary

Silorn's Selective membership, prophetic rescue, search for Nenyond and Manthar, returned skin, and VIGILANT relic forms are mod-continuity material pending separate licensed-source comparison.
