# Menta-Na

- Continuity: `tes.mod.vigilant`
- Primary NPC: `020B76F1` / `zzzCHBossMentana`
- Summon form: `02110C6E` / `zzzCHSummonMentana`
- Main-quest alias: `zzzCHMQ00` alias 6, `Mentana`
- Boss quest: `024F69B6` / **VS Menta-Na**
- Placed boss reference: `020B76F2` in `CELL 0206DE3D` / `CHVarlaGate01`

## Role in Coldharbour

Menta-Na is structurally bound into the main **Coldharbour** quest and has a dedicated boss quest. Inquisitor Pepe describes Menta-Na as a Daedroth that learned to fly and says he devours people attempting to leave the Waterfront District. This is Pepe's testimony about the creature; the boss form, alias, and encounter quest independently establish that Menta-Na is a concrete Act 4 encounter.

The boss is placed at `CHVarlaGate01`, tying the encounter spatially to the route toward Varla-controlled territory.

## Boss-state mechanics

`VS Menta-Na` has a dedicated quest-fragment file `QF_zzzCHBossQuestMentana_024F69B6`. The boss alias carries deterministic ESM scripts:

- entering combat advances the boss quest to stage **5**;
- Menta-Na's death advances it to stage **10**;
- detaching the cell after stage 10 advances it to stage **20**.

The exact Papyrus statements in the stage fragments remain external to the ESM.

## Evidence anchors

- `INFO 0212F2EE` — Pepe's account of Menta-Na.
- `QUST 0212F24E` — Menta-Na as main-quest alias.
- `QUST 024F69B6` — dedicated boss state machine.
- `ACHR 020B76F2` — physical encounter placement.
