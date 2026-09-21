# Package/state choreography

Continuity: `tes.mod.clockwork`

This page resolves selected story-relevant `PACK` targets through placed-reference CELL context.

## Shadow tunnel route

`CLWShadowManage01Quest` uses stage-named packages whose target markers establish the haunting's internal route:

| Internal stage | PACK | Target CELL |
|---:|---|---|
| 10 | `0506FCE5` | `05063DB9` — Velothi Mountain Tunnels |
| 20 | `0506FCE7` | `05063DB9` — Velothi Mountain Tunnels |
| 30 | `05073A4C` | `05063DB9` — Velothi Mountain Tunnels |
| 40 | `0507F7B9` | `05079DDF` — Velothi Tunnels - Bone Hollow |
| 50 | `0507F7BD` | `05079DDF` — Velothi Tunnels - Bone Hollow |

The package CTDA data points back to `QUST 0506FCE4` and uses stage-comparison values matching those package names. Combined with the quest VMAD's Shadow alias and slow-time spell, this gives a record-backed route for the pre-castle haunting.

During *I Against I*, `PACK 05764B53` / `CLWShadowSQ04Stage20Package` targets marker `05764B52` inside `CELL 053566B7` / **Clockwork Castle Mausoleum**, tying Shadow's renewed movement to the party's descent back toward Nurndural.

## Gilded introduction

The three choreography packages for `SCEN 05384489` target markers `05384486`, `05384487`, and `05384488`. All three markers are placed in:

`CELL 0537A08F` / **Nurndural - Hall of Elements**

Therefore the seven Gilded01/02/03 lines resolved by the SCEN pass are also location-resolved to the Hall of Elements.

## Can't-leave sequence

`PACK 054F7876` targets `REFR 054F7873` / `CLWSQ02CantLeave01PlayerMark01REF`, which is placed in:

`CELL 0503C62F` / **Clockwork Castle Travel Room**

This structurally locates the scripted “cannot leave” sequence at the Travel Machine rather than merely inferring it from journal prose.

## Amalgam retreat

Both `CLWSQ03Stage70Scene01AmalgamMark01Package` and `CLWAmalgamSQ03Stage80Package` target `REFR 0559A4B2`, placed in:

`CELL 0552F496` / **Nurndural - Sickness Ward**

This complements the Amalgam VMAD evidence for the paralysis/teleport/portcullis retreat.
