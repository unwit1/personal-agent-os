# The Wheels of Lull

Sub-continuity for the Skyrim mod **The Wheels of Lull**.

- Continuity ID: `tes.mod.wheels-of-lull`
- Primary source: user-provided `WheelsOfLull.esp`
- ESP SHA-256: `230b102cd1ec13f2d104da8803d32c19227ef519eaca766a00b076c322aa78bb`

## Structured lore-source ingestion: complete

- BOOK **33/33**
- QUST **32/32**
- DIAL **337/337**
- INFO **410/410**
- NPC_ **75/75**
- LCTN **33/33**
- CELL **103/103**
- MESG **53/53**
- SCEN **14/14**
- **1,090 structured lore-bearing source records** persisted.

The raw source import is complete. Messages preserve user-facing text where present; scenes preserve owning quest, subrecord order, and deterministic references to dialogue/quest/NPC records where resolvable.

## Core post-ingestion analysis: complete with one bounded repair

Completed:
- speaker/condition analysis for every readable INFO record;
- character, place, artifact/technology, and faction dossiers;
- 31 normalized core claims and 7 tension/canon-boundary records;
- 14 topic dossiers plus theme/reliability synthesis;
- compact routing/retrieval derivatives with 76 analysis entries;
- deterministic fingerprints for all 33 BOOK records;
- BOOK provenance passes 01-03;
- machine-readable BOOK-to-central-source relations.

### Dialogue repair boundary

Two stored gzip shards are corrupt:

- `raw/source-records-0151-0200.jsonl.gz`
- `raw/source-records-0401-0450.jsonl.gz`

This leaves **52 INFO records** outside exhaustive speaker resolution. Of 410 INFO records, 358 are readable/processed, 288 are deterministically speaker-resolved, and 70 readable records remain intentionally unresolved.

The bad blobs were already corrupt in their creation commits. The exact `WheelsOfLull.esp` is not currently available in the repository or indexed file library, so deterministic repair requires reacquiring that exact source file and verifying its SHA-256 before regeneration.

See:
- `analysis/source-integrity.json`
- `analysis/repair-plan.md`
- `analysis/post-ingestion-status.json`

## BOOK provenance

All **33/33 BOOK records** have raw, normalized, and comparison SHA-256 fingerprints.

Current provenance state:
- **3** verified prior/external text reuses: KINMUNE, Tatterdemalion, and The Cacophany / Xal-Gosleigh excerpt;
- **1** strong-indirect legacy Trainwiz candidate: *Harquebuses* — concept predates Wheels, exact treatise witness still unverified;
- **19** continuity-local contextual/operational documents with historical origin unresolved;
- **10** named lore works with no verified pre-Wheels witness found in the current search surfaces.

KINMUNE has a completed edition-level comparison proving the Wheels text is an abridged/edited variant rather than an exact duplicate.

See:
- `analysis/book-normalization-index.json`
- `analysis/book-provenance-pass-02.*`
- `analysis/book-provenance-pass-03-search-audit.*`
- `analysis/book-variant-pass-01.*`
- `normalized/book-source-relations.json`

## Retrieval state

Existing compact indexes cover the expected 1,090-record corpus, but a **fresh full materialization is currently blocked** by the two corrupt raw shards. The retrieval builder now fails closed instead of silently creating a partial corpus.

After shard repair:
1. merge the 52 repaired INFO records into speaker resolution;
2. rerun full 1,090-record retrieval materialization;
3. validate routing/lexical derivatives before replacing persistent indexes.

## Provenance policy

All material remains scoped to `tes.mod.wheels-of-lull` unless an explicit source relationship is verified. Character testimony, quest narration, UI/message text, implementation evidence, external/developer texts, and later synthesis remain distinct evidence classes.

No missing dialogue is inferred, no ambiguous line is silently assigned to a speaker, and no reused text is promoted into Bethesda canon merely because Wheels embeds it.
