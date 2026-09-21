# Foot Of The Mountain

Quest FormID: `0505F6C9`  
Editor ID: `CLWKicker01Quest`

## Journal stages

### Stage 10

I encountered a strange assailant on the road. Perhaps there will be a clue to the attack on his body.

### Stage 20

I encountered a strange assailant on the road, and found a note on his body. I should read it.

### Stage 30

The note on the assailant's body mentioned some ruins near Cragwallow Slope in Eastmarch, newly uncovered by a landslide. It sounds like no-one has been inside for a very long time. Maybe I should investigate...

## Objectives

- `10` — Search the body for clues to the attack
- `20` — Read Camilla's Note
- `30` — Investigate the ruins mentioned in Camilla's Note
- `40` — Enter the Velothi Mountain Tunnels

## Aliases

- `0` **TRIGGER** (reference) → unresolved/non-actor
- `1` **myHoldLocation** (location) → unresolved/non-actor
- `2` **myHoldContested** (location) → unresolved/non-actor
- `3` **myHoldImperial** (location) → unresolved/non-actor
- `4` **myHoldSons** (location) → unresolved/non-actor
- `5` **Scene Marker2** (reference) → unresolved/non-actor
- `6` **Scene Marker1** (reference) → unresolved/non-actor
- `7` **CenterMarker** (reference) → unresolved/non-actor
- `8` **IsidorAlias** (reference) → Isidor
- `9` **Note** (reference) → unresolved/non-actor
- `11` **MapMarker** (reference) → unresolved/non-actor

## Runtime progression

The opening quest chain is directly scripted:

- `NPC_ 0505F157` / **Isidor**: `defaultSetStageOnDeath` → stage **10**.
- `BOOK 0505F158` / **Camilla's Note**: player acquisition → stage **20**.
- The same note: close/read → stage **30**.
- `REFR 050632CB`: player entry trigger → stage **40**.

Because objective 10 targets `IsidorAlias`, this structurally identifies Isidor as the journal's “strange assailant.”
