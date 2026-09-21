# Funeral side quest — structural separation pass

Continuity: `tes.mod.vigilant`

Quest:
- `QUST 02129BCA`
- EditorID: `zzzCHSubQuest04`
- Title: **Funeral**
- Act 4 starter-list member

## Core finding

The **Funeral** side quest is structurally distinct from the **Funeral Temple / Manthar / Nenyond / Silorn** historical complex.

This distinction matters because keyword searches for “Funeral” otherwise collapse two different source clusters.

## Quest aliases

A prior whole-plugin structural pass found that `zzzCHSubQuest04` centers on aliases:

- `Sister`
- `SisterDead`

The retained ESM analysis did not find the quest structurally referencing:
- `NPC_ 021146D9` / Sorcerer Manthar;
- `ACHR 021146DA` / the placed Manthar boss.

Its VMAD/stage layer likewise did not establish a Manthar transformation or Manthar-owned quest route.

Therefore:

**Funeral side quest ≠ explanation for Manthar's Bone Lord state.**

## Separate Funeral Temple complex

The separate historical/environmental cluster includes:
- **Nenyond's Underground Priory**;
- **Funeral Temple**;
- Sorcerer Manthar / Bone Lord;
- Abbot Silorn remains and relic imagery;
- the Eight Saints tradition.

Those records remain important, but their shared funeral language should not be treated as evidence that `zzzCHSubQuest04` governs them.

## Current quest ontology

The strongest current reconstruction is intentionally narrow:

**Funeral → Act 4 side quest → Sister/SisterDead alias pair → detailed narrative body not yet persisted.**

The Sister/SisterDead pairing suggests a living/dead-state relationship, but the exact mechanism must remain unresolved until alias bases, dialogue, stages, or scripts are recovered.

Do not yet encode:
- Sister as a known saint;
- SisterDead as a resurrection state;
- a relationship to Silorn, Nenyond, or Manthar;
- a specific burial or funeral ritual.

## Why this is useful

This pass removes a major false-positive path in future ingestion.

Searches for “Funeral” should now branch into:

1. **`zzzCHSubQuest04` / Funeral** — Sister/SisterDead side quest.
2. **Funeral Temple** — Nenyond/Manthar/Silorn historical location complex.

They should only be rejoined if future records explicitly connect them.

## Required future extraction

Priority recovery:
- resolve `Sister` and `SisterDead` to their base/reference FormIDs;
- extract quest-conditioned INFO records;
- extract objectives/stages and SCEN ownership;
- identify placements/cells;
- ingest PEX fragment bodies if available.

## Current classification

**High-confidence structural separation; narrative content still incomplete.**

## Canon boundary

The Funeral side quest and its Sister/SisterDead implementation are VIGILANT-continuity material.
