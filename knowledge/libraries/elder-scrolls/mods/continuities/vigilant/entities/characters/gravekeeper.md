# Gravekeeper

- Continuity: `tes.mod.vigilant`
- Role: Act 4 side-quest figure
- Quest: **The Saint's Corpse** / `zzzChSubQuest15`
- Dialogue scenes:
  - `SCEN 0255BC98` — Gravekeeper
  - `SCEN 0255BCAA` — Gravekeeper
- Associated location: **Gravekeeper's House** (`CELL 025585CE`)
- Exact NPC FormID: not yet persisted in the current browsable repository corpus

## Structural placement

The Gravekeeper is a dialogue-bearing character in the Act 4 side quest **The Saint's Corpse**.

Two dedicated scenes resolve to the Gravekeeper, and Coldharbour's door graph independently places **Gravekeeper's House** as an interior directly connected to the main Coldharbour exterior hub.

This gives the character a firm structural footprint even though the currently browsable repository layer does not yet preserve a full Gravekeeper dialogue dossier.

## Not the current best match for Vision stanza 6

The character's title makes the Gravekeeper an obvious semantic candidate for stanza 6 of `BOOK 02054ED0` / *A Vision in Malada*, which describes a grave keeper and a returning grave robber.

However, the current evidence map explicitly prefers **Melus Petilius**.

The reason is evidentiary rather than thematic:

- Melus directly says the graverobber always returns;
- Melus directly says he repeatedly crushes the graverobber's skull;
- those actions closely match the stanza;
- no equally specific Gravekeeper dialogue has yet been persisted.

Therefore Lorekeeper should **not** merge Gravekeeper with the stanza-6 figure based on title alone.

## Current ontology

At present the Gravekeeper should be modeled as:

**named Act 4 quest character with dedicated scenes and house/location anchor; detailed biography pending dialogue-level extraction.**

Do not infer:
- that Gravekeeper is Melus;
- that Gravekeeper is the returning graverobber;
- that Gravekeeper is the stanza-6 prophecy figure;
- that The Saint's Corpse necessarily concerns the same burial cycle as Paladin Melus.

## Relationship map

- **Gravekeeper → dialogue-bearing figure in → The Saint's Corpse**
- **Gravekeeper → associated with → Gravekeeper's House**
- **Gravekeeper → distinct from → Melus Petilius**
- **Vision stanza 6 → currently maps to → Melus, not Gravekeeper**

## Canon boundary

The Gravekeeper and The Saint's Corpse are VIGILANT-specific continuity material.
