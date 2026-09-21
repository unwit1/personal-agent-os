# DAc0da worldspace / location index

**Continuity:** `tes.mod.vicn.dac0da`  
**Source:** `DAc0da.esm`

This index separates **narrative place names** from raw CELL implementation names.

DAc0da contains three custom WRLD records:

| Source | Editor ID | Displayed name |
|---|---|---|
| `DAc0da.esm:000DBB` | `zDcdGhostSea` | **Sea of Causality** |
| `DAc0da.esm:0097E3` | `zDcdDwemereth` | **Dwemereth** |
| `DAc0da.esm:00B765` | `zDcdBlindRealm` | **Mozarella Spacetime** |

The plugin also uses Skyrim/Solitude world records, but the three records above are DAc0da-defined world layers.

## Sea of Causality

The Sea of Causality world uses a full exterior grid, but only a minority of cells are assigned to named DAc0da locations. The named LCTN records are the preferred narrative labels.

### Main MQ01 / ship-graveyard region

| LCTN | Displayed name | Cells | Structural significance |
|---|---|---:|---|
| `0013FD` | **Talos' Regrets** | 1 | initial Sea of Causality entry/start region |
| `0013FB` | **Ship Graveyard** | 14 | southern graveyard sector; Akashiya-Samon is placed here |
| `0013FC` | **Ship Graveyard** | 9 | central graveyard sector |
| `0013FE` | **Ship Graveyard** | 15 | northern/transition graveyard sector |
| `001412` | **Ship Graveyard** | 3 | end/boss sector; N'Danda and the MQ01 Agent are placed here |
| `000F88` | **Fox Rocks** | 9 | Zurin/Underking-associated island region |

Actor anchors:

- Akashiya-Samon -> cell `DcdShGrA01` in Ship Graveyard.
- N'Danda -> `DcdShGrEnd01` in Ship Graveyard.
- MQ01 **The Agent** -> the same `DcdShGrEnd01` boss/end cell.

This makes the Ship Graveyard a concrete convergence point for Samon's arrival, Sload activity, and the Daggerfall-coded Agent event.

### Drowned Nighthawk / Atmora region

| LCTN | Displayed name | Cells | Structural significance |
|---|---|---:|---|
| `001CA5` | **Road to the Fallen Star** | 2 | transition toward Harakk |
| `00168C` | **Stranded Harakk** | 17 | Yngol / Hgelhelm opening region |
| `00168D` | **Shivering Glacier** | 4 | road toward Jylkurfyk |
| `00168E` | **Jylkurfyk** | 6 | Atmoran port; Sindwen encounter |
| `001E51` | **Jylkurfyk Dock** | 9 | port/dock layer |
| `001E52` | **Jylkurfyk Defense Line** | 12 | fortified frozen line |
| `001E53` | **Jylkurfyk Checkpoint** | 9 | Haalj / later Yngol state |
| `001C08` | **Hare Mound** | 6 | Atmoran route node |
| `002FE6` | **Forelgrim** | 19 | large Atmoran exterior region |
| `003012` | **Forelgrim** | 9 | Forelgrim continuation/end region |
| `003038` | **Crash Site** | 11 | final Yngol/Tsuunalinfaxtir region |

Actor anchors:

- Yngol + Hgelhelm the Outcast -> `DcdHarakkShip`, **Stranded Harakk**.
- Sindwen the Wintercaller -> `DcdJylkurfyk05`, **Jylkurfyk**.
- Haalj Hgelhelmson + second Yngol state -> `DcdFrostSeaCEND`, **Jylkurfyk Checkpoint**.
- third Yngol state -> `DcdKalpicShip03`, **Crash Site**.
- Yngol the Tsunaltir -> `DcdKalpicShip06`, **Crash Site**.
- Tsuunalinfaxtir -> `DcdKalpicShip03`, **Crash Site**.

The location layout independently confirms that Drowned Nighthawk physically progresses from the stranded Harakk/Jylkurfyk conflict into the later Crash Site transformation/climax.

### Echoes of Mnemolichite / Sload region

| LCTN | Displayed name | Cells | Structural significance |
|---|---|---:|---|
| `003677` | **Necromantic Beach** | 6 | Vanus entry region |
| `00371E` | **Thrassian Critical Reef** | 2 | Yu'qbar / Dreugh route |
| `00371F` | **Yaghra Breeding Ground** | 11 | Yaghra complex sector A |
| `003720` | **Yaghra Breeding Ground** | 8 | Yaghra complex sector B |
| `005938` | **Yaghra Breeding Ground** | 6 | Yaghra complex sector C |
| `005C94` | **Disposal Cave** | 6 | cave sector A |
| `0037BF` | **Disposal Cave** | 6 | cave sector B; Athanasius placement |
| `003D8A` | **Ul'voric 2nd Neural Corridor** | 10 | Sload/Ul'vor Kus neural corridor |
| `00426E` | **Road to Neo-Thras** | 2 | Abnur route toward Sload capital |
| `004270` | **Neo-Thras** | 9 | main Sload city/capital layer |
| `004271` | **Neo-Thras** | 5 | sub/capital extension |
| `004276` | **Dragontail Isle** | 7 | later ritual-route island |
| `0039B1` | **Worm Hole** | 6 | Mannimarco / God-of-Worms climax |

