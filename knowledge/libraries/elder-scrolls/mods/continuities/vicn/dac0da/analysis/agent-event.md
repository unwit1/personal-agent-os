# Agent Event / Yaghra Agent

**Support quest:** `zDcdMqAgent` — Agent Event  
**Source:** `DAc0da.esm:004566`  
**Parent story:** `zDcdMq01` — The Sea of Causality  
**Continuity:** `tes.mod.vicn.dac0da`

## Support quest actor

`zDcdMqAgent` has one unique alias:

- `Agent` -> `DAc0da.esm:00458C`
- Editor ID: `zDcdUqCyborgAgent`
- FULL: **Yaghra Bioborg - The Agent**
- short name: **The Agent**

The actor is placed at `DAc0da.esm:00458E` in the **Sea of Causality** location layer.

The support quest defines stages:

- 0
- 10
- 15
- 20
- 900
- 999

Its generated script references:

- `zDcdSloadCallLP` — a Sload call sound
- a banish visual effect
- the Agent alias

This makes the support record a scripted manifestation/encounter wrapper rather than a dialogue-bearing quest.

## Shared Yaghra-Agent template

The support actor `zDcdUqCyborgAgent` inherits from:

- `DAc0da.esm:0043F6`
- Editor ID: `zDcdBossCyborgAgent01`
- FULL: **Yaghra Chimera - The Agent**

The main MQ01 Agent alias uses another NPC:

- `DAc0da.esm:004410`
- Editor ID: `zDcdBossCyborgAgent02`
- FULL: **The Agent**

That NPC also inherits from `zDcdBossCyborgAgent01`.

A summon variant also exists:

- `DAc0da.esm:0048BB`
- `zDcdSummonYaghraAgent`
- **Yaghra Chimera - The Agent**

DAc0da therefore implements "The Agent" as a small family of Yaghra/bioborg/chimera forms sharing one combat template.

## Main-quest falling-agent event

MQ01 has a dedicated activator:

- `DAc0da.esm:0044F7`
- Editor ID: `zDcdActFallingAgent`

Its script `DcdActFallingAgentScript` directly references:

- MQ01 as `MyQ`
- `NextStage = 80`
- two fall/explosion effects
- a summon effect
- a custom linked reference

The placed activator is:

- `DAc0da.esm:0044F8`
- Editor ID: `zDcdMq01BossActRef`

This is direct mechanical evidence that the Agent is staged as a dramatic falling/summoned encounter during **The Sea of Causality**.

## Main MQ01 Agent boss

MQ01 alias `Agent` points to:

- `DAc0da.esm:004410` — **The Agent**

Its placed actor is:

- `DAc0da.esm:004521`

A second placed instance of the base template `zDcdBossCyborgAgent01` also exists at `DAc0da.esm:0044FC` in the same Ship Graveyard layer.

These records belong to the MQ01 boss/event choreography and should not be confused with the later alternate Agent bodies inside Numidium.

## Ash-pile provenance link to Daggerfall

MQ01 has a dedicated ash-pile container:

- base container `DAc0da.esm:00452B` — `zDcdBossAgentAshChest`
- placed ref `DAc0da.esm:00452C` — `zDcdAgentAshRef`

The ash pile contains:

- Yaghra Chimera armor pieces;
- Abyssal Heat Greatsword;
- `DAc0da.esm:004563` — `zDcdLitemAgentLetter`;
- `DAc0da.esm:004F90` — Totem of Obsession.

### Agent-letter leveled list

`zDcdLitemAgentLetter` consists entirely of six BOOK records:

- `DAc0da.esm:00455D` — Letter from Queen Akorithi
- `DAc0da.esm:00455E` — Letter from King Eadwyre
- `DAc0da.esm:00455F` — Letter from Gortwog
- `DAc0da.esm:004560` — Letter from King of Worms
- `DAc0da.esm:004561` — Letter from The Underking
- `DAc0da.esm:004562` — Letter from Lady Brisienna

These are the Daggerfall/Totem correspondence set already flagged by the BOOK provenance pass as reused-source candidates.

Putting that correspondence specifically in **The Agent's ash pile** is strong DAc0da-specific contextual evidence that this Yaghra Agent is intentionally associated with the **Daggerfall Agent / Totem / Warp in the West** identity cluster.

The text of the reused letters should still be attributed to its original source, while the **placement of those letters as Agent loot** is a DAc0da design fact.

## Relation to later Prisoner material

MQ04 dialogue independently identifies an Agent associated with the Warp in the West as a candidate **Prisoner** and discusses Agent bodies through Ghost Choir 9 / quantum-vibration language.

The MQ01 ash-pile correspondence provides a separate earlier material clue pointing toward the same Daggerfall-Agent identity.

The safest synthesis is:

> DAc0da repeatedly encodes "The Agent" around Daggerfall/Warp-in-the-West material, first through MQ01 boss loot and later through explicit MQ04 Prisoner/Agent exposition.

Do not assume every Yaghra body is the original historical body of the Daggerfall player character; DAc0da repeatedly uses copied, alternate, reconstructed, and possibility-line bodies.
