# Clockwork continuity

**Continuity ID:** `tes.mod.clockwork`  
**Source:** user-provided `Clockwork.esp`  
**Boundary:** mod continuity; do not treat its additions as base Elder Scrolls canon unless separately supported by base-canon evidence.

This directory is the source-backed Clockwork overlay for Lorekeeper. The raw corpus is intentionally retained so summaries, claims, quest graphs, and entity pages can be regenerated without depending on prior model prose.

## What is ingested

- all 13 readable `BOOK` records as individual plain-text files in `books/`, preserving the decoded in-game text and markup;
- a complete archival transcript of all 520 extracted dialogue response strings in `raw/dialogue-transcript.txt.gz`, grouped by `DIAL`/`INFO` FormID;
- all 12 `QUST` records with extracted objectives and journal-stage text in `raw/quest-records.txt.gz`;
- a record-type inventory for the plugin;
- an initial set of provenance-backed lore claim seeds.

## Quest surface identified in the plugin

Player-facing story/side quest records include:

- `CLWKicker01Quest` — *Foot Of The Mountain*
- `CLWStory01Quest` — *Shadow Under The Mountain*
- `CLWStory02Quest` — *Steam-Powered*
- `CLWStory03Quest` — *Crystalline Heart*
- `CLWStory04Quest` — *I Against I*
- `CLWSide01Quest` — *A Bed of Dust*
- `CLWSide02Quest` — *Staff Enchanting*

Other `QUST` records are dialogue, MCM, Shadow-management, or miscellaneous tracking infrastructure.

## Evidence policy

`claim-seeds.json` is not a replacement for the source corpus. Each claim is scoped to this continuity and points back to BOOK or INFO FormIDs. Character testimony remains testimony; uncertainty around the Dwemer disappearance/Kagrenac is preserved rather than converted into objective base-canon fact.

## Next pass

The next useful ingestion pass is to resolve INFO speakers, dialogue conditions, scene ordering, and quest-stage links. That will allow Lorekeeper to generate speaker-attributed transcripts, entity relationship pages, and a proper quest/narrative graph while retaining exact record provenance.
