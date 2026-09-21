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

## Dedicated boss quest

Caliburn has a dedicated encounter quest:

- `QUST 024F69BE` / `zzzCHBossQuestSelector` — **VS Selector**
- alias `Boss` → `NPC_ 0211C369` / **Arch-Selective Caliburn**
- local trigger `REFR 024F69BF` in **Malada Ageasel**

The boss alias advances the quest on:
- entering combat → stage 5;
- death → stage 10;
- later cell-detach cleanup → stage 20.

This confirms Caliburn is a deliberately staged Malada encounter rather than a loose placed NPC.

## The Great Gate

Caliburn's death list `LVLI 02129060` contains:

- `BOOK 020D429E` / **The Great Gate**

That book appears only in Caliburn's death list.

Its first-person narrator describes Marukh's holy corpse tracing the Seventy-Seven signs and opening a luminous breach. The gathered faithful are destroyed, the narrator's own body crumbles, and the destination beyond the light proves to be a barren wasteland rather than the expected paradise.

The record has no explicit author field, so Lorekeeper classifies it as **high-confidence Caliburn-associated first-person testimony**, likely Caliburn's voice but not formally author-tagged.

This materially sharpens the saint text's statement that Caliburn's Aetherius attempt “failed”: the ritual appears to have opened a breach, but not to the paradise the narrator expected.

Exact source text is preserved at:

`books/020D429E-the-great-gate.txt`

A detailed reconstruction is at:

`analysis/caliburn-great-gate.md`

## Stone-fragment handoff

The same Caliburn death list also contains:

- `BOOK 0211E0A5` / **Fragment of the Stone: Arch-Selective Caliburn**

That fragment leads to:
- `MGEF 0211E0A3` / **Conjure Arch-Selective Caliburn**
- `NPC_ 0211E0A2` / `zzzCHSummonSelector` — summonable **Arch-Selective Caliburn**

So the gameplay chain is:

**defeat Caliburn → recover his Great Gate testimony and Stone fragment → gain a summonable Caliburn form.**

This explains the post-defeat preservation mechanic, not the original historical transformation into the boss form.

## Interpretation

Caliburn is one of the clearest cases where *The Eight Saints of Cyrod*'s historical biography and the playable Coldharbour environment line up directly:

1. historical text ties Caliburn to Malada;
2. the plugin places his named boss identity in Malada Ageasel;
3. a Stone fragment preserves him as a summonable identity.

The ESM now gives a much clearer account of the failed gate: *The Great Gate* describes a ritual that opened a luminous breach and destroyed the faithful, but revealed a barren realm rather than the Aetherius paradise the narrator expected. What remains unresolved is the exact realm reached and how the historical Caliburn became the later boss/summon identity.

## Evidence limits

No INFO records currently resolve uniquely to Caliburn, so his ideology and motives should remain bounded by *The Eight Saints of Cyrod* and structural encounter evidence rather than reconstructed dialogue.

## Canon boundary

Caliburn's Selective role, attempted Aetherius gate at Malada, disappearance, and later boss/Stone-fragment manifestation are recorded as `tes.mod.vigilant` material unless separately corroborated by licensed Elder Scrolls sources.
