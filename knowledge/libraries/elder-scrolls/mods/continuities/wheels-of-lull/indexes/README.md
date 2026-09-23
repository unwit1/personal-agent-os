# Wheels of Lull retrieval indexes

Continuity: `tes.mod.wheels-of-lull`

The raw source-record shards remain the canonical text layer. These indexes are compact deterministic derivatives used to route retrieval without loading or duplicating the complete corpus.

## Persistent indexes

- `form-routing.json.gz` — all 1,090 persisted lore-bearing FormIDs mapped to `[source_record_index, record_type, raw_shard]`.
- `lexical-df.json.gz` — document-frequency statistics across the 1,090-document normalized corpus for deterministic lexical retrieval.
- `../locations/cell-index.json.gz` — all 33 LCTN and 103 CELL records with implementation-backed ownership relationships.

## Materialized retrieval documents

Run:

```bash
python technical/build-retrieval-index.py .
```

from the continuity directory (or pass the continuity path from elsewhere). The builder reads the canonical raw shards and speaker-resolution overlay and writes `.generated-retrieval/` with normalized documents and fresh routing/lexical artifacts.

It also supports a deterministic BM25 smoke/search surface:

```bash
python technical/build-retrieval-index.py . --search "Memory Landfall Towers" --top-k 10
```

## Vector retrieval

Dense/vector embeddings are deliberately **not** treated as canonical Git state because they depend on an embedding model/version. Agents may generate a vector index from the same normalized materialization and combine it with the committed lexical/routing baseline. This keeps the continuity provider-neutral and reproducible.

## Provenance guarantee

Retrieval results should route back to a raw source record by FormID/source-record index before being used as evidence. Dossiers and claim seeds are navigation/synthesis layers, not substitutes for source evidence.
