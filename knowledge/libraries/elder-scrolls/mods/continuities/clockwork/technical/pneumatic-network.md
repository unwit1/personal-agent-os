# Clockwork Castle pneumatic-tube and sorting network

Continuity: `tes.mod.clockwork`

The castle implements a real item-routing network around `Pneumatic Tube Receptacle` containers (`CLWPneumTubeContainer01`). VMAD properties on placed buttons identify source and destination receptacles directly.

## Receptacle endpoints

| Endpoint | Receptacle ref | CELL |
|---|---|---|
| Mage's Study | `0502A623` | `050261BA` — Clockwork Castle Mage's Study |
| Work Room | `05038845` | `05037757` — Clockwork Castle Work Room |
| Kitchen/Hall | `0503EFA5` | `0500196F` — Clockwork Castle Hall |
| Travel Room | `0503C987` | `0503C62F` — Clockwork Castle Travel Room |
| Armoury | `050347CD` | `050345A1` — Clockwork Castle Armoury |
| Master Bedroom (broken) | `05328BD2` | `05013ECF` — Clockwork Castle Master Bedroom |

## Remote routing

In Mage's Study, Work Room, Travel Room, Armoury, and the Hall/Kitchen terminal, transfer buttons can move receptacle contents to other network rooms. The corresponding sort buttons use FormLists to move only selected item categories.

Remote routing is gated by the same `CLWSQ02Machines01GLOB` machinery state used by the restored castle systems, so the network is tied to steam-power restoration rather than being an unrelated convenience.

## Master Bedroom terminal

The Master Bedroom has a Pneumatic Tube Receptacle (`05328BD2`) and a button based on `CLWImpButtonDwe01TransferBroken01`. Its placed script points toward the Kitchen/Hall receptacle but overrides the machinery check with `CLWConstant0GLOB` and uses `CLWBrokenButton01Msg`, making it deliberately nonfunctional.

## Local sorting stations

- **Alchemy Ingredients** — `0502C6AA` in Clockwork Castle Mage's Study.
- **Soul Gems** — `0531985C` in Clockwork Castle Mage's Study.
- **Food** — `0502CC24` in Clockwork Castle Hall.
- **Books** — `0502DC84` in Clockwork Castle Mage's Study.
- **Smithing Materials** — `05038DDD` in Clockwork Castle Work Room.

These local sorters route categories into nearby specialized containers/bookcases. They are separate from the room-to-room pneumatic transfer buttons.

## Narrative significance

The records substantiate Ludwig/Lahar descriptions of Clockwork Castle as highly automated domestic infrastructure: items can be moved between rooms without carrying them manually, while room-specific sorting systems automatically organize food, books, alchemical materials, soul gems, and smithing supplies. This is implementation support for the broader theme that the castle can remove ordinary reasons to move around or interact with others.
