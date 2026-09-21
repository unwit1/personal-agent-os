# DAc0da branch-state manager

**Continuity:** `tes.mod.vicn.dac0da`  
**Primary quest:** `zDcdJsonManager` — Json Manager  
**Source:** `DAc0da.esm:00D043`

DAc0da carries important side-quest/ending results forward through dedicated global state variables.

## Persistent state globals

The Json Manager script directly references:

- `DAc0da.esm:00D044` — `zDcdJsClear`
- `DAc0da.esm:00D045` — `zDcdJsClearWorm`
- `DAc0da.esm:00D046` — `zDcdJsClearYngol`
- `DAc0da.esm:00D047` — `zDcdJsEndHist`
- `DAc0da.esm:00D048` — `zDcdJsEndCheese`

All are GLOB records with initial value 0.

The manager also references a form list containing these tracked values.

## Yngol branch persistence

**Drowned Nighthawk** has direct quest-script properties:

- `qJson` -> Json Manager
- `gJsYngol` -> `zDcdJsClearYngol`

**Patchwork** independently has:

- `gJsYngolClear` -> the same global

and later MQ03/MQ04 INFO conditions explicitly test `zDcdJsClearYngol`.

This proves Yngol's side-quest resolution is intentionally carried into later main-quest dialogue.

For example, later Rolls-On-Roads dialogue about the Atmoran influx/golden dragon is conditionally selected using the Yngol-clear state.

## Worm/Mnemolichite branch persistence

**Echoes of Mnemolichite** has direct properties:

- `qJson` -> Json Manager
- `gJsWorm` -> `zDcdJsClearWorm`

**Patchwork** independently references the same global through `gJsWormClear`.

Later conditional dialogue concerning the Sload/Mannimarco/Abnur anomaly also checks this global.

The Worm arc is therefore not isolated optional content; the main quest can recognize whether it occurred.

## Hist ending

**Pan-Argonia** has:

- `qJson` -> Json Manager
- `gJsHistEnd` -> `zDcdJsEndHist`

This gives the Hist/Numidium alternate ending an explicit persistent state flag.

## Cheese/Jill ending

**Rella Mozzarella** has:

- `qJson` -> Json Manager
- `gJsCheeseEnd` -> `zDcdJsEndCheese`

MQ04 also references the Cheese-ending quest directly.

This gives the Sheogorath/Jillian-censorship alternate ending its own persistent state.

## Interpretation

DAc0da is designed around a persistent **branch-history model**:

- side quests can modify later main-quest exposition;
- mutually different endings are tracked explicitly;
- epilogues can be launched from branch-specific state;
- later retrieval should therefore keep branch conditions attached to claims.

The lore library should avoid flattening conditional lines into one universal chronology. Where possible, future ingestion should record the relevant global/quest condition alongside each branch-sensitive INFO.
