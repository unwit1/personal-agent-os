# Dealing with Daedra import coverage

## Source extraction complete
- Direct TES5 plugin parsing, including compressed records and `XXXX` extended-size subrecords.
- Full record inventory: **20,733** records.
- FormID provenance split between mod-added records and master overrides.
- Complete decoded non-EDID text-bearing record corpus: **7,721** records across **29** gzip-compressed JSONL shards.
- BOOK, DIAL/INFO, MESG, QUST, SCEN, NPC_, FACT, CELL, WRLD and other named/described record classes retained.
- Papyrus source string-literal inventory.
- Printable-string capture for the two PEX files lacking source.

## Semantic closeout complete
Semantic passes **01–13** have been completed. Pass 13 used small durable batches and finished with a source-exhaustion audit of the lore-bearing corpus.

Verified closeout coverage includes:
- long-form written lore and operational text;
- high-value and short-form lore-bearing dialogue;
- all **41** `dealsinfonote` bulletin-board INFO records;
- artifacts, locations, chronology, relationships, recruitment/coercion/economy layers, contradictions, and source-reliability notes;
- all **3** SCEN records, which contain no independent extracted phase prose beyond dialogue already represented in INFO/DIAL evidence;
- both compiled-only scripts, `TIF__056051EE.pex` and `TIF__0572C7F4.pex`, whose retained printable strings contain boilerplate/function metadata rather than additional lore prose;
- provenance and deduplication refinement, including verified work identity for the Gallus encoded journal and `Fundaments of Alchemy`; Gallus is a whitespace-normalized exact Skyrim text reuse, while `Fundaments of Alchemy` is a near-exact established-work variant inside an Arcadia-specific wrapper.

No remaining gap requires re-reading the entire ESP to make this continuity usable by Lorekeeper.

## Remaining interpretation / normalization limits
- **1,636 / 1,807** mod-added INFO records are deterministically resolved to one named Subject NPC, covering **2,472 / 2,674** response strings.
- The remaining **171** INFO records are not a backlog of unanalyzed lore. They use faction, generic-role, state, race/location, multi-actor, or other contextual routing that does not safely identify one individual speaker.
- **47** of the remaining INFO records have positive Subject faction conditions and are represented in `indexes/contextual-speaker-role-index.md`.
- Multi-actor/state variants are retained at narrative-entity or role-group level where the plugin deliberately permits multiple speakers.
- **7** character/faction/source identity questions remain explicitly unresolved rather than being promoted from inference to fact.
- The two high-value reused-book identities are no longer unresolved: their work identities are verified, but stable central Personal Agent OS work/source records are still pending.
- Papyrus binaries were not generally decompiled; source exists for essentially all compiled scripts except the two audited compiled-only PEX files above.
- Meshes, textures, audio, facegen, and other non-text assets are intentionally excluded from the lore repository.
- Short raw records remain preserved for future targeted micro-queries even when they did not warrant standalone dossiers or claims during the semantic pass.

Authoritative closeout references:
- `../continuity.json`
- `semantic-pass-13-closeout.md`
- `speaker-resolution-pass-02.md`
- `../indexes/contextual-speaker-role-index.md`
- `../indexes/multi-actor-speaker-groups.md`
- `../claims/unresolved-identity-index.jsonl`
- `refinement-pass-14-claim-integrity-qc.md`
- `refinement-pass-15-book-provenance-verification.md`
- `../normalized/book-source-relations.json`


## Refinement pass 16

- Evidence-locator QC added `indexes/evidence-locator-index.jsonl` with 14 locator records: 13 Papyrus script filenames and the recovered corrupt-signet MESG locator.
- Papyrus claim evidence totals 18 references across 13 unique script names; full PSC bodies are not currently persisted, so byte/line revalidation remains archive-dependent.
- `dwd-078` is the only indexed claim whose listed evidence is entirely Papyrus-based.
- Two semantic duplicate pairs were normalized without deleting historical IDs: `dwd-091` / `dwd-223`, and `dwd-118` / `dwd-173`.
- Relation layer now contains 21 records: 7 conflicts, 7 uncertainty boundaries, and 7 specialized relations, with zero cross-role overlap after QC.
- No new named-speaker promotions were made; the remaining 171 context-routed INFO records remain intentionally conservative.


## Refinement pass 17

- The two verified reused works now have stable central normalized work records:
  - `tes.work.gallus-encoded-journal`
  - `tes.work.fundaments-of-alchemy`
- DWD `normalized/book-source-relations.json` routes both local BOOK witnesses to those work IDs while preserving local presentation, wrapper, placement, and variant metadata.
- Central work identity is now resolved for both high-value candidates; no single canonical normalized text has been elected because first-party game corpora are not yet normalized broadly enough.
