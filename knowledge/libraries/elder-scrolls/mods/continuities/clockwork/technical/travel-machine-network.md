# Travel Machine network — record wiring

Continuity: `tes.mod.clockwork`

The Travel Room contains eleven destination selectors. Each placed button runs `CLWTravelMachineButton01Script`, enables exactly one transition/portal, and disables the other destinations. The city transitions are paired `XTEL` doors between the Travel Room and dedicated Terminus cells.

| Destination | Button ref | Plate angle | Enabled transition | Destination cell |
|---|---|---:|---|---|
| Dawnstar | `0503F513` | 30.0 | `0503C8E1` | `0503E755` — Dawnstar Clockwork Terminus |
| Falkreath | `0503F515` | 60.0 | `0503E1D9` | `050450B4` — Falkreath Clockwork Terminus |
| Markarth | `0503F518` | 90.0 | `0503E1DA` | `050456B7` — Markarth Clockwork Terminus |
| Morthal | `0503F516` | 120.0 | `0503E1DB` | `050462AE` — Morthal Clockwork Terminus |
| Raven Rock | `05006669` | 150.0 | `05006668` | `050065D4` — Raven Rock Clockwork Terminus |
| Recall Point | `0503F510` | 0.0 | `0503E1DD` | `050A842C` — Recall Point |
| Riften | `0503F50F` | 210.0 | `0503E1DE` | `050468EC` — Riften Clockwork Terminus |
| Solitude | `0503F517` | 240.0 | `0503E1DF` | `050485ED` — Solitude Clockwork Terminus |
| Whiterun | `0503F514` | 270.0 | `0503E1E0` | `050491CE` — Whiterun Clockwork Terminus |
| Windhelm | `0503F511` | 300.0 | `0503E1E1` | `05049DA1` — Windhelm Clockwork Terminus |
| Winterhold | `0503F512` | 330.0 | `0503E1E2` | `0504A9AF` — Winterhold Clockwork Terminus |

## Recall Point

Recall differs from the city network. Its selector enables `CLWTMRecallPortal01EnableParentREF` (`0503E1DD`). That parent enables `CLWDoorCastleTravelRoomToRecallDummy01REF` (`050A8537`), which teleports to `CLWRecallDummyToTravelRoomREF` (`050A8535`) in `CELL 050A842C` / **Recall Point**. The actual marked return position is managed separately by the Recall spell (`CLWRecallPointMarker02REF`).

## Raven Rock gating

The Raven Rock selector is the only button instance with `pRRButton = true`. Its script properties also reference `DLC2Init`, `CLWNotVisitedSolstheimMsg`, and `CLWRRButtonNotWorking01GLOB`. This is direct implementation evidence that Raven Rock is an optional Dragonborn/Solstheim destination with extra availability checks.

## Interpretation

This proves the Travel Machine is implemented as a selectable hub-and-spoke portal system. It does not, by itself, explain the in-universe physics of Dwemer teleportation.
