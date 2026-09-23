# Dealing with Daedra

Isolated Elder Scrolls mod continuity for **Dealing with Daedra**.

- Continuity ID: `tes.mod.dealing-with-daedra`
- Primary source: user-provided `DealingwithDaedra.esp`
- ESP SHA-256: `c278b1a9ccaa7080579a6421a0c21d6b0513a2ad8263048c3c96208bd6a19133`
- Import policy: mod-added lore may reference Bethesda continuity but cannot overwrite or silently become base canon.

## Import coverage

This source import preserves the complete decoded text-bearing corpus from the ESP:

- **20,733** plugin records inventoried.
- **19,793** mod-added records and **939** master overrides distinguished by FormID provenance.
- **332 BOOK** records, including **295** with non-empty body text.
- **889 DIAL** topics and **1,809 INFO** records with **2,674** response strings.
- **557 MESG** records and **561** button strings.
- **19 QUST**, **3 SCEN**, **216 NPC_**, **46 FACT**, **247 CELL**, and **8 WRLD** records represented in source/index layers.
- All decoded text-bearing record fields are retained in `source-records/`, including names/descriptions for items, spells, magic effects, activators, containers, furniture, and other record classes.
- Papyrus source string literals are inventoried in `technical/`; two compiled scripts without source are retained as printable-string evidence.

## Browse

- `source-records/` — canonical, loss-minimized text-bearing ESP evidence with FormID, record type, editor ID, source scope, text tags, and decoded text.
- `indexes/book-index.md` — book/note catalog.
- `indexes/dialogue-topic-index.md` — dialogue topic catalog.
- `indexes/quest-index.md` and structured entity/location indexes — navigation into quests, actors, factions, cells, worlds, and scenes.
- `technical/` — Papyrus string evidence and compiled-only script-string evidence.
- `raw/record_counts.json` — complete plugin record-type inventory.
- `analysis/coverage.md` — extraction, semantic-closeout, and interpretation-limit notes.
- `analysis/semantic-pass-13-closeout.md` — source-exhaustion audit and final semantic-pass status.
- `continuity.json` — current structured coverage and analysis counters.

## Provenance rule

All claims derived from this folder default to `tes.mod.dealing-with-daedra`. Records overriding Skyrim/Dawnguard/HearthFires/Dragonborn forms remain explicitly marked as overrides. They are evidence about this mod's continuity, not automatic corrections to Bethesda canon.

## Semantic-analysis status

Semantic passes **01–13** are complete, and the lore-bearing source corpus has been source-exhaustion audited. Long-form written sources, operational dialogue, bulletin notes, artifacts, institutions, social/economic systems, chronology, contradictions, source reliability, technical residuals, and provenance/deduplication candidates now have dedicated analysis layers.

Remaining work is intentionally narrower normalization/refinement rather than missing bulk lore extraction:

- **171** mod-added INFO records are not uniquely attributable to one individual NPC from the deterministic positive-Subject-`GetIsID` rule. Role, faction, state, or group attribution is preserved where supported; named speakers are not guessed.
- **47** of those INFO records have positive Subject faction conditions and are represented through contextual speaker-role groups.
- **7** identity questions remain explicitly uncertain in `claims/unresolved-identity-index.jsonl`.
- The Gallus/Mercer encoded journal and `Fundaments of Alchemy` remain central-source normalization candidates pending stable canonical-work linkage.
- Short raw records remain available for future micro-queries, but no remaining lore-bearing source gap requires re-reading the ESP.

See `continuity.json`, `analysis/speaker-resolution-pass-02.md`, and `analysis/semantic-pass-13-closeout.md` for the current authoritative state.
