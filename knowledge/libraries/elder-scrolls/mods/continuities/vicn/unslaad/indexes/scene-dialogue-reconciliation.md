# SCEN dialogue reconciliation

Continuity: tes.mod.vicn.unslaad  
Primary source: translated Unslaad.esm 3.0.6

## Coverage result

The ESM contains **59 SCEN records**.

Deterministic SCEN parsing found:
- **53 scenes with DIAL-backed dialogue actions**
- **6 scenes with no DIAL dialogue actions**

Every DIAL-backed scene maps to a quest/dialogue family that has now been ingested or explicitly analyzed.

## Dialogue-bearing families

The 53 dialogue-bearing scenes belong to already-covered families:
- Hoarfrost
- When You Wish Upon a Star
- Long Winter
- Lingering Snow
- Boss Rush
- Stairway to Llesw'er
- The Owl Flies at Dusk
- Epilogue Scenes
- Liturgy of I
- Sermon of Khev
- VS Dreugh King
- The Final Journey
- Loveletter to the Fifth Era
- Under the Elder Tree

These scene mappings supplied important actor-alias evidence for Austella, Ulliss, Jhunal/Gray Owl, Ja'cobee, Lizz, Khev, Herkel, and the Woodland Man.

## Scenes without DIAL actions

The following six SCEN records contain no DIAL-backed dialogue actions in the direct parse:

- 03022976 — zzzCrbMq01Sc01
- 0312BE21 — zzzCrbSq02Sc01
- 0319BAB1 — zzzCrbMq05ScGhostWalk
- 03364E4A — zzzCrbSq04Sc01
- 0347299F — zzzCrbMq08ScDragonDisable
- 03493A06 — zzzCrbMq08ScWESHerkel

They may still orchestrate movement, packages, animation, conditions, or scripts, but they are **non-dialogue technical scenes**, not missing transcript material.

## Conclusion

At the SCEN/DIAL layer there is **no hidden scene-dialogue backlog** in the supplied ESM version.

Future SCEN work is therefore technical/narrative-orchestration analysis rather than additional dialogue discovery.

## Final scene status

**Complete:** all 59 SCEN records are accounted for at the dialogue-discovery layer.

No additional SCEN transcript ingestion is required for UNSLAAD 3.0.6. Future work on the six non-dialogue scenes would be optional orchestration/script analysis only.
