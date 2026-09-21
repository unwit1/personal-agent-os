# Caliburn

- Continuity: `tes.mod.vigilant`
- Historical role: founder and arch-member of the Marukhati Selectives
- Boss form: `NPC_ 0211C369` / `zzzCHBossSelector` — **Arch-Selective Caliburn**
- Summon form: `NPC_ 0211E0A2` / `zzzCHSummonSelector` — **Arch-Selective Caliburn**
- Placed boss reference: `ACHR 0211C36A`
- Encounter location: `CELL 0211BC4B` / **Malada Ageasel**
- Associated book: `BOOK 0211E0A5` / **Fragment of the Stone: Arch-Selective Caliburn**

## Saint tradition

`BOOK 020CB0DF` / *The Eight Saints of Cyrod* describes Caliburn as one of the founders of the **Marukhati Selectives** and says that even among the sect he was regarded as unusually fanatical.

The text says Caliburn:
- took Marukh's holy body to **Malada**;
- tried to open a gate to **Aetherius** there;
- failed;
- vanished together with hundreds of followers.

## VIGILANT implementation

The ESM turns Caliburn into an encounter identity:

- `0211C369` — **Arch-Selective Caliburn**, boss form;
- `0211E0A2` — summon version, templated from the boss;
- `0211C36A` — placed actor reference in **Malada Ageasel**;
- `0211E0A5` — *Fragment of the Stone: Arch-Selective Caliburn*, which grants/conveys the ability to conjure him.

The placement in Malada is significant because it independently reinforces the saint book's claim that Caliburn's final undertaking occurred there.

## Interpretation

Caliburn is one of the clearest cases where *The Eight Saints of Cyrod*'s historical biography and the playable Coldharbour environment line up directly:

1. historical text ties Caliburn to Malada;
2. the plugin places his named boss identity in Malada Ageasel;
3. a Stone fragment preserves him as a summonable identity.

What the ESM does **not** establish by itself is the exact mechanism by which Caliburn and his followers vanished, how his Aetherius attempt failed, or how the later boss/summon form relates metaphysically to the historical person.

## Evidence limits

No INFO records currently resolve uniquely to Caliburn, so his ideology and motives should remain bounded by *The Eight Saints of Cyrod* and structural encounter evidence rather than reconstructed dialogue.

## Canon boundary

Caliburn's Selective role, attempted Aetherius gate at Malada, disappearance, and later boss/Stone-fragment manifestation are recorded as `tes.mod.vigilant` material unless separately corroborated by licensed Elder Scrolls sources.
