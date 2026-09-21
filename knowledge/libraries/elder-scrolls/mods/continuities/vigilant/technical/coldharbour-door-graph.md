# Coldharbour door/traversal graph

Continuity: `tes.mod.vigilant`

This graph is derived from VIGILANT `REFR` records whose base object is a `DOOR` and which contain an `XTEL` teleport destination. Source and destination cells are recovered from the plugin's CELL child-group hierarchy.

## Coverage

- **272** teleporting door references are present in the plugin.
- **240** touch the Coldharbour cell/worldspace set.
- **87** unique non-self cell pairs occur in the current Coldharbour-focused graph.
- The large unnamed exterior cell `02072985` is in `WRLD 0206D275` / **Coldharbour** and functions as a major exterior hub in the placement graph.

A door edge proves that the plugin configures a teleport route between two references. It does **not** prove that the route is always unlocked, reachable in every quest state, or chronologically traversed in both directions.

## Exterior hub

`CELL 02072985` (unnamed exterior, Coldharbour worldspace) connects directly to many interiors, including:

- `0207FB11` — **Mathmalatu Priory**
- `020AE0E4` — **Gardener's House**
- `020AFB4B` — **Abandoned House**
- `020AFB8D` — **Bandit Kanra's Lair**
- `020B07D1` — **Slave Trader's House**
- `020B0EF5` — **Rusty Blacksmith**
- `020B0F6B` — **Bourlor's House**
- `020B1581` — **Jo'vanni's House**
- `020B1BDB` — **Martha's House**
- `020B6206` — **Sandman Inn**
- `020B704A` — **Witch's House**
- `020C13C0` — **Thrassian Apothecary**
- `020C3764` — **Chestnut Handy Stables**
- `020CB07C` — **Old Temple of the Eight Divines**
- `020D6B49` — **Eastern Sewers**
- `020D8C1F` — **Inquisition Court Sewers**
- `020DD5ED` — **Narfin's Inquisition Court**
- `020E2693` — **Fort Welkynd**
- `020E75A0` — **Fort Sepredia**
- `020E9062` — **Curia Morimath**
- `020EB072` — **Fort Verin**
- `020EDDF6` — **Slums**
- `020F9C21` — **Prison Tower**
- `02101AA1` — **Marukh's Underground Priory**
- `021038CB` — **Malatar Mansion**
- `02109458` — **Sard's Charnel**
- `0210EBFD` — **Nenyond's Underground Priory**
- `0211BC4B` — **Malada Ageasel**
- `0211E11F` — **Sancremor Tower**
- `02123F84` — **First Corridor** of the Silver Cocoon route
- `02125B35` — **Throne of Order**
- `02143B78` — **Ultar's Charnel**
- `0221AFA1` — **First Inquisition Court**
- `02239B51` — **Silorn's Priory**
- `02259C5B` — **Jhunal's Library**
- `025585CE` — **Gravekeeper's House**

This strongly supports treating the Coldharbour overworld as a hub with many instanced/interior story sites rather than a single linear dungeon.

## Important multi-cell chains

### Imperial City / prison route
`Slums (020EDDF6)`
→ `Beggar's Path (020F024E)`
→ `Imperial Prison Sewers (020F4D2F)`
→ either `Bed of Corruption (020F86C4)` or `Prison Tower (020F9C21)`.

### Malada route
`Marukh's Underground Priory (02101AA1)`
↔ `Malada (021157FC)`
↔ `Malada Gandrasel (0211821A)`
↔ `Malada Aldmerisel (02119953)`
↔ `Malada Ageasel (0211BC4B)`
↔ `Malada Abasel (0211C93B)`.

A branch from **Gandrasel** also reaches **Malada Burosel** (`0211B381`).

### Sancremor route
`Sancremor Tower (0211E11F)`
↔ `Sancremor Ceysel (0211E8D4)`
↔ `Sancremor Nagasel (02120DA9)`
↔ `Sancremor Angasel (02121AA2)`.

### Silver Cocoon / Order route
`First Corridor (02123F84)`
↔ `Second Corridor (02125336)`
↔ `Large Void (02253895)`
↔ `Throne of Order (02125B35)`.

### Alessian / Belharza court route
`Second Inquisition Court (0221AEA7)`
↔ `First Inquisition Court (0221AFA1)`
↔ `Belharza's Hidden Charnel (0251C043)`
↔/→ `??? memory prison (0251D5D5)`.

The First Inquisition Court also links directly to the memory-prison cell.

### Wellspring / Silorn route
`Underground Lake (020C09BA)` connects to `Passageway (020C2D85)` and also directly to `Silorn's Priory (02239B51)`.

### Arkay complex
`Chapel of Arkay Cemetery (020C8FCF)`
↔ `Chapel of Arkay (020C98F8)`
↔ `Ossuary (021E3F63)`.

### Fort and court interiors
- `Fort Welkynd (020E2693)` ↔ `Varla's Hall (020E63D8)`
- `Curia Morimath (020E9062)` ↔ `Golden Sanctuary (02224E78)`
- `Narfin's Inquisition Court (020DD5ED)` ↔ `Fountain Garden of Dibella (020E0889)`
- `Sard's Charnel (02109458)` ↔ `Sard's Ossuary (0210CDFD)`
- `Nenyond's Underground Priory (0210EBFD)` ↔ `Funeral Temple (021114AF)`

## Cross-layer edge

The graph contains a configured door pair between the ordinary **Temple of Stendarr** (`02025091`) and **Mathmalatu Priory** (`0207FB11`) in the Coldharbour set.

This is implementation evidence for a direct teleport relationship, but its story meaning and availability must be determined from lock/state/script conditions before treating it as an always-open physical doorway between the pre-Coldharbour Temple and Coldharbour.

## Next technical layer

To turn this topology into a chronological route graph, combine these XTEL edges with:

1. door enable/disable and lock state;
2. quest stage conditions;
3. scene/VMAD fragments that move or enable references;
4. memory-quest transition markers;
5. the Good/Bad Aetherius selection logic.
