# Gaiden Shinji — VIGILANT continuity

- Continuity: `tes.mod.vigilant`
- Base identity: historical Redguard blademaster / Order of Diagna hero
- NPC: `NPC_ 02313C50` / `zzzCHGaidenShinji` — **Gaiden Shinji**
- Race: master Redguard race
- Placement: `ACHR 02316319`
- Worldspace: `WRLD 020B2AEE` / **Arena**, a child worldspace of Coldharbour
- Location assignment: `LCTN 0206D7EA` / **Coldharbour**
- Ability: `SPEL 024F7BBB` / **Gaiden Shinji Ability**
- Outfit: `OTFT 024FC4C4` / `zzzCHOutfitGaiden`
- Weapons:
  - `WEAP 02556062` / **Shinji's Sword**
  - `WEAP 02556063` / **Shinji's Greatsword**
- Generic-dialogue quest: `QUST 02126838` / **CH Generic dialogue**
- Call trigger: `ACTI 02317678` / `zzzCHGaidenCallTrigger`

## Historical identity

VIGILANT presents this NPC directly as **Gaiden Shinji**, not as an unnamed imitation.

His implementation reinforces the historical Redguard/Diagna identity:

- Redguard race;
- unique Gaiden equipment;
- explicit knowledge of **Diagna**;
- speech invoking **Tu'whacca** and **Tava**;
- a personal search tied to ancient Yokuda;
- later involvement with Aredhel through **Blade of Diagna** equipment.

Current classification:

**high-confidence VIGILANT representation of the established historical Gaiden Shinji.**

Whether this is literally Gaiden's surviving soul, a Coldharbour reconstruction, or another supernatural reappearance remains unresolved.

## Arrival in Coldharbour

The player can ask:

**“How did you get here? I swear there was no one here before.”**

Gaiden answers that:

- with **Tu'whacca's permission**;
- he arrived **on the wings of Tava**;
- the sound of swords clashing led him to the player.

This is VIGILANT-specific testimony explaining his supernatural arrival.

Because established history treats Gaiden as a dead First Era hero, the line strongly suggests a postmortem/soul-transit interpretation.

However, the ESM does not label him explicitly as:
- ghost;
- shade;
- memory;
- Soul Shriven;
- summoned ancestor.

Lorekeeper should therefore preserve the statement without forcing a single metaphysical mechanism.

## Arena placement

Gaiden's placed actor `02316319` belongs to:

- `WRLD 020B2AEE` / **Arena**
- with `XLCN 0206D7EA` / **Coldharbour**

The Arena worldspace itself uses:
- `LCTN 020B2BDB` / **Arena**
- parent world `WRLD 0206D275` / **Coldharbour**

So Gaiden is structurally a Coldharbour/Arena NPC rather than a historical-memory quest actor.

This distinction matters: he is not assigned to one of the 13 formal memory quests.

## Gaiden call trigger

The ESM contains:

- `ACTI 02317678` / `zzzCHGaidenCallTrigger`
- placed as `REFR 02317679`
- linked to Gaiden's actor reference.

Its VMAD uses:
- `CHGaidenCallTriggerScript`

with properties referencing:

- `QUST 024F57C1` / **VS Grey Prince**
- `GLOB 021A2551` / `zzzCHWinnerPoint`
- `ACTI 021DB906` / a summon/valor visual effect activator.

This strongly suggests Gaiden's appearance/call logic is connected to Arena victory state and the Grey Prince encounter.

The external script body is not present in the ESM, so Lorekeeper should **not** assert the exact winner-point threshold or trigger timing.

## Generic dialogue

All six Gaiden dialogue topics belong to:

- `QUST 02126838` / **CH Generic dialogue**

Each response is explicitly conditioned on:

- `NPC_ 02313C50` / Gaiden Shinji

so the speaker attribution is structural.

### Greeting / combat recognition

`INFO 02317662`:

Gaiden praises the player after a good fight and says they must be a warrior of some renown.

This fits his Arena placement.

### Aredhel

`DIAL 02317664` asks:

**“Does the name Aredhel mean anything to you?”**

`INFO 02317665` has Gaiden say:

- Aredhel was an elf;
- a brilliant swordsman;
- sought revenge on someone;
- Gaiden gave Aredhel a sword and armor;
- outside this wasteland Aredhel might have earned great fame in Tamriel.

