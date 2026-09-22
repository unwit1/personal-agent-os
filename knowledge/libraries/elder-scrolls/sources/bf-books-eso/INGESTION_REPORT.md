# BF Books ESO ingestion report

## Result

- Source: `BF_Books_ESO.esp`
- SHA-256: `636cd8138f7b5eef3d10c57791ed894610cc3da571f76934eac0193f827cddc7`
- Source master: `Skyrim.esm`
- Parsed `BOOK` records: **4,277**
- Records with non-empty text: **4,273**
- Empty `DESC` records preserved: **4**
- Total extracted text: **7,835,819 characters** / **7,837,308 UTF-8 bytes**
- Unique display titles: **4,244**
- Duplicate-title instances: **33**
- Unique text bodies: **4,255**
- Duplicate-text instances: **22**
- Median book length: **960 characters**
- Longest book length: **194,689 characters**
- Editor IDs beginning with `ZOS`: **4,277/4,277**

## Encoding and fidelity

The plugin strings use Windows-1252 punctuation in some records. They were decoded as Windows-1252 and written as UTF-8, preserving curly quotes, em dashes, bullets, accented characters, and the original Skyrim/HTML-like book markup. No normalization was applied to `[pagebreak]`, `<p>`, `<br>`, `img://`, spelling, line breaks, or punctuation.

## Empty records

- `01009B2C` / `ZOScatalogcostumes` — Catalog of costumes
- `01009B2D` / `ZOScatalogmomentos` — Catalog of momentos
- `01009B2B` / `ZOScatalogmounts` — Catalog of mounts
- `01009B2A` / `ZOScatalogpets` — Catalog of pets

## Stored representations

- `books/` — one exact UTF-8 text file per BOOK record.
- `source-manifest.json` — stable FormID/editor-ID/title/path/hash crosswalk and extraction metadata.
- `INDEX.md` — alphabetical human-readable catalog.
- `books.jsonl` — complete machine-readable full-text corpus.
- `books.sqlite3` — local searchable database with an FTS5 full-text index.
- `technical/record-counts.json` — plugin record inventory.
- `technical/duplicates.json` — duplicate-title/text diagnostics.

## Provenance boundary

All 4,277 editor IDs use the `ZOS` prefix, strongly indicating ESO-derived material in this compilation. The supplied Skyrim plugin remains the direct extraction source, so the corpus preserves that compilation provenance rather than treating the plugin itself as proof of the original source of every individual text. Per-record ESO provenance can be verified later against direct ESO game data, UESP, or The Imperial Library when needed.