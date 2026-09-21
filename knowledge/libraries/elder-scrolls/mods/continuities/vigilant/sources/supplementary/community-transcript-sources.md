# Community transcript and walkthrough sources

Continuity: `tes.mod.vigilant`

These sources are useful for recovering dialogue/context that is not yet persisted in the local ESM extraction, but they are **secondary/community evidence**.

They must never silently outrank direct ESM records.

## English Translation / Voiced Addon — Nexus Mods

Title:
- **VIGILANT - English Translation (Plus Voiced Addon)**

Host:
- Nexus Mods

Relevant provenance use:
- translation/voice metadata;
- named voice-role pairings;
- useful identity hints such as the credited role **Bal-Rahel**;
- confirmation that Facis and Reyda are distinct voiced roles.

URL:
- https://www.nexusmods.com/skyrimspecialedition/mods/11894

Evidence class:
- `translation_metadata`

Do not use voice credits alone to infer full biography or metaphysical identity.

## Elder Scrolls Mods Wiki — community transcripts

Host:
- The Elder Scrolls Mods Wiki / Fandom

Relevant pages used in current ingestion:
- **Reyda**
- **Hilda the Witch**
- **Jacob**
- **Old Guilts**
- **No Mercy**
- **Loose Ends**

Examples of useful recoveries:
- Reyda's branching *The Endless Fall* dialogue;
- Hilda's account of Reyda's earlier Ivarstead life and Molag Bal transformation;
- Jacob/Bal/Rahel community transcript material;
- quest-order and encounter context;
- Joshua-related Old Guilts walkthrough context.

Evidence class:
- `community_transcript`

Caution:
- wiki summaries can contain interpretation;
- wording/version may differ from current VIGILANT/translation build;
- use direct quotations sparingly and verify against ESM when source bytes become available.

## La Confrérie des Traducteurs — VIGILANT guide/wiki

Host:
- La Confrérie des Traducteurs

Relevant current use:
- Act II guide material describing Facis as Lamae's former servant/steward;
- post-Blood-Matron Facis merchant/warning role;
- memory-guide contextual descriptions.

Evidence class:
- `community_walkthrough_translation`

Caution:
- walkthrough narration is not the same as direct plugin dialogue;
- use for context, not to overwrite ESM structure.

## Retrieval rule

When information exists only here, phrase it internally as:

- `supplementary community transcript says...`
- `community walkthrough describes...`

When direct ESM evidence is later recovered:
1. keep the community source;
2. compare wording;
3. promote the direct ESM evidence;
4. retain discrepancies/version differences explicitly.

## Current dossiers using this layer

- `entities/characters/facis.md`
- `entities/characters/reyda.md`
- `entities/characters/rahel.md`
- `entities/characters/joshua.md`
- `analysis/windhelm-maiden-statue-incident.md`
