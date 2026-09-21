# Clockwork Terminus cells

Continuity: `tes.mod.clockwork`  
Location record: `LCTN 05046F70` / `CLWClockworkTerminusLocation`

The ESP defines individual Terminus cells:

| Destination | CELL | Editor ID |
|---|---|---|
| Dawnstar | `0503E755` | `CLWTerminusDawnstar` |
| Falkreath | `050450B4` | `CLWTerminusFalkreath` |
| Markarth | `050456B7` | `CLWTerminusMarkarth` |
| Morthal | `050462AE` | `CLWTerminusMorthal` |
| Riften | `050468EC` | `CLWTerminusRiften` |
| Solitude | `050485ED` | `CLWTerminusSolitude` |
| Whiterun | `050491CE` | `CLWTerminusWhiterun` |
| Windhelm | `05049DA1` | `CLWTerminusWindhelm` |
| Winterhold | `0504A9AF` | `CLWTerminusWinterhold` |
| Raven Rock | `050065D4` | `CLWDBTerminusRavenRock` |

Raven Rock therefore has a dedicated Dragonborn-aware Terminus cell rather than being only a dialogue reference. Dialogue separately notes that this Terminus is temperamental.

See `../topics/travel-machine.md`.

## Door-pair wiring

The Travel Room destination controls enable paired teleport doors. Each city/Raven Rock Travel Room door has an `XTEL` link to a return door inside the corresponding Terminus cell, and the return door links back to the Travel Room.

Recall Point is structurally different: the selector enables a portal-parent in the Travel Room, whose child door leads to a hidden `Recall Point` dummy cell. The Recall spell manages the actual marked return position separately.

See `../technical/travel-machine-network.md` for the full record graph.
