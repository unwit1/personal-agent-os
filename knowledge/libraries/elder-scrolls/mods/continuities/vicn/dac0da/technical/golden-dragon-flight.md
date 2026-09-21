# Golden Dragon Flight

**Quest:** `zDcdMqDragon`  
**Title:** Golden Dragon Flight  
**Source:** `DAc0da.esm:004564`  
**Continuity:** `tes.mod.vicn.dac0da`  
**Evidence mode:** QUST/SCEN/PACK/REFR/VMAD choreography

## Purpose

This support quest does **not** own dialogue. It is a movement/state controller for DAc0da's golden dragon.

MQ01, **The Sea of Causality**, has a direct quest-script property:

- `qDragon` -> `zDcdMqDragon`

so the support quest is structurally part of MQ01.

## Dragon alias

Alias 0, `Dragon`, points to unique NPC:

- `DAc0da.esm:0033BC`
- `zDcdUqDragonGold`
- displayed FULL: **???**

The intentionally obscured display name is consistent with the main story initially presenting the dragon as an unidentified golden dragon.

The NPC carries standard dragon actor behavior plus DAc0da-specific appearance/script data.

## Flight packages

The Dragon alias has six quest packages:

1. `zDcdMqDragonFilightA01`
2. `zDcdMqDragonFilightA02`
3. `zDcdMqDragonFlightA03`
4. `zDcdMqDragonFlightA04`
5. `zDcdMqDragonFlightA05`
6. `zDcdMqDragonFlightEnd`

Their quest-stage conditions step through the flight sequence at approximately stages:

- 20
- 30
- 40
- 50
- 60
- 70

The quest also defines stages 0, 10, 20, 30, 40, 50, 60, 70, 900, and 999.

This is choreography/state evidence, not new cosmological exposition.

## Scene sequence

SCEN `DAc0da.esm:004565` / `zDcdMqDragonSc01` controls the dragon through scene phases.

Its package actions include:

- `zDcdMqDragon01OrbitStart`
- `zDcdMqDragon01PerchShip`
- `zDcdMqDragon01FilightAway`

The scene then hands movement back to the later staged flight packages.

A dedicated trigger activator exists:

- `DAc0da.esm:004567`
- `zDcdMqDragonSceneTrigger`

Its script `DcdStartSceneTriggerScript` has `ReqQuest` pointing directly to `zDcdMqDragon`.

## Sound/state properties

The quest fragment script includes:

- `SdDragonFall` -> DAc0da sound `zDcdDragonFallLP`;
- `SdDragonDeath` -> a master-file dragon death sound;
- `Alias_Dragon` -> quest alias 0.

These properties show that falling/death audio is part of the controlled sequence, but the ESM does not expose the fragment code needed to say exactly which stage plays each sound.

## Lore interpretation boundary

The support quest itself establishes only that DAc0da intentionally choreographs the same mysterious golden dragon through MQ01.

Later **Drowned Nighthawk** dialogue/alias evidence is what identifies the relevant golden-dragon identity thread with **Tsuunalinfaxtir / Yngol's other half**.

Do not use this support quest alone to assert that every golden-dragon appearance is Tsuunalinfaxtir; identity should remain tied to the later direct evidence.
