# BF Books ESO book corpus

Direct extraction of the `BOOK` records from the user-supplied `BF_Books_ESO.esp`.

- Source type: compiled Skyrim plugin / ESO book corpus
- Source file: `BF_Books_ESO.esp`
- Source SHA-256: `636cd8138f7b5eef3d10c57791ed894610cc3da571f76934eac0193f827cddc7`
- Masters: `Skyrim.esm`
- Extracted BOOK records: **4,277**
- Empty-text BOOK records preserved: **4**
- Unique display titles: **4,244**
- Unique text bodies: **4,255**
- Batch size: **50 books per commit** (final batch contains 27)
- Storage: newline-delimited JSON; each record preserves FormID, editor ID, title, source/hash metadata, and full decoded book text.

## Provenance boundary

All editor IDs in this supplied compilation use the `ZOS` prefix, strongly indicating ESO-derived material. The plugin is retained as the direct extraction provenance and is not, by itself, treated as proof of original per-record provenance. Individual texts can be verified later against ESO game data, UESP, or The Imperial Library.

## Layout

- `batches/` — full-text JSONL, 50 books per file/commit.
- `batch-index.json` — deterministic batch boundaries and hashes (added when the corpus is complete).
- `source-manifest.json` — complete record crosswalk (added when the corpus is complete).
- `INDEX.md` — human-readable title index (added when the corpus is complete).
