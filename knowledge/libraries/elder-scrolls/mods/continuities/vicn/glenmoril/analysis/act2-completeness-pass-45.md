# Act 2 completeness audit — pass 45

The sequential Witch Hunt ingestion has now been checked against the raw ESM rather than assumed complete from quest order.

## Raw reconciliation

Direct core Act-2 scope:
- all QUST records matching `zzzGHMq01–zzzGHMq06` including subquests/BO/generic/radio variants;
- St. Bazura's lowercase-`mq` editor ID;
- associated `zzzLrhSubQuest01 The Black Owl`.

Raw expected response count: **1,743**.

Repository count before recovery batch: **1,595**.

Gap: **148**.

## Entire gap explained

- Mq02 Generic: 15
- Black Owl 04: 5
- Thalmor Radio: 15
- Or the Gospel non-SCEN topics: 113

Total recovered: **148**.

## Historical count correction

The audit also found:
- one old Dream Within a Dream overcount;
- one old Or-the-Gospel undercount.

They cancel, so the total remained unaffected once both were corrected.

## Result

**1,743 / 1,743 direct core Act-2 responses are now accounted for.**

The Act-2 Witch Hunt dialogue layer can therefore be marked **closed for direct QUST/SCEN linkage**.

## Next ingestion frontier

Proceed to **Act 1 `zzzLrhMq*`** using the same deterministic parser and completeness ledger from the start.

Before prose promotion, create an Act-1 raw inventory:
- quest IDs/titles;
- SCEN response counts;
- non-SCEN QNAM response counts;
- alias maps;
- zero-dialogue quest markers.

This should prevent the repeated partial-audit cleanup that Act 2 required.
