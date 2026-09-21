# Act 1 dialogue completeness ledger

Source: raw `Glenmoril.esm`
Scope: the ten main `zzzLrhMq01–zzzLrhMq10` **Little Red** quests.

## Counting method

1. SCEN `PNAM` → associated QUST.
2. Dialogue actions: `ANAM type 0` → `DATA` DIAL.
3. DIAL → child INFO records.
4. Count every INFO `NAM1` response.
5. For non-SCEN dialogue, DIAL `QNAM` → QUST, excluding DIALs already consumed by SCEN dialogue actions.
6. Speakers resolve through SCEN Actor ID → QUST alias, INFO `GetIsAliasRef`, or INFO `GetIsID`.

## Raw expected responses

| Quest | Title | SCEN | topics | total |
|---|---|---:|---:|---:|
| zzzLrhMq01 | The Way is Blocked | 25 | 72 | **97** |
| zzzLrhMq02 | The Chick Trader | 15 | 61 | **76** |
| zzzLrhMq03 | A Curious Animal | 8 | 18 | **26** |
| zzzLrhMq04 | Weary of Waiting | 9 | 20 | **29** |
| zzzLrhMq05 | Ah, Apple Pie! | 20 | 33 | **53** |
| zzzLrhMq06 | Cleaning Up Falkreath | 8 | 40 | **48** |
| zzzLrhMq07 | The Blessing | 10 | 34 | **44** |
| zzzLrhMq08 | My Precious | 7 | 29 | **36** |
| zzzLrhMq09 | Ta Ta! | 27 | 33 | **60** |
| zzzLrhMq10 | The Cat and the Chick | 32 | 84 | **116** |

**Act-1 raw expected total: 585 exact response texts.**

## Processing status

- Mq01 — The Way is Blocked: **97 / 97 normalized**
- Mq02 — The Chick Trader: **76 / 76 normalized**
- Mq03 — A Curious Animal: **26 / 26 normalized**
- Mq04 — Weary of Waiting: **29 / 29 normalized**
- Mq05 — Ah, Apple Pie!: **53 / 53 normalized**
- Mq06–Mq10: inventoried, pending sequential normalization

Normalized so far: **281 / 585**
Remaining: **304**