Actor anchors:

- Vanus Galerion -> `DcdRoadToCoral01`, **Necromantic Beach**.
- Yu'qbar -> `DcdCoralReefRoad02`, **Thrassian Critical Reef**.
- Vigilant Athanasius -> `DcdYaghraCaveEND`, **Disposal Cave**.
- Abnur's second form -> `DcdRoadToThras01`, **Road to Neo-Thras**.
- Mannimarco the God of Worms -> `DcdRevenantGate04`, **Worm Hole**.
- Necromancer's Moon -> `DcdRevenantGate00`, **Worm Hole**.

This gives the Worm arc a clear physical progression from necromantic coast/reef through Yaghra/Sload processing regions into Neo-Thras and finally the Worm Hole ritual/boss layer.

## Dwemereth

**WRLD:** `DAc0da.esm:0097E3` / `zDcdDwemereth`  
**Displayed name:** **Dwemereth**

Dwemereth is a separate exterior-style world used for the late Numidium/Mantella layer.

Its named cells form a compact custom region:

- `DcdDwemerethStart`
- central (`CU*`)
- northeast (`NE*`)
- southeast (`Se*`)
- southwest (`Sw*`)
- northwest (`Nw*`)
- a six-cell **Mantella Tower** cluster:
  - `DcdMantellaTower01`
  - `02`
  - `03`
  - `04`
  - `05`
  - `06`

**Dumac's Tonalframe** is physically placed in `DcdMantellaTower01`.

The location therefore acts as the exteriorized late-Numidium/Mantella battlefield rather than an ordinary province called Dwemereth.

### Numidium interiors associated with this route

DAc0da also defines named interior CELL/LCTN pairs:

| CELL | LCTN / displayed name | Major anchor |
|---|---|---|
| `zDcdNumidium01` | **Numidium Cavitas** | Nchunak the Evangelist |
| `zDcdNumidium02` | **Numidium Arteria** | interior route |
| `zDcdNumidium03` | **Numidium Vena** | GC9 and O.Y.A.R.S.A |
| `zDcdNumidium04` | **Numidium Iecur** | Arcanist |
| `zDcdNumidium05` | **Numidium Diaphragm** | interior route |
| `zDcdNumidium06` | **Numidium Vena Cava** | Zurin Arctus |
| `zDcdNumidium07` | **Numidium Neural Circuit** | upper machine route |
| `zDcdNumidiumEND` | **Numidium Cockpit** | late control/end layer |
| `zDcdNumidiumAnus` | **Anu[s]midium** | separate named Numidium interior |

The anatomical naming—Cavitas, Arteria, Vena, Iecur, Diaphragm, Vena Cava, Neural Circuit—reinforces Rolls-On-Roads' dialogue describing Numidium's passages as analogous to vascular/bodily systems.

## Mozarella Spacetime

**WRLD:** `DAc0da.esm:00B765` / `zDcdBlindRealm`  
**Displayed name:** **Mozarella Spacetime**

This world contains nine named central cells:

- `DcdBlindStart`
- `DcdBlindRealm01`
- `DcdBlindRealm02`
- `DcdBlindRealm03`
- `DcdBlindRealm04`
- `DcdBlindRealm05`
- `DcdBlindRealm06`
- `DcdBlindRealm07`
- `DcdBlindRealm08`

Placed actor evidence includes:

- alternate Sheogorath form -> `DcdBlindRealm07`
- bitten/alternate Rolls-On-Roads -> `DcdBlindRealm07`
- multiple **Jill** actors in surrounding cells

This is the world layer used by the Jillian-censorship / Rella Mozzarella alternate-ending material.

Its internal EditorIDs call it the **Blind Realm**, while the WRLD display name presented to the player is **Mozarella Spacetime**. Both names should be retained:

- **Mozarella Spacetime** = game-facing world name
- **Blind Realm** = implementation/editor namespace

## Important standalone interiors

DAc0da also defines several lore-relevant custom interiors outside the three exterior world layers:

- **Tharn's Hideout** — `zDcdTharnShip`
- **Dozing Rat Inn** — `zDcdDozingRatInn`
- **Room of the Obscure** — `zDcdObscureRoom`
- **Divine Pineal Laboratory** — `zDcdSloadHideout`
- **Cheese Party** — `zDcdCheeseParty`
- **Actor Room** — `zDcdActorRoom` (staging/support cell; includes Rolls-On-Roads forms)

These should not automatically be treated as exterior regions of the Sea of Causality merely because their quests connect to that story.

## Retrieval rule

For location-sensitive lore queries, retrieve:

1. the **LCTN display name**;
2. the underlying CELL/WRLD evidence;
3. the quest/actor evidence that anchors the narrative there.

Do not infer geography between distinct worldspaces solely from adjacent quest stages or teleport transitions.