This directly supports the later Aredhel encounter's equipment story.

## Connection to Aredhel

The later Coldharbour Aredhel:

- is an elf;
- carries **Aredhel's Sword**;
- wears the **Blade of Diagna** armor set;
- retains other legacy `Renald` identifiers in the encounter implementation.

Gaiden's dialogue independently says he supplied Aredhel with a sword and armor for revenge.

This provides strong narrative support for:

**Blood Matron Aredhel → survives/reappears in Coldharbour → meets Gaiden → receives Diagna-associated equipment → pursues revenge → later confronts the player in Pitier.**

The precise chronology and metaphysical mechanism remain unresolved.

See:

`analysis/aredhel-renald-identity.md`

## Purpose in Coldharbour

When asked why he is there, Gaiden says he is searching for:

- a certain **“sword”**;
- lost when **Yokuda sank**;
- possibly related to **Diagna**.

He says he has searched for it for many years without finding even a trace, and does not believe it is present there either.

This is a VIGILANT-specific extension of Gaiden's story.

### Diagna explanation

When asked about Diagna, Gaiden calls him:

**the Orichalc God of the Sideways Blade**

and an old god of the Redguards whose name few still know.

That identification is compatible with established Redguard religious tradition, while Gaiden's personal lost-sword search is VIGILANT-specific.

## No identified lost sword

A focused ESM search found no named weapon, miscellaneous item, activator, or other artifact explicitly matching:

- Gaiden's lost Yokudan sword;
- a “Sideways Blade” item;
- an “Orichalc” sword;
- a Diagna sword artifact.

The only direct references to the lost sword are Gaiden's dialogue.

Therefore the object should currently be modeled as:

**unidentified lost Yokudan/Diagna-associated sword — testimony-only quest motive**

rather than linked to an arbitrary katana.

## Broader Diagna cluster

The ESM does contain other Diagna-related records:

- **Blade of Diagna** armor used by Aredhel;
- **Knight of Diagna** armor worn by `NPC_ 0251653B` / **Judo of the Order of Diagna**;
- Judo's two **Akaviri Black Katanas** and the related crafting-unlock system.

These establish a broader Order-of-Diagna presence in VIGILANT. The record-level comparison is preserved at `analysis/diagna-coldharbour-cluster.md`.

They do not identify Gaiden's missing sword.

## Follower behavior

The player can ask:

**“Will you lend me your strength?”**

`INFO 02317671` has Gaiden agree to travel with the player.

The INFO's VMAD contains a fragment script with a property explicitly named:

- `PotentialFollowerFaction`

referencing the master-game PotentialFollowerFaction.

This is strong structural evidence that the acceptance response has follower-enrollment behavior.

The exact fragment body is external/not decoded here, so the precise add/remove faction calls should not be asserted.

## Player / Sep remark

In the same response Gaiden calls the player:

**someone embraced by Sep**

before agreeing to accompany them.

That phrase is VIGILANT character testimony and may reflect Gaiden's Redguard theological interpretation of the player/Prisoner.

It should not automatically be converted into an objective statement that the player is literally an avatar or chosen agent of Sep.

## Equipment

### Outfit

`OTFT 024FC4C4` contains:

- `024FC4B8` — **Gaiden's Boots**
- `024FC4B9` — **Gaiden's Armor**
- `024FC4BA` — **Gaiden's Gauntlets**
- `024FC4BB` — **Gaiden's Helmet**

### Weapons

Gaiden directly carries:

- **Shinji's Sword**
- **Shinji's Greatsword**

These are his own distinct equipment and should not be conflated with:
- Aredhel's Sword;
- the Akaviri Black Katana;
- the unidentified lost Yokudan/Diagna sword he is searching for.

## Canon boundary

Established Elder Scrolls lore supplies Gaiden Shinji, the Order of Diagna, his Redguard/Yokudan cultural context, and his status as a historical martial hero.

VIGILANT specifically adds:
- his supernatural arrival in Coldharbour;
- Tu'whacca/Tava as the explanation for that arrival;
- his search for an unidentified lost Yokudan sword;
- his meeting with/equipment gift to Aredhel;
- his potential follower role;
- his interaction with the VIGILANT player.

These additions remain `tes.mod.vigilant`.
