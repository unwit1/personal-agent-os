# Auxiliary zzzLrh dialogue completeness ledger

Source: raw `Glenmoril.esm`

Scope: every QUST whose EditorID begins `zzzLrh` / `zzzLRH`, excluding the ten main `zzzLrhMq01–zzzLrhMq10` Little Red quests.

## Raw inventory

| Quest | Title | SCEN | topics | total | status |
|---|---|---:|---:|---:|---|
| zzzLrhBypass | Bypass | 0 | 0 | **0** | inventoried |
| zzzLrhGeneric | LRH Generic Dialogue | 0 | 45 | **45** | normalized |
| zzzLrhQCheckDreamTorvesard | Check Sleep | 0 | 0 | **0** | inventoried |
| zzzLrhqChickTraderRevenge | The Chick Trader's Shadow | 0 | 0 | **0** | inventoried |
| zzzLrhqItheliaCall01 | Jazel Call Ithelia 01 | 18 | 0 | **18** | normalized |
| zzzLrhqItheliaCall02 | Grasping at Straws | 8 | 0 | **8** | normalized |
| zzzLrhQTorvesardContact | Ghost in the Mirror | 3 | 36 | **39** | normalized |
| zzzLRHrqChicken | Chicken Extermination | 0 | 0 | **0** | inventoried |
| zzzLRHrqCookingRecipe | Cooking Recipe | 0 | 0 | **0** | inventoried |
| zzzLRHrqKanraRescue | Kanra Rescue | 0 | 0 | **0** | inventoried |
| zzzLRHrqMushroom | Mushroom | 0 | 0 | **0** | inventoried |
| zzzLRHrqNutrient | Nutritional Potion | 0 | 0 | **0** | inventoried |
| zzzLRHrqRogueHunt | Ruffian Hunt | 0 | 0 | **0** | inventoried |
| zzzLRHrqSweetroll | Sweet Roll | 0 | 0 | **0** | inventoried |
| zzzLrhSqRoadRoller | Brain-Billy's Sting | 8 | 569 | **577** | normalized |
| zzzLRHSqRoadRollerStarter | Starter: Rolls-On-Roads | 0 | 0 | **0** | inventoried |
| zzzLrhSubQuest01 | The Black Owl | 0 | 5 | **5** | normalized previously |
| zzzLrhSubQuest02 | Nostos G | 0 | 0 | **0** | inventoried |
| zzzLrhSubQuest03 | The Black Owl Flies | 0 | 0 | **0** | inventoried |

**Auxiliary raw expected total: 692 exact response texts.**
**Normalized: 692 / 692.**
**Status: closed for direct QUST/SCEN linkage.**

## Overlap note

The five responses from `zzzLrhSubQuest01 The Black Owl` were already included in the core Act-2 completeness scope.

Therefore:
- auxiliary corpus total: 692
- newly additive beyond the already-counted core Act-2 corpus: **687**

## Counting method

Same deterministic pipeline used for Act 1 and Act 2:
- SCEN PNAM → QUST;
- dialogue action DATA → DIAL → child INFO NAM1;
- non-SCEN DIAL QNAM → QUST, excluding DIALs consumed by scenes;
- speaker resolution via SCEN alias, GetIsAliasRef, or GetIsID.
