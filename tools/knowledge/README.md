# Knowledge Extraction Tools

These scripts convert authoritative or high-value source material into **candidate indexes and manifests** for Agent OS knowledge libraries.

They deliberately do not auto-promote generated facts into canonical knowledge. Generated data must retain exact source provenance and pass validation/reconciliation first.

## LEGO / Brickmen integration

LEGO customs and custom-minifigure knowledge extraction tooling is canonical in `unwit1/brickmen`.

Agent OS should route LEGO/custom-minifigure ingestion and research jobs to Brickmen rather than maintaining duplicate local tool copies or canonical LEGO datasets here. Cross-project orchestration may reference Brickmen outputs through stable repository paths/provenance.

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
