# DAc0da worldspace / location index

**Continuity:** `tes.mod.vicn.dac0da`  
**Source:** `DAc0da.esm`

## Worldspaces

DAc0da defines or directly uses five WRLD records:

| Source | Editor ID | Name | Role |
|---|---|---|---|
| `DAc0da.esm:00003C` | `Tamriel` | Skyrim | base-game exterior used for entry/return anchors |
| `DAc0da.esm:037EDF` | `SolitudeWorld` | Solitude | base-game city world used by the Solitude/lighthouse framing |
| `DAc0da.esm:000DBB` | `zDcdGhostSea` | **Sea of Causality** | primary DAc0da exterior/adventure world |
| `DAc0da.esm:0097E3` | `zDcdDwemereth` | **Dwemereth** | Numidium/Dwemer machine-world exterior |
| `DAc0da.esm:00B765` | `zDcdBlindRealm` | **Mozarella Spacetime** | alternate/censorship realm used by Sheogorath/Rella-Mozzarella material |

The three custom worlds are distinct records and should be indexed independently rather than treated as one continuous exterior.

---

# Sea of Causality

**WRLD:** `DAc0da.esm:000DBB` / `zDcdGhostSea`

The world contains thousands of exterior CELL records because the worldspace grid is explicitly represented, but approximately two hundred cells carry meaningful custom EditorIDs. Those IDs form recognizable narrative regions.

## Ship Graveyard

Primary prefix: `DcdShGr*`  
Named-cell cluster: about **41** custom cells.

Important anchors:

- Samon placed actor `DAc0da.esm:004471` is in `DcdShGrA01`.
- the golden dragon actor `DAc0da.esm:004472` is in the same Ship-Graveyard route layer;
- N'Danda's encounter resolves near `DcdShGrEnd01`;
- the MQ01 Agent/falling-Agent encounter also belongs to this world layer.

Narrative use:

- **The Sea of Causality**
- Akashiya-Samon introduction
- Sload/N'Danda encounter
- Yaghra Agent event
- golden-dragon flight hook

## Road to Coral / Coral Reef Road

Prefixes:

- `DcdRoadToCoral*`
- `DcdCoralReefRoad*`

Vanus Galerion's placed actor `DAc0da.esm:00524F` anchors at `DcdRoadToCoral01`.

Yu'qbar's placed actor `DAc0da.esm:005300` anchors at `DcdCoralReefRoad02`.

This forms the opening approach to the **Echoes of Mnemolichite** side arc.

## Frost Sea

Primary prefix: `DcdFrostSea*`  
Named-cell cluster: about **30** cells.

Haalj Hgelhelmson's placed actor `DAc0da.esm:004B20` resolves to `DcdFrostSeaCEND`.

Narrative use:

- later **Drowned Nighthawk** route
- temporally displaced Atmoran material

## Forelgrim

Primary prefix: `DcdForelgrim*`  
Named-cell cluster: about **28** cells.

This is a large contiguous Atmoran/Yngol-route region adjacent to Frost Sea and the Harakk/Jylkurfyk sequence.

## Harakk

Prefixes:

- `DcdHarakk*`
- `DcdRoadToHarakk*`

Named-cell cluster: about **17** Harakk cells plus approach cells.

Yngol and Hgelhelm initially share placed cell `DcdHarakkShip`.

Narrative use:

- **Drowned Nighthawk**
- Yngol's dream/awakening
- Hgelhelm encounter
- later Harakk/stardust endpoint language

## Jylkurfyk

Prefixes:

- `DcdJylkurfyk*`
- `DcdRoadJylkurfyk*`

Named-cell cluster: at least **10** direct/approach cells.

Sindwen the Wintercaller is placed in `DcdJylkurfyk05`.

Narrative use:

- contested Atmoran/Snow-Elf history
- Wintercaller attack
- anti-elven purge testimony
- Yngol/Sindwen confrontation
- 500 Companions / Atmoran civil-war memory layer

## Kalpic Ship

Primary prefix: `DcdKalpicShip*`  
Named-cell cluster: about **11** cells.

Tsuunalinfaxtir is placed in `DcdKalpicShip03`.

The cluster includes a distinct `DcdKalpicShipTotem` cell, reinforcing the old-kalpa/dragon-transformation route.

## Yaghra Beds and Yaghra Caves

Prefixes:

- `DcdYaghraBed*`
- `DcdYaghraCave*`

Named-cell clusters:

- about **25** Yaghra-Bed cells;
- about **12** Yaghra-Cave cells.

Vigilant Athanasius is placed at `DcdYaghraCaveEND`.

Narrative use:

- Sload/Yaghra experimentation
- Echoes of Mnemolichite
- wounded/survivor branch
- transition toward Sload research layers

## Neuron Cave

Primary prefix: `DcdNeuronCave*`  
Named-cell cluster: about **10** cells.

This route sits in the same Sload/Yaghra research geography and leads toward Neo-Thras.

## Neo-Thras

Primary prefix: `DcdNeoThras*`  
Named-cell cluster: about **14** cells, including:

- `DcdNeoThrasStart`
- `DcdNeoThrasCapital`
- several `Sub*` cells

Narrative use:

- Sload capital
- Echoes of Mnemolichite
- Group Battle: The Sload City
- Sload research/necromancer infrastructure

## Dragontail Isle

