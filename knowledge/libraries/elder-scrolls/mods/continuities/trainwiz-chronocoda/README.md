# Trainwiz ChronoC0da

Umbrella continuity graph for related Trainwiz projects. Verified current-source ingestion now includes **Sotha Sil Expanded 3.1**, **Aethernautics 3.1**, and the existing **Wheels of Lull** corpus.

Each source remains independently provenance-scoped. Shared books and concepts are linked through explicit relations rather than deduplicating away local editions, wording changes, or release chronology.

## Full current-snapshot structure

The verified Aethernautics 3.1 and Sotha Sil Expanded 3.1 sources now have an exhaustive lore-structure layer under `corpus/`. It reconstructs 53 logical retrieval artifacts from 13 validated transport segments and covers all extracted books, dialogue, journals, NPCs/speakers, places, factions, named objects, script lore strings, script/source edges, concept evidence and relationship graphs.

Historical edition archaeology is intentionally a cold/optional backlog. The active work is semantic synthesis over the current snapshots. See `FULL_STRUCTURE.md`, `full-structure-ingestion.json`, `corpus/manifest.json`, and `technical/unpack-full-structure.py`.
