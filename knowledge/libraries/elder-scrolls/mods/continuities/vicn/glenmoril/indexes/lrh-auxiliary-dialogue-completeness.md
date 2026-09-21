# Auxiliary zzzLrh dialogue completeness ledger

Source: raw `Glenmoril.esm`

Scope: every QUST whose EditorID begins `zzzLrh` / `zzzLRH`, excluding the ten main `zzzLrhMq01–zzzLrhMq10` Little Red quests.

## Raw inventory

| Quest | Title | SCEN | topics | total |
|---|---|---:|---:|---:|
| zzzLrhBypass | Bypass | 0 | 0 | **0** |
| zzzLrhGeneric | LRH Generic Dialogue | 0 | 45 | **45** |
| zzzLrhQCheckDreamTorvesard | Check Sleep | 0 | 0 | **0** |
| zzzLrhqChickTraderRevenge | The Chick Trader's Shadow | 0 | 0 | **0** |
| zzzLrhqItheliaCall01 | Jazel Call Ithelia 01 | 18 | 0 | **18** |
| zzzLrhqItheliaCall02 | Grasping at Straws | 8 | 0 | **8** |
| zzzLrhQTorvesardContact | Ghost in the Mirror | 3 | 36 | **39** |
| zzzLRHrqChicken | Chicken Extermination | 0 | 0 | **0** |
| zzzLRHrqCookingRecipe | Cooking Recipe | 0 | 0 | **0** |
| zzzLRHrqKanraRescue | Kanra Rescue | 0 | 0 | **0** |
| zzzLRHrqMushroom | Mushroom | 0 | 0 | **0** |
| zzzLRHrqNutrient | Nutritional Potion | 0 | 0 | **0** |
| zzzLRHrqRogueHunt | Ruffian Hunt | 0 | 0 | **0** |
| zzzLRHrqSweetroll | Sweet Roll | 0 | 0 | **0** |
| zzzLrhSqRoadRoller | Brain-Billy's Sting | 8 | 569 | **577** |
| zzzLRHSqRoadRollerStarter | Starter: Rolls-On-Roads | 0 | 0 | **0** |
| zzzLrhSubQuest01 | The Black Owl | 0 | 5 | **5** |
| zzzLrhSubQuest02 | Nostos G | 0 | 0 | **0** |
| zzzLrhSubQuest03 | The Black Owl Flies | 0 | 0 | **0** |

**Auxiliary raw expected total: 692 exact response texts.**

## Current normalization

Already normalized previously:
- `zzzLrhSubQuest01 The Black Owl`: 5 / 5

Normalized in auxiliary batch 25:
- `zzzLrhGeneric`: 45 / 45
- `zzzLrhQTorvesardContact`: 39 / 39
- `zzzLrhqItheliaCall01`: 18 / 18
- `zzzLrhqItheliaCall02`: 8 / 8

All zero-response quests are explicitly inventoried.

**Normalized: 115 / 692**
**Remaining: 577**

The entire remaining response backlog is therefore:
`zzzLrhSqRoadRoller Brain-Billy's Sting` — **577 responses**.

## Counting method

Same as the Act-1/Act-2 ledgers:
- SCEN PNAM → QUST;
- dialogue action DATA → DIAL → child INFO NAM1;
- non-SCEN DIAL QNAM → QUST, excluding DIALs consumed by scenes;
- speaker resolution via SCEN alias, GetIsAliasRef, or GetIsID.
