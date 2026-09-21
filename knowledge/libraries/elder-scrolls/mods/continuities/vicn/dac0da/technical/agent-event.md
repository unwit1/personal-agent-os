# Agent Event

**Quest:** `zDcdMqAgent`  
**Title:** Agent Event  
**Source:** `DAc0da.esm:004566`  
**Continuity:** `tes.mod.vicn.dac0da`  
**Evidence mode:** QUST/SCEN/PACK/NPC structure

## Purpose

This support quest is an ambient/foreshadowing encounter for **The Agent** during MQ01.

MQ01 has a direct quest-script property:

- `qAgent` -> `zDcdMqAgent`

and its own later `Agent` alias/boss machinery.

The support quest owns no DIAL topics.

## Ambient Agent actor

Alias 0, `Agent`, points to:

- `DAc0da.esm:00458C`
- `zDcdUqCyborgAgent`
- FULL: **Yaghra Bioborg - The Agent**
- short name: **The Agent**

This NPC uses:

- template `DAc0da.esm:0043F6` — **Yaghra Chimera - The Agent**
- an **Abyssal Heat Greatsword**
- DAc0da's Charmed FX

The form is therefore a deliberately modified/bioborg presentation of the same Agent boss lineage rather than an unrelated creature.

## Relationship to MQ01 Agent forms

MQ01 alias 9, also named `Agent`, points to:

- `DAc0da.esm:004410`
- `zDcdBossCyborgAgent02`
- FULL: **The Agent**

That boss form also uses `DAc0da.esm:0043F6`, **Yaghra Chimera - The Agent**, as its template.

The support-event bioborg and the later MQ01 Agent boss therefore share a concrete template lineage.

This is strong structural evidence for multiple forms/states of the same Agent encounter concept.

## Scene choreography

SCEN `DAc0da.esm:004593` / `zDcdMqAgentSc01` controls the encounter.

Its package sequence includes:

### Eat Dreugh

`DAc0da.esm:004594` / `zDcdMqAgentEatDreugh`

This package targets a placed `zDcdFeedIdleMarker`, showing the Agent performing a feeding interaction.

### Notice Player

`DAc0da.esm:004595` / `zDcdMqAgentNoticePlayer`

The next scene phase has the Agent react to the player's presence.

### Retreat

`DAc0da.esm:004597` / `zDcdMqAgentRetreat`

The final movement phase sends the Agent toward a retreat marker.

The quest stages include 0, 10, 15, 20, 900, and 999.

## Quest properties

The fragment script contains:

- `SdCall` -> DAc0da sound `zDcdSloadCallLP`;
- `banishFX` -> a master-file visual effect;
- `Alias_Agent` -> quest alias 0.

The scene/fragment code itself is compiled outside the ESM, so exact calls/effect timing remain unresolved.

## Narrative significance

This support event provides **visual foreshadowing** for the later Agent confrontation:

1. a Yaghra/Agent hybrid appears;
2. it feeds on a Dreugh target;
3. notices the player;
4. retreats;
5. later MQ01 uses a separate Agent boss form from the same template family.

No new spoken claims are introduced here. The event should be retrieved as evidence for the Agent's biological/cyborg transformation states and Sload/Yaghra experimentation, not as independent dialogue lore.
