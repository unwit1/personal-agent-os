# Ambiguous Gilded ambient dialogue

Continuity: `tes.mod.clockwork`  
Records: **519**

These INFO records resolve to the broad Gilded actor pool rather than one named NPC. They are therefore retained as **collective/ambient Gilded dialogue evidence** and must not be attributed to Lahar, Lamashtu, Amalgam, or another individual without additional record-level evidence.

## Topic counts

- `CLWDGTaunt` — 46 INFO records
- `CLWDGSharedInfo` — 46
- `CLWDGIdle` — 46
- `CLWDGALertToCombat` — 46
- `CLWDGAlertToNormal` — 46
- `CLWDGCombatToLost` — 46
- `CLWDGCombatToNormal` — 46
- `CLWDGLostToCombat` — 46
- `CLWDGNormalToAlert` — 46
- `CLWDGNormalToCombat` — 46
- `CLWDGLostToNormal` — 38
- no editor ID — 7
- `CLWDGAttack` — 6
- `CLWDGHit` — 5
- `CLWDGDeath` — 3

Most of this layer is combat/state-transition/idle material. The exact response text and INFO provenance remain preserved in the full raw dialogue corpus at `../raw/dialogue-transcript.txt.gz`; the normalized resolver statistics are in `../normalized/resolution-stats.json`.
