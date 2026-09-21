# UNSLAAD continuity

**Continuity ID:** tes.mod.vicn.unslaad  
**Parent continuity:** tes.mod.vicn  
**Primary source:** user-provided translated Unslaad.esm (UNSLAAD 3.0.6)  
**Source SHA-256:** 1dabd2782ad6f4af565ace37fbe198c497d18f7a9ae0d2f36d892d743454b05b  
**Source size:** 10,432,096 bytes

UNSLAAD is stored under the shared **Vicn continuity** with **VIGILANT**, **GLENMORIL**, and **DAc0da**. Source-level claims remain attributable to UNSLAAD unless another Vicn work independently supports them. Nothing in this layer is silently promoted into official Elder Scrolls canon.

## Direct ESM inventory

The deterministic parser pass found **44,103 records**, including:

- 833 INFO records with **1,015 embedded response strings**
- 661 DIAL records
- 52 QUST records
- 517 NPC_ records
- 50 BOOK records
- 98 MESG records
- 59 SCEN records
- 1,740 CELL records
- 7 WRLD records

The translated ESM is not localized, so its English dialogue and book text can be extracted directly without external string tables.

## Current coverage

### Numbered main quest

The lore-bearing dialogue/scene pass is complete for all ten numbered main quests, from **Falling Cat** through **Under the Elder Tree**.

### Side quests and shared dialogue

High-value side/generic material is now ingested, including:
- Fluffy's Secret
- Dragon Souls
- Arkved
- Snow Guardian
- Liturgy of I
- Watcher from the Third Era
- Boss Rush
- Sermon of Khev
- VS Dreugh King
- radiant/repeatable dialogue families

The shared **zzzCrbGeneric** audit resolved:
- **217 INFO rows**
- **120 DIAL topics**
- **28 named speaker labels**

using GetIsID speaker conditions.

### Epilogue

The Epilogue quest's **106 INFO responses** have been analyzed for Ulliss/Lizz, Lizz/Fluffy-Ja'cobee, and Lizz/Aisha relationship evidence.

### Scene reconciliation

All **59 SCEN records** are accounted for:
- **53** contain DIAL-backed dialogue actions, all mapped to already-ingested dialogue families;
- **6** contain no DIAL actions and are retained as technical/orchestration scenes.

There is therefore no hidden SCEN dialogue backlog in this ESM version.

### Books

The source corpus preserves **50 / 50 BOOK records** as individual FormID-keyed files under books/source/.

This includes:
- all seven Loveletter fragments;
- the full Loveletter From the Fifth Era;
- Sermon 37;
- Sermon 0;
- Vivec and Molag Bal;
- Ysmir the Forefather, Volume IV;
- Harakk Warrior's Final Note;
- Note from Fluffy;
- all gameplay/spell/summon books.

Reused/apocryphal texts remain provenance-distinct from UNSLAAD-authored material.

### No-dialogue boss/trial quests

Named boss/trial families have a structural index even when they contain no ordinary INFO dialogue, including:
- Trial of the Gods;
- Idol of Magnar;
- Last Giant of Jhunal;
- Jill trials;
- Ysgramor trial;
- Priest of Jhunal;
- Woodland Man hunt.

## Major established VICN links

- **Ja'cobee / Ulliss / Aisha / EGG:** direct named and conceptual overlap with GLENMORIL; UNSLAAD now independently contains Ja'cobee/EGG statements.
- **Jhunal / Owls / Saarthal / Night of Tears / Magnus-fire:** independently recurring in UNSLAAD, VIGILANT, and GLENMORIL.
- **Jhunal / Laza / dragon experimentation:** UNSLAAD Gray Owl names Laza among failed experiments; VIGILANT Jhunal independently links Laza to dragon harvesting.
- **Arkved / Oneiromancer:** direct explicit link in both UNSLAAD and GLENMORIL.
- **Orlando / Blue Star / Owl / Elder Wood:** direct Orlando recurrence plus Owl/Atmora material.
- **Mnemo-Li / Blue Orphan / dream without a dreamer:** distinctive vocabulary shared with GLENMORIL.
- **Loveletter / Nu-Mantia:** reused apocryphal substrate actively interpreted by UNSLAAD through Liturgy of I and Khev.
- **Hjalti / Alcaire:** multiple internally consistent UNSLAAD references, retained as a comparison thread rather than a forced Talos identity.

## Provenance policy

- Quest structure, aliases, GetIsID/GetIsAliasRef conditions, scene bindings, record placements, and exact actor forms are implementation evidence.
- Character explanations remain attributed testimony unless separately corroborated.
- Reused official/apocryphal texts are not attributed to Vicn merely because copies exist in Unslaad.esm.
- Colored Owl/Jhunal/Orlando forms remain densely linked but are not globally merged into one body/person.
- Translation wording is preserved when terminology is uncertain.
- Contradictory or unstable identity evidence is retained rather than normalized away.

## Remaining ingestion frontier

Basic text/dialogue discovery is now substantially complete. The next high-value work is deeper structural lore analysis:

1. placed-reference and cell-context analysis for major entities, relics, books, and bosses;
2. VMAD/Papyrus-property and quest-fragment orchestration where it can establish narrative mechanics without inventing hidden script bodies;
3. artifact, spell, death-item, faction, and creature relationship indexing;
4. deeper concept synthesis for Lyg, Khev, Radiance/Name, Atmoran ice, and Woodland-Man memory/story mechanics;
5. direct cross-comparison against the increasingly complete DAc0da corpus;
6. external provenance verification for the few reused BOOK texts whose authorship/source class is still uncertain.
