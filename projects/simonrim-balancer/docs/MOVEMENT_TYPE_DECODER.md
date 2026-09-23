# MOVT Movement-Type Decoder

## Scope

This checkpoint decodes the 12 `MOVT` records supplied by Blade and Blunt 4.0.3 using the documented TES5/SSE layout.

- `SPED`: 44 bytes / 11 floats for directional walking/running and rotational movement.
- `INAM`: 12 bytes / 3 floats for animation-change thresholds.
- `MNAM`: simplified movement-type name.

The authoritative raw record/subrecord payloads remain preserved separately.

## Results

- 12 / 12 MOVT records decoded; 0 failures.
- 8 distinct exact numeric profiles.
- 2 exact profiles repeat across at least three movement states.
- `NPC_Default_MT`, `NPC_1HM_MT`, and `NPC_2HM_MT` share one exact profile.
- `NPC_Attacking_MT`, `NPC_Attacking2H_MT`, and `NPC_PowerAttacking_MT` share another exact profile.
- Every supplied `INAM` threshold slot is the IEEE float-max sentinel (`~3.4028235e38`).

Derived run/walk ratios and radians-to-degrees rotation conversions are convenience projections only; raw floats remain the evidence.

## Critical limitation

All 12 records resolve as overrides of `Skyrim.esm`, whose MOVT record bodies are not present in this snapshot. Therefore this pass records **absolute Blade and Blunt movement evidence only**. It does not claim which values differ from vanilla, by how much, or why. Those comparisons become valid only after the corresponding Skyrim master records are ingested.

## Rule status

No movement observation is an approved Simonrim rule. Repeated profiles are `observed_pattern` evidence and must be reviewed with vanilla deltas, author documentation, animation behavior, and exceptions before promotion.
