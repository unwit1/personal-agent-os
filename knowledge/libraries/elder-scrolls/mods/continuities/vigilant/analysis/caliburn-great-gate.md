# Caliburn and the Great Gate

Continuity: `tes.mod.vigilant`

Primary source: user-provided `Vigilant.esm`

This pass asks how strongly the ESM connects **Arch-Selective Caliburn** to the failed Aetherius-gate episode described in *The Eight Saints of Cyrod*.

## Historical starting point

`BOOK 020CB0DF` / *The Eight Saints of Cyrod* says Caliburn:

- helped found the Marukhati Selectives;
- was unusually fanatical even by the sect's standards;
- brought Marukh's holy body to **Malada**;
- attempted to open a gate to **Aetherius**;
- failed;
- vanished together with hundreds of followers.

That is the saint-book summary.

## Dedicated encounter

Caliburn is not merely an unowned placed boss.

The ESM contains:

- `QUST 024F69BE` / `zzzCHBossQuestSelector` — **VS Selector**
- boss alias `Boss` → `NPC_ 0211C369` / **Arch-Selective Caliburn**
- `ACHR 0211C36A` / `CHBossSelectorRef`
- encounter location: `CELL 0211BC4B` / **Malada Ageasel**

A local trigger, `REFR 024F69BF`, is placed in the same Malada Ageasel cell and runs `defaultsetStageTrigSCRIPT` against the Caliburn boss quest.

The boss alias carries:
- `CHSetstageOnCombat` with next stage **5**;
- `defaultaliasondeathscript` with death stage **10**;
- `CHSetStageOnCellDetach` with stage **20** after the death-stage state.

The boss quest itself contains stages 0, 5, 10, 20, and 255.

This establishes a dedicated encounter lifecycle rather than an incidental spawn.

## Boss identity

`NPC_ 0211C369`:
- EditorID: `zzzCHBossSelector`
- display name: **Arch-Selective Caliburn**
- death list: `LVLI 02129060` / `zzzCHDeathItemSelector`
- boss ability: `SPEL 0211C36B` / **Selector Ability**
- placed in Malada Ageasel.

No INFO records resolve to Caliburn, so this encounter is primarily environmental/structural rather than conversational.

## The Great Gate

The most important new evidence is:

- `BOOK 020D429E` / **The Great Gate**
- EditorID: `zzzCHSelectorNote`

This book appears **only** in Caliburn's death-item list.

Its first-person narrator describes:

1. Marukh's holy corpse rising;
2. the corpse tracing the **Seventy-Seven signs**;
3. a luminous crack opening in reality;
4. the assembled faithful being reduced to ash;
5. the narrator's own limbs crumbling;
6. the narrator initially believing this to be the long-awaited Aetherius;
7. the revealed destination instead appearing as a barren, godless wasteland;
8. a subsequent rejection of the gods and a vow directed against the blood of Anu.

This is the clearest internal account of the event summarized in *The Eight Saints of Cyrod*.

### Authorship confidence

The BOOK record does **not** contain an explicit author name.

However:
- its EditorID is `zzzCHSelectorNote`;
- it occurs only in `zzzCHDeathItemSelector`;
- that death list belongs to **Arch-Selective Caliburn**;
- the first-person narrator describes being physically caught in the same gate event attributed to Caliburn.

Current classification: **high-confidence Caliburn-associated first-person testimony; likely Caliburn's voice, but not explicitly author-tagged by the ESM.**

Exact decoded text is preserved at:

`books/020D429E-the-great-gate.txt`

## What “failure” appears to mean

The saint text simply says Caliburn's attempt to open Aetherius **failed**.

*The Great Gate* complicates that.

The ritual appears to open **something**:
- light floods through;
- followers are destroyed;
- the narrator crosses/perceives beyond the breach.

But the destination does not match the narrator's expected paradise.

Therefore the strongest VIGILANT-specific reading is:

**Caliburn's ritual succeeded at opening a breach, but failed as an ascent to the Aetherius he expected.**

The ESM does not independently identify the wasteland by a named worldspace inside the BOOK record. It should not be automatically equated with a particular realm without further evidence.

## Death loot and Stone preservation

Caliburn's death list contains seven entries, including:

- `BOOK 020D429E` — **The Great Gate**
- `BOOK 0211E0A5` — **Fragment of the Stone: Arch-Selective Caliburn**
- `ALCH 020E2592` — **Ashes of St. Sard**
- `ARMO 021418AA` — **Orkey's Spell Clutch Ring**
- several master-game loot entries.

The unique combination of **The Great Gate** and Caliburn's Stone fragment makes the boss loot itself a lore handoff:
- one item supplies the failed-gate testimony;
- the other preserves Caliburn as a summonable Stone identity.

## Summon chain

`BOOK 0211E0A5` / **Fragment of the Stone: Arch-Selective Caliburn** grants the Caliburn conjuration.

The corresponding effect is:
- `MGEF 0211E0A3` / **Conjure Arch-Selective Caliburn**

It summons:
- `NPC_ 0211E0A2` / `zzzCHSummonSelector` — **Arch-Selective Caliburn**

The summon NPC is templated from the boss identity.

This makes the post-defeat sequence:

**Caliburn boss → Stone fragment → summonable Caliburn**

As with Manthar, this explains the gameplay preservation of the encounter identity, not the historical mechanism that produced the boss form.

## Current reconstruction

The combined evidence supports:

**Caliburn brings Marukh's body to Malada → a ritual using the Seventy-Seven signs opens a luminous breach → followers and narrator are reduced to ash → the perceived destination is not the promised paradise → Caliburn later exists as the named Malada boss → his Stone fragment preserves a summonable form.**

The exact metaphysical relation among:
- Marukh's corpse;
- the Seventy-Seven signs;
- the opened breach;
- the wasteland beyond;
- Caliburn's later boss form;
- the Stone fragment;

is not fully resolved at ESM-record level.

## Reliability

- **A:** Caliburn boss identity, Malada placement, boss quest, loot, Stone fragment, summon chain.
- **B/C:** *The Great Gate* as Caliburn-associated first-person testimony.
- **C:** *The Eight Saints of Cyrod* historical summary.
- **Unresolved:** exact realm reached and precise metaphysical cause of Caliburn's later manifestation.

## Canon boundary

The Caliburn/Great Gate reconstruction belongs to `tes.mod.vigilant`. It should not be promoted into base TES history without separate licensed-source evidence.
