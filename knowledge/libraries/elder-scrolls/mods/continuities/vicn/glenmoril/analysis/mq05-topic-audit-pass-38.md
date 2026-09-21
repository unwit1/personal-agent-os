# Mq05 topic audit — pass 38

After completing the SCEN audit, the raw ESM was scanned for DIAL records whose `QNAM` points to a `zzzGHMq05*` quest but whose DIAL FormID is **not referenced by any dialogue SCEN action**.

## Inventory

The audit found **204 non-SCEN responses** across the Mq05 family:

- main Oneiromancer: 81
- Broken Egg: 44
- Dream Within a Dream: 12
- Last Chick Trader: 43
- Lucid Dream ambient: 9
- Subject Dialogue: 15

Lucid Dream ambient and Subject Dialogue were already ingested in batches 08 and 09.

## Pass 38 completion

The **81 main Oneiromancer rows** are now normalized, raising the tracked exact corpus from 458 to **539**.

## Remaining topic backlog

Not yet corpus-normalized in this audit:
- Broken Egg: 44
- Dream Within a Dream: 12
- Last Chick Trader: 43

Total remaining newly identified topic rows: **99**.

These should be processed next, with Last Chick Trader prioritized for Chick/EGG/Owl terminology and Broken Egg prioritized for Lalanoah/Brandt/Ulrik/Jhunal evidence.
