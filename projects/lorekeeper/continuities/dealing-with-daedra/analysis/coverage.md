# Dealing with Daedra import coverage

## Completed
- Direct TES5 plugin parsing, including compressed records and `XXXX` extended-size subrecords.
- Full record inventory: 20,733 records.
- FormID provenance split between mod-added records and master overrides.
- Complete decoded non-EDID text-bearing record corpus: 7721 records across 29 gzip-compressed JSONL shards.
- BOOK, DIAL/INFO, MESG, QUST, SCEN, NPC_, FACT, CELL, WRLD and other named/described record classes retained.
- Papyrus source string-literal inventory.
- Printable-string capture for the two PEX files lacking source.

## Known gaps / interpretation limits
- Speaker attribution is not yet fully normalized. INFO/DIAL evidence is preserved for a later speaker-resolution pass.
- Papyrus binaries are not decompiled. Source exists for essentially all compiled scripts except `TIF__056051EE.pex` and `TIF__0572C7F4.pex`; printable strings from those two are retained.
- Meshes, textures, audio, facegen, and other non-text assets are intentionally excluded from the lore repository.
- This pass imports source evidence; higher-order claims, relationships, chronology, reliability judgments, and contradictions remain follow-up analysis.
