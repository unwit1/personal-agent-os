# Wheels of Lull retrieval indexes

Continuity: `tes.mod.wheels-of-lull`

The raw source-record shards remain the canonical text layer. These indexes are compact deterministic derivatives used to route retrieval without loading or duplicating the complete corpus.

## Persistent indexes

- `form-routing.json.gz` — preexisting full-corpus routing map for the expected 1,090 persisted lore-bearing FormIDs.
- `lexical-df.json.gz` — preexisting document-frequency statistics for the expected 1,090-document normalized corpus.
- `../locations/cell-index.json.gz` — all 33 LCTN and 103 CELL records with implementation-backed ownership relationships.
- `../normalized/book-source-relations.json` — all 33 BOOK records classified for central-source routing, variant preservation, and unresolved-origin handling.

## Current rebuild state

A fresh full retrieval materialization is **blocked** until these corrupt raw shards are regenerated from the exact verified ESP:

- `../raw/source-records-0151-0200.jsonl.gz`
- `../raw/source-records-0401-0450.jsonl.gz`

The existing compact indexes were produced earlier and report the expected full corpus. They remain useful routing derivatives, but current reproducibility is degraded because the canonical stored raw corpus cannot be reread end-to-end.

Do **not** regenerate a partial index and present it as complete. `technical/build-retrieval-index.py` now fails closed when a raw shard is unreadable.

Repair instructions: `../analysis/repair-plan.md`.

## Materialized retrieval documents

After repair, run:

```bash
python technical/build-retrieval-index.py .
```

from the continuity directory (or pass the continuity path from elsewhere). The builder reads the canonical raw shards and speaker-resolution overlay and writes `.generated-retrieval/` with normalized documents and fresh routing/lexical artifacts.

It also supports a deterministic BM25 smoke/search surface:

```bash
python technical/build-retrieval-index.py . --search "Memory Landfall Towers" --top-k 10
```

Before replacing persistent indexes, verify the regenerated corpus contains exactly **1,090 documents** and reconcile repaired speaker-resolution rows.

## Vector retrieval

Dense/vector embeddings are deliberately **not** treated as canonical Git state because they depend on an embedding model/version. Agents may generate a vector index from the same fully normalized materialization and combine it with the committed lexical/routing baseline. This keeps the continuity provider-neutral and reproducible.

## Provenance guarantee

Retrieval results should route back to a raw source record by FormID/source-record index before being used as evidence. BOOK retrieval should additionally consult `book-source-relations.json` so externally reused works route to central source history without erasing the Wheels-local variant.

Dossiers, claim seeds, and compact indexes are navigation/synthesis layers, not substitutes for source evidence.
