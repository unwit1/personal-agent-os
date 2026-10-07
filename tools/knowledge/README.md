# Knowledge Extraction Tools

These scripts convert authoritative or high-value source material into **candidate indexes and manifests** for Agent OS knowledge libraries.

They deliberately do not auto-promote generated facts into canonical knowledge. Generated data must retain exact source provenance and pass validation/reconciliation first.

## LEGO / Brickmen integration

LEGO customs and custom-minifigure knowledge extraction tooling is canonical in `unwit1/brickmen`.

Agent OS should route LEGO/custom-minifigure ingestion and research jobs to Brickmen rather than maintaining duplicate local tool copies or canonical LEGO datasets here. Cross-project orchestration may reference Brickmen outputs through stable repository paths/provenance.

## Elder Scrolls / Skyrim integration

Elder Scrolls content does not live in Agent OS (operator decision, 2026-10-07):

- Lore (continuities, books, claims, entities) is canonical in `unwit1/knowledge-tes`. The former `projects/lorekeeper/` copy was retired; knowledge-tes holds every file it had.
- Skyrim/SSE modding knowledge and tooling is canonical in `unwit1/sse-modforge`. That includes the xEdit, Papyrus and CommonLibSSE extractors formerly here (`capture_xedit_schema.py`, `extract_xedit_schema.py`, `extract_papyrus_api.py`, `extract_commonlib_symbols.py`), the Mod Factory validators, and `projects/simonrim-balancer/`. See its `MIGRATION.md` and `integration/migrated-from-personal-agent-os-2026-10-07.json`.

Agent OS routes Elder Scrolls ingestion and research jobs to those repositories rather than keeping local copies.

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