Primary prefix: `DcdDragontaileIsle*`  
Named-cell cluster: about **7** cells.

This is part of the late Echoes-of-Mnemolichite route toward the ritual/God-of-Worms confrontation.

## Revenant Gate

Primary prefix: `DcdRevenantGate*`  
Named-cell cluster: about **6** cells.

Mannimarco / God-of-Worms actor `DAc0da.esm:005FA2` is placed in `DcdRevenantGate04`.

Narrative use:

- **Group Battle: The Revenant**
- Mannimarco / God of Worms manifestation
- final necromancer/portal confrontation

## Zurin Island

Primary prefix: `DcdZurinIsland*`  
Named-cell cluster: about **9** cells.

This is associated with the Zurin/Underking temporal-displacement material from the early-middle main quest.

## Cheese Party cells inside Sea of Causality

Two cells use:

- `DcdCheeseParty01`
- `DcdCheeseParty02`

These are separate from the interior cell named **Cheese Party** and should not be conflated with Mozarella Spacetime.

---

# Dwemereth

**WRLD:** `DAc0da.esm:0097E3` / `zDcdDwemereth`  
**Name:** Dwemereth

About **35** exterior cells have meaningful custom EditorIDs.

## Regional cell families

- `DcdDwemerethStart`
- `DcdDwemerethCL*`
- `DcdDwemerethCU*`
- `DcdDwemerethNE*`
- `DcdDwemerethNW*`
- `DcdDwemerethNw*`
- `DcdDwemerethSe*`
- `DcdDwemerethSw*`
- `DcdMantellaTower01`–`06`

## Narrative role

Dwemereth is the exterior machine-world layer associated with the **Numidium Tertius** portion of DAc0da.

The six-cell **Mantella Tower** cluster is especially important because the MQ04/Mantella/Underking material explicitly revolves around the Mantella replacement-heart system.

## Boss / actor anchors

DAc0da's major Numidium actors also resolve into named Numidium interiors connected to this broader Dwemereth machine-world:

- GC9 / O.Y.A.R.S.A -> **Numidium Vena**
- Arcanist -> **Numidium Iecur**
- Zurin Arctus -> **Numidium Vena Cava**
- Dumac's Tonalframe -> **Mantella Tower 01**

These actor placements make the machine anatomy literal in level structure rather than merely metaphorical dialogue.

---

# Mozarella Spacetime

**WRLD:** `DAc0da.esm:00B765` / `zDcdBlindRealm`  
**Name:** Mozarella Spacetime

Named exterior cells:

- `DcdBlindStart`
- `DcdBlindRealm01`
- `DcdBlindRealm02`
- `DcdBlindRealm03`
- `DcdBlindRealm04`
- `DcdBlindRealm05`
- `DcdBlindRealm06`
- `DcdBlindRealm07`
- `DcdBlindRealm08`

Sheogorath `DAc0da.esm:00C994` and the Rolls-On-Roads fragment/bit form `DAc0da.esm:00C995` are both placed in `DcdBlindRealm07`.

Narrative use:

- **Rella Mozzarella**
- Jillian censorship/consumption
- collapsing half-plane
- Sheogorath-assisted escape
- Rolls-On-Roads being bitten/devoured by the Jills

This world should be treated as a branch/alternate-ending space rather than part of the ordinary Sea-of-Causality geography.

---

# Important interior cells

Several named interiors are not exterior cells of the three custom WRLD grids and therefore deserve separate indexing.

| Source | Editor ID | Display name | Narrative role |
|---|---|---|---|
| `DAc0da.esm:004602` | `zDcdTharnShip` | Tharn's Hideout | Abnur Tharn side quest |
| `DAc0da.esm:0047B4` | `zDcdObscureRoom` | Room of the Obscure | Augur material |
| `DAc0da.esm:004802` | `zDcdSloadHideout` | Divine Pineal Laboratory | Sload research |
| `DAc0da.esm:00626C` | `zDcdNumidium01` | Numidium Cavitas | Numidium interior |
| `DAc0da.esm:006BEC` | `zDcdNumidium02` | Numidium Arteria | Numidium interior |
| `DAc0da.esm:00738C` | `zDcdNumidium03` | Numidium Vena | Ghost Choir/O.Y.A.R.S.A placement |
| `DAc0da.esm:0079A3` | `zDcdNumidium04` | Numidium Iecur | Arcanist placement |
| `DAc0da.esm:008B08` | `zDcdNumidium05` | Numidium Diaphragm | Numidium interior |
| `DAc0da.esm:009658` | `zDcdNumidium06` | Numidium Vena Cava | Zurin Arctus placement |
| `DAc0da.esm:009680` | `zDcdNumidium07` | Numidium Neural Circuit | Numidium interior |
| `DAc0da.esm:006182` | `zDcdNumidiumEND` | Numidium Cockpit | late Numidium route |
| `DAc0da.esm:008B0C` | `zDcdNumidiumAnus` | Anu[s]midium | anomalous Numidium interior |
| `DAc0da.esm:00CCEC` | `zDcdCheeseParty` | Cheese Party | Sheogorath side material |

## Retrieval guidance

Location queries should retrieve:

1. the worldspace/location page;
2. quests known to occupy that region;
3. actors with direct placed-reference anchors in that region;
4. relevant written lore tied to the same place.

Do not infer exact geography from EditorID adjacency alone when no actor/quest/reference anchor has been resolved.
