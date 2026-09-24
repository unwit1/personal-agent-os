# Current-snapshot full lore structure

The Trainwiz / ChronoC0da library now treats the verified **Aethernautics 3.1** and **Sotha Sil Expanded 3.1** packages as the authoritative current-source snapshots for structural lore retrieval. Historical edition archaeology is not an active requirement.

## What is preserved

The exhaustive layer preserves the complete extracted lore-bearing structure rather than only summaries: all book text, Aethernautics messages/quest/entities, all Sotha Sil Expanded dialogue responses and topics, all quest-journal entries, NPC/speaker/place/faction/named-object records, script-carried user-facing/lore strings, script-to-source reference edges, concept-evidence maps, and evidence-scoped relationship graphs.

Coverage is **22 Aethernautics books, 20 messages, 8 NPCs, 28 locations/cells, 1 quest and 90 implementation objects**, plus **49 Sotha books, 250 dialogue topics, 1,147 dialogue responses, 344 NPCs, 144 explicit speakers, 460 cells, 44 journal topics, 7 factions, 543 scripts scanned, 1,291 named implementation objects and 1,441 script/source reference edges**.

## Storage

The complete generated structure is stored in 13 deterministic `corpus/full-structure-XX-of-13.jsonl.gz.b64` segments. `corpus/manifest.json` records the SHA-256 and virtual-file membership of every segment. `technical/unpack-full-structure.py --check` verifies the gzip bytes and every reconstructed virtual file; without `--check` it reconstructs all **53** retrieval artifacts. This packaging is transport/storage only: the reconstructed virtual paths define the logical corpus.

## Modeling boundaries

Aethernautics, Sotha Sil Expanded, and Wheels of Lull remain independent provenance scopes connected by the `tes.mod.trainwiz-chronocoda` graph. Shared concepts and books may be linked, but mod claims do not overwrite Bethesda/base-continuity claims. Current 3.1 text is sufficient for this project's structural goal; historical 2012-2014 wording/version comparison is optional archival research only.

Binary-only/visual semantics are not exhaustively decoded. In particular, *Transmeta Interivatives* points to the vanilla `DivineMetaphysics_text1.tga` / `DivineMetaphysics_text2.tga` assets and remains marked image-dependent rather than treated as missing custom prose.