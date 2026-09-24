# Wheels of Lull Post-Ingestion Analysis

Status: **source ingestion exhausted for the supplied ESP; core analysis complete; only external BOOK provenance/edition follow-up remains**.

Completed products:
- complete 1,090-record core source corpus with all stored raw shards readable;
- deterministic raw-shard repair for the former 151-200 and 401-450 gaps;
- strict CTDA integrity resolution for all 410 INFO records;
- broader contextual/candidate speaker analysis retained in the dialogue layer;
- major character evidence dossiers;
- complete 33-location / 103-cell place index and high-value place dossiers;
- artifact/technology dossiers;
- faction/group dossiers;
- 31 normalized core claims;
- 7 canon/tension handling records;
- machine-readable retrieval index with 76 analysis entries, including all 14 topic dossiers;
- deterministic normalization and SHA-256 fingerprints for all 33 BOOK records;
- BOOK provenance passes 01-05 plus a search audit and KINMUNE variant pass;
- central-source links for verified KINMUNE, Tatterdemalion, and Xal-Gosleigh reuse;
- full physical audit of all 36,824 plugin records;
- separate 370-record implementation-evidence layer for omitted player-facing/structural evidence, plus 16 field augmentations.

## Dialogue integrity

All **410 INFO records** are now source-readable.

A strict, reproducible CTDA pass resolves **332** INFO records and intentionally leaves **78** unresolved when direct equality `GetIsID` or a uniquely mapped equality `GetIsVoiceType` is absent. The independently regenerated result for the previously readable 358-record subset is exactly the old baseline (**288 resolved / 70 unresolved**); the 52 repaired INFO records add **44 resolved / 8 unresolved**.

The broader dialogue analysis remains useful for scene aliases, role-level identities, shared candidate sets, talking activators, and contextual Wailway attribution. Strict unresolved status must not be mistaken for proof that no contextual speaker is known.

See:
- `speaker-resolution.md`
- `speaker-repair-validation.json`
- `source-integrity.json`

## Full-plugin exhaustiveness

The verified ESP was traversed through all **36,824 physical records**. The original core filter correctly captured the narrative-heavy source classes, but it omitted useful implementation text. The audit therefore added `raw/implementation-text-supplement.jsonl.gz` with **328** records covering player-facing or lore-structural evidence from factions, talking activators, voice types, mechanisms, equipment, spells/effects, races/creatures, named references, and related records.

Implementation-only strings such as asset paths, package parameter labels, animation-event names, and editor wiring were audited but not promoted into lore claims.

See `exhaustiveness-audit.md` and `implementation-text-supplement.json`.

## BOOK provenance state

All **33/33 BOOK records** have raw, normalized, and comparison SHA-256 fingerprints in `book-normalization-index.json`.

Semantic gap closure also added dedicated topic dossiers for *Musings On Power*, *De Rerum Mutabilitatis*, and *How Two Moon* without changing their unresolved historical provenance.

Current origin/provenance triage:
- **3** verified prior/external text reuses;
- **1** strong-indirect legacy Trainwiz candidate (*Harquebuses*), not yet promoted to verified exact-text reuse;
- **19** continuity-local functional/context documents whose historical origin remains unresolved;
- **10** named works still requiring prior-source research.

These are **external provenance questions**, not unprocessed content in the supplied Wheels of Lull plugin.

## Policy

No ambiguous line is silently assigned to a speaker. No Wheels of Lull claim is silently promoted into Bethesda canon. No text is deduplicated into a central work merely because titles or themes are similar; edition/source relationships require evidence.

## Archive witness state

Provenance pass 04 located dated pre-Wheels Trainwiz package witnesses for **Aethernautics** and **Sotha Sil Expanded**. The archive pages, filenames, byte sizes, dates, upload attribution, and published MD5 hashes are now persisted in `book-provenance-pass-04-archive-witnesses.md` and its JSON companion.

This narrows the remaining historical-source blocker: the packages are located, but their RAR binaries could not be materialized by the current retrieval environment. No BOOK relation was promoted without exact text inspection.\n\nPass 05 re-tested the live download handoff and confirmed that the remaining obstacle is binary materialization rather than package discovery. It also deepened the already-known September 2012 Aethernautics Weaponry Tweaks witness by preserving its exact chronology and previously unrecorded third-party plans involving \"Cronographers\" and a Sotha Sil fortress. Those plans are classified as community-adjacent development history, not Trainwiz-authored source lore. A separate 2015 Trainwiz post explicitly states that Aethernautics and Wheels of Lull take place in the same canon; this is retained as a shared-continuity witness, not prior-text provenance. See `book-provenance-pass-05-retrieval-path-audit.md`.\n\nResume provenance work at archive materialization and deterministic text comparison; if archive bytes remain inaccessible, use a genuinely new historical record-level dump, translation table, xEdit export, or plugin-derived BOOK inventory. Do not repeat generic title searches, package rediscovery, or pass-05 metadata extraction.
