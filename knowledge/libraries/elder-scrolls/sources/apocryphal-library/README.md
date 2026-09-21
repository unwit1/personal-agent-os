# Apocryphal Library book corpus

Direct extraction of the `BOOK` records from the user-supplied `LB_ApocryphaBooks.esp`.

- Source type: compiled Skyrim plugin / book corpus
- Source file: `LB_ApocryphaBooks.esp`
- Source SHA-256: `dd4a9f5b523e4aae5b257c2528bd17bfd6545ed0a29a097d5a047d9cd6a79324`
- Masters: `Skyrim.esm`, `Update.esm`, `Dawnguard.esm`, `Dragonborn.esm`
- Extracted `BOOK` records: **784**
- Empty-text `BOOK` records preserved: **2**
- Extraction: direct Bethesda plugin record parsing; `FULL` is the title and `DESC` is preserved as decoded UTF-8 text.
- Skyrim book markup, page breaks, image tags, spelling, and punctuation are retained.

## Provenance policy

This plugin is treated as a **compilation source**, not as authority for the original continuity of every text it contains. Presence in this ESP does not by itself establish that a text is Bethesda-canonical, developer/obscure material, or authored by the compilation mod.

Individual origins should be resolved separately and linked to official game, developer, Imperial Library, mod, or community sources when evidence is available. Until then, claims drawn only from this corpus should cite the Apocryphal Library compilation and retain an unresolved-origin/source-status marker.

## Browse

- [`INDEX.md`](./INDEX.md) — alphabetical human-friendly index of all 784 extracted books
- [`PROVENANCE.md`](./PROVENANCE.md) — origin-verification policy and current triage counts
- [`COLLECTIONS.md`](./COLLECTIONS.md) — compiler-defined containers and leveled-list groupings
- [`provenance-triage.json`](./provenance-triage.json) — per-record provenance status and discovery hints
- `books/` — extracted text files, named with FormID + title slug for stable uniqueness
- `source-manifest.json` — title/editor-ID/FormID/path/text-hash crosswalk and source metadata
- `technical/record-counts.json` — plugin record inventory from this extraction pass
