# Travel Machine

Continuity: `tes.mod.clockwork`  
Topic type: Dwemer transportation technology

The Travel Machine is a large Dwemer teleportation device beneath Clockwork Castle. Ludwig says it was uncovered in 4E 23 and restored over roughly a decade with Gilded help. Lamashtu described it as a crossroads linked to remote **Terminus Machines**.

By 4E 33 Lahar could scout destinations and Ludwig briefly visited outside Markarth. It then became the castle's principal outside connection and supply route.

During the main quest, lost steam power first makes the machine mechanically nonfunctional. After repair, the machine itself works but the player is supernaturally prevented from leaving; Lamashtu later attributes that barrier to Shadow. After reunion, she teaches the player a Mark/Recall-like spell connecting a marked location and the Travel Machine.

## Core evidence

- `BOOK 05332EAA` — discovery, restoration, control map, successful destinations.
- `INFO 052C8526`, `052D78B5`, `052D78CD` — failure and later supply/trade use.
- `QUST 052908C1` — separates mechanical repair from supernatural blockage.
- `INFO 05679F5E` — Shadow blocks departure.
- `INFO 0578D466` — Mark/Recall-like spell.
- `INFO 057A18BD` — Raven Rock Terminus is temperamental.

## Exact implemented network

Record wiring shows the Travel Room as an eleven-selector hub. The nine Skyrim city destinations are Dawnstar, Falkreath, Markarth, Morthal, Riften, Solitude, Whiterun, Windhelm, and Winterhold; Raven Rock is a tenth remote Terminus, and Recall Point is the eleventh selector.

Each placed selector runs `CLWTravelMachineButton01Script` and enables one portal/door while disabling the others. The city/Raven Rock transitions are paired `XTEL` door references between the Travel Room and dedicated Terminus cells. Recall instead enables a hidden portal into `CELL 050A842C` / **Recall Point**, while the spell separately tracks the player's marked return position.

The Raven Rock selector alone carries the `pRRButton` flag and Dragonborn/Solstheim availability checks.

See `../technical/travel-machine-network.md` for the exact button, portal, return-door, cell, and plate-angle mapping.
