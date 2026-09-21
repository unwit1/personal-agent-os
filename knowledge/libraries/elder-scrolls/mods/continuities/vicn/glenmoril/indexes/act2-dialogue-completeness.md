# Act 2 dialogue completeness ledger

Source: raw `Glenmoril.esm`
Scope: direct Witch Hunt quest families whose QUST EDIDs match `zzzGHMq01` through `zzzGHMq06` (case-insensitive `Mq/mq`), plus the associated `zzzLrhSubQuest01 The Black Owl`.

## Counting method

For each quest:

1. Resolve SCEN association using the scene's quest `PNAM`.
2. For each dialogue action (`ANAM` type 0), follow `DATA` → DIAL → child INFO records.
3. Count every INFO `NAM1` response text.
4. For non-SCEN topics, follow DIAL `QNAM` → quest and exclude any DIAL already used by a dialogue SCEN action.
5. Count every remaining child INFO `NAM1`.
6. Resolve speakers through:
   - SCEN Actor ID → QUST alias;
   - INFO `GetIsAliasRef` (function 566);
   - INFO `GetIsID` (function 72) where required.

This avoids counting the same DIAL once as a scene row and again as a general topic.

## Reconciled totals

| Quest | Responses |
|---|---:|
| zzzGHMq01 — The Blue Bird | 179 |
| zzzGHMq01Captive — Captive | 0 |
| zzzGHMq01SideA — Chaplain's Song 1 | 10 |
| zzzGHMq02 — Ebonwall | 161 |
| zzzGHMq02BO — The Black Owl 02 | 5 |
| zzzGHMq02Gen — Mq02 Generic | 15 |
| zzzGHMq02GoodEnd — Embers | 17 |
| zzzGHMq02Nazeem — Nazeem | 0 |
| zzzGHMq02Sub01 — Percussive Maintenance | 91 |
| zzzGHMq03 — Tainted Orphan | 155 |
| zzzGHMq03BO — The Black Owl 03 | 7 |
| zzzGHMq03Sub01 — A Thousand Daggers | 76 |
| zzzGHMq04 — The Bronze Key | 148 |
| zzzGHMq04BO — The Black Owl 04 | 5 |
| zzzGHMq04Radio — Thalmor Radio | 15 |
| zzzGHMq04Sub01 — Shop of Curiosities | 103 |
| zzzGHMq05 — Oneiromancer | 144 |
| zzzGHMq05Charm — Charm | 29 |
| zzzGHMq05Joint — Broken Egg | 70 |
| zzzGHMq05Sub01 — Dream Within a Dream | 43 |
| zzzGHMq05Sub02 — The Last Chick Trader | 50 |
| zzzGHMq05Sub03 — The Night of Tears | 18 |
| zzzGHMq05Sub04 — Louse | 9 |
| zzzGHMq05Sub05 — The Owls | 10 |
| zzzGHMq05Sub06 — Confined | 7 |
| zzzGHMq05Sub07 — Lucid Dream | 69 |
| zzzGHMq05Subject — Subject Dialogue | 15 |
| zzzGHMq06 — Or the Gospel | 175 |
| zzzGHmq06Sub01 — St. Bazura | 112 |
| zzzLrhSubQuest01 — The Black Owl | 5 |

**Total: 1,743 exact response texts.**

## Audit corrections

Two old manual counts were off by one in opposite directions:

- `zzzGHMq05ScJazelBoy`: 16 responses, not 17.
- `zzzGHMq06ScPlan`: 9 responses, not 8.

Their net effect on the post-batch-05 cumulative total was zero.

## Closure status

Within this defined scope, the direct QUST-linked / SCEN-linked dialogue corpus is now **numerically reconciled against the raw ESM**.

This does **not** claim that every dialogue-like string in the entire plugin is finished. Separate future audits should cover:
- shared/general DIAL records with no direct QNAM;
- dialogue reached only through scripts or indirect conditions;
- replay/debug quests;
- Act 1 `zzzLrhMq*`;
- later/revision quest families outside the core Witch Hunt namespace;
- non-dialogue quest evidence such as packages, scripts, books, activators, and terminal/message records.
