# Golden Dragon Flight

**Quest:** `zDcdMqDragon`  
**Title:** Golden Dragon Flight  
**Source:** `DAc0da.esm:004564`  
**Continuity:** `tes.mod.vicn.dac0da`  
**Evidence mode:** QUST/alias/package routing

## Role

This is a support/state-machine quest linked directly from **The Sea of Causality**.

The MQ01 generated quest script has:

- `qDragon` -> `DAc0da.esm:004564`

The support quest has a single unique actor alias:

- `Dragon` -> `DAc0da.esm:0033BC`
- Editor ID: `zDcdUqDragonGold`
- displayed name: **???**

The placed actor reference is `DAc0da.esm:004472` in the **Sea of Causality** location layer.

## Stage-driven flight route

The quest defines stages:

- 0
- 10
- 20
- 30
- 40
- 50
- 60
- 70
- 900
- 999

The Dragon alias owns a package sequence:

- `DAc0da.esm:004474` — `zDcdMqDragonFilightA01`
- `DAc0da.esm:004537` — `zDcdMqDragonFilightA02`
- `DAc0da.esm:00456D` — `zDcdMqDragonFlightA03`
- `DAc0da.esm:004570` — `zDcdMqDragonFlightA04`
- `DAc0da.esm:004573` — `zDcdMqDragonFlightA05`
- `DAc0da.esm:004577` — `zDcdMqDragonFlightEnd`

Their conditions reference `zDcdMqDragon` at successive stage values **20, 30, 40, 50, 60, and 70** and point at a chain of route/marker references in the same worldspace.

This is therefore a deterministic **flight choreography/state machine**, not an exposition quest.

## Sound hooks

The generated quest script also references:

- `DAc0da.esm:004579` — `zDcdDragonFallLP`
- a Skyrim-master dragon-death/fall sound reference

This supports the quest's role in controlling a visible/audible dragon-flight event.

## Relationship to Samon

In MQ01, Akashiya-Samon says he saw and pursued a **golden dragon**, later saying it flew east and that he would follow it.

That dialogue and this support quest occupy the same main-quest layer, so `zDcdMqDragon` is the mechanical implementation of the golden-dragon movement hook that Samon follows.

## Relationship to Tsuunalinfaxtir

**Drowned Nighthawk** later uses a different dragon NPC form:

- `DAc0da.esm:005036` — **Tsuunalinfaxtir**

Yngol ultimately says Tsuunalinfaxtir is the other half of his being.

The earlier MQ01 golden-dragon NPC and Tsuunalinfaxtir share the same dragon race, voice, skin/armor form, combat style, class, and several other base-NPC fields, but they are **different FormIDs** and differ in some actor-base values.

Therefore the safe library statement is:

> Golden Dragon Flight carries the unnamed golden dragon pursued by Samon; Drowned Nighthawk later centers on a golden dragon that Yngol names Tsuunalinfaxtir.

The continuity strongly suggests a narrative handoff, but exact same-actor identity should remain a comparison claim rather than being asserted solely from matching appearance/archetype.
