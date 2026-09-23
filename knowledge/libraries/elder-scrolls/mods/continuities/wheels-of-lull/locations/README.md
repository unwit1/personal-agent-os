# Wheels of Lull location index

Continuity: `tes.mod.wheels-of-lull`

This index is backed by the complete **33 LCTN / 103 CELL** implementation corpus. Cell names and XLCN ownership are direct plugin evidence; narrative interpretations remain in topic/quest dossiers.

## Major cell clusters

- **Boiling Foundry** — 15 CELL records: `051805C4` Boiling Foundry, Water Tank, `0515221E` Boiling Foundry, Heating Room, `051805C5` Boiling Foundry, Haptics Station, `0515221F` Boiling Foundry, Generator Room, `05152220` Boiling Foundry, Hall of Anor, +10 more
- **Stonehole Mine** — 12 CELL records: `05080DB8` Stonehole Mine, Minecart Alleys, `05080DB9` Stonehole Mine, Cavern, `05080DBA` Stonehole Mine, Canals, `05080DBB` Stonehole Mine, Old Shaft, `05080DBC` Stonehole Mine, Cart Station, +7 more
- **The Bottom Of The World** — 12 CELL records: `051E67E8` The Bottom of the World, Catacomb, `051E67E9` The Bottom of the World, Chasm, `051E67EA` The Bottom of the World, Tomb, `051EBB82` The Bottom of the World, Corridor, `051E67EB` The Bottom of the World, Arena, +7 more
- **The Brass Forest** — 10 CELL records: `0518AC2C` Brass Forest, Western Catacombs, `0518AC2D` Brass Forest, Winding Column, `0518AC2E` Brass Forest, Maze of Roots, `0518AC2F` Brass Forest, Tomb, `0518AC30` Brass Forest, Great Chasm, +5 more
- **The Cave** — 10 CELL records: `051F0EC8` The Cave, Subtract of Gyt, `051F0EC9` The Cave, Product of Rumur, `051F0ECA` The Cave, Fractal of Magnus, `051F0EC2` The Cave, Point of Nymar, `051F0EC3` The Cave, Hanlon's Vector, +5 more
- **Lull-Mor** — 5 CELL records: `050488A0` Lull-Mor, Elevators, `05248147` Ancient Tram Route, `05005900` Lull-Mor, Railroad Station, `0500AA4E` Lull-Mor, Upper Half, `0500AA4F` Lull-Mor, Bottom Half
- **Whitehorn Fortress** — 3 CELL records: `050C8A50` Whitehorn Labs, `050C8A4E` Whitehorn Fortress, `050C8A4F` Whitehorn Courtyard
- **Whitehorn Mines** — 3 CELL records: `0530AD18` Whitehorn Mines, `0530AD19` Whitehorn Mines, Reservoir, `0530AD1A` Whitehorn Mines, Boiler
- **Lull-Mor, Jail** — 2 CELL records: `05052FA4` Lull-Mor, Jail, `05000A88` Lull-Mor, Jail
- **Snow-Throat** — 2 CELL records: `05248146` Snow-Throat, `0536669E` Snow-Throat, Destroyed
- **Strange Shore** — 2 CELL records: `000098C0` LullStrangeShore, `000098A1` None
- **Underwater** — 2 CELL records: `05324779` Deep-sea Trenches, `0532477B` Deep-sea Downgate Station
- **Deep Sea Chronographer Station** — 1 CELL record: `05324778` Deep-Sea Chronographer Station
- **Disused Wailway Station** — 1 CELL record: `0504DF41` Disused Wailway Station
- **Sotha Sil** — 1 CELL record: `05248148` Sotha Sil, Dome of Sotha Sil

## Machine-readable

- `cell-index.json.gz` — all LCTN records plus all CELL records, including XLCN relationships and source offsets.
- `../normalized/retrieval-manifest.json` — retrieval materialization and routing policy.

The seven CELL records without an XLCN relationship are retained in the machine index rather than assigned a speculative parent location.
