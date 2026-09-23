# Wheels of Lull Post-Ingestion Analysis

Status: **core analysis complete; bounded raw-shard regeneration remains; BOOK provenance follow-up is active**.

Completed products:
- deterministic speaker-resolution batches for every readable INFO shard;
- major character evidence dossiers;
- complete 33-location / 103-cell place index and high-value place dossiers;
- artifact/technology dossiers;
- faction/group dossiers;
- 25 normalized core claims;
- 7 canon/tension handling records;
- machine-readable retrieval index;
- deterministic normalization and SHA-256 fingerprints for all 33 BOOK records;
- BOOK provenance passes 01-02;
- central-source links for verified KINMUNE, Tatterdemalion, and Xal-Gosleigh reuse.

## Dialogue integrity boundary

Speaker resolution processed **358 of 410 INFO records**. **288** were deterministically resolved and **70** remain intentionally unresolved. The other **52 INFO records** fall inside two stored gzip shards that are corrupt and require deterministic regeneration from the original `WheelsOfLull.esp` before speaker resolution can be called exhaustive:

- `raw/source-records-0151-0200.jsonl.gz`
- `raw/source-records-0401-0450.jsonl.gz`

The original ESP is not currently present in the repository/file-library access layer, and both bad blobs were already corrupt in their creation commits. No dialogue from those ranges is inferred to fill the gap.

## BOOK provenance state

All **33/33 BOOK records** have raw, normalized, and comparison SHA-256 fingerprints in `book-normalization-index.json`.

Current origin/provenance triage:
- **3** verified prior/external text reuses;
- **1** strong-indirect legacy Trainwiz candidate (*Harquebuses*), not yet promoted to verified exact-text reuse;
- **19** continuity-local functional/context documents whose historical origin remains unresolved;
- **10** named works still requiring prior-source research.

See:
- `book-provenance-pass-01.md`
- `book-provenance-pass-02.md`
- `book-normalization-index.json`

## Policy

No ambiguous line is silently assigned to a speaker. No Wheels of Lull claim is silently promoted into Bethesda canon. No text is deduplicated into a central work merely because titles or themes are similar; edition/source relationships require evidence.
