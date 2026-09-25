# Knowledge Extraction Tools

These scripts convert authoritative or high-value source material into **candidate indexes and manifests** for Agent OS knowledge libraries.

They deliberately do not auto-promote generated facts into canonical knowledge. Generated data must retain exact source provenance and pass validation/reconciliation first.

## LEGO Minifigure Reference Corpus

### ingest_lego_minifigure_references.py

Input: current Rebrickable bulk CSV directory.

Core output:
- physical figure census;
- component-level minifigure inventories where bulk part tables are present;
- figure and component image URL manifests;
- set/theme relationships;
- SQLite research index;
- source-file hashes and coverage report.

This is the bulk physical-reference spine. Raw images are not mirrored by this importer.

### materialize_lego_reference_images.py

Input: JSONL reference manifest containing exact source image URLs.

Behavior:
- exact URLs only;
- no crawling;
- explicit `--allow-host` source review;
- rate-limited requests;
- SHA-256 content-addressed storage;
- keeps all source occurrences while deduplicating exact bytes.

### dedupe_lego_reference_images.py

Adds deterministic perceptual dHash values to local image records for near-duplicate review. Requires Pillow. It never deletes or merges records automatically.

### index_ldraw_minifig_patterns.py

Indexes patterned minifigure components in a local LDraw Parts Library, preserves LDraw author/license headers, and can optionally render local previews with LDView.

LDraw is a community reconstruction source; LDraw `Official` does not mean LEGO-authored or LEGO-approved.

### index_ttgames_minifigure_assets.py

Indexes already-extracted files from a legally obtained local TT Games LEGO installation. It hashes/ranks texture, model and metadata candidates for later character resolution and canonical-view rendering.

It does not bypass DRM or extract proprietary archives itself.

### extract_lego_film_reference_frames.py

Requires ffmpeg/ffprobe and a legally obtained local film/video.

Extracts:
- fixed-interval coverage frames;
- scene-change frames;
- source/frame SHA provenance.

Raw frames remain local. Character detection, crops, perceptual dedupe, costume/expression clustering and physical counterpart resolution are later stages.

## Skyrim Knowledge Extraction

### rebuild_skyrim_terminology_index.py
Scans the repository's terminology modules and regenerates counts/index links.

### extract_papyrus_api.py
Input: a PSC source tree such as vanilla, SKSE, po3 Papyrus Extender, PapyrusUtil, or another framework.

Output:
- structured JSON;
- reviewable Markdown signatures;
- ScriptName/parent/declaration source line provenance.

Run one source family at a time so a function's provider remains explicit.

### extract_commonlib_symbols.py
Input: Doxygen XML generated from an exact CommonLibSSE-NG checkout.

Output:
- classes/structs/namespaces/files;
- functions, variables, enums and typedefs;
- source file/line locations.

### capture_xedit_schema.py
Preferred xEdit schema acquisition path. Invokes xEdit's own xDump/xExport definition exporter in RAW or UESPWIKI mode and records executable hash, exact command and upstream provenance.

### extract_xedit_schema.py
Input: exact xEdit/TES5Edit source checkout.

Output:
- lexical candidate inventory of record signatures and source locations.

It is intentionally conservative and is not itself a plugin parser/writer.

## Provenance requirements

Every run should record:
- upstream source;
- exact version/tag/commit where applicable;
- retrieval date;
- tool/script commit;
- local source hashes where possible;
- target game/runtime/media release where applicable;
- storage/rights policy.

Generated high-volume output should normally live in local/index storage unless it is a durable reviewed schema/statistical snapshot appropriate for Git.

## Promotion pipeline

source -> extractor/indexer -> candidate JSON/SQLite/Markdown -> dedupe/version comparison -> validation -> reviewed canonical knowledge

Do not skip validation merely because the source is authoritative: the extractor itself can misparse or omit semantics.
