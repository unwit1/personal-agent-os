# Skyrim Knowledge Extraction Tools

These scripts convert authoritative source trees into **candidate indexes** for the Skyrim Modding Knowledge Repository.

They deliberately do not auto-promote generated facts into canonical knowledge. Generated data must retain exact source provenance and pass validation/reconciliation first.

## Tools

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

This is intended to become the native API/symbol graph.

### capture_xedit_schema.py
Preferred xEdit schema acquisition path. Invokes xEdit's own xDump/xExport definition exporter in RAW or UESPWIKI mode and records executable hash, exact command and upstream provenance.

### extract_xedit_schema.py
Input: exact xEdit/TES5Edit source checkout.

Output:
- lexical candidate inventory of record signatures and source locations.

It is intentionally conservative and **not** a plugin parser or writer. A later phase should consume xEdit's actual schema structures/export to produce field/subrecord semantics.

## Provenance requirements

Every run should record:
- upstream repository;
- exact tag or commit SHA;
- retrieval date;
- tool/script commit;
- target game/runtime where applicable.

Generated high-volume output should normally be stored in local/index storage unless it is a durable reviewed schema snapshot appropriate for Git.

## Promotion pipeline

source checkout -> extractor -> candidate JSON/Markdown -> dedup/version comparison -> validation -> reviewed canonical knowledge

Do not skip the validation stage merely because the source is authoritative: the extractor itself can misparse or omit semantics.


## xEdit schema strategy

Prefer xEdit-native export via `capture_xedit_schema.py`. The lexical `extract_xedit_schema.py` remains a fallback/cross-check, not the authoritative schema parser. See `knowledge/libraries/skyrim-modding/research/xedit-native-schema-extraction.md`.
