# Wheels of Lull Post-Ingestion Analysis

Status: **complete with a bounded raw-shard decode gap**.

Completed products:
- deterministic speaker-resolution batches for every readable INFO shard;
- major character evidence dossiers;
- complete 33-location / 103-cell place index and high-value place dossiers;
- artifact/technology dossiers;
- faction/group dossiers;
- 25 normalized core claims;
- 7 canon/tension handling records;
- machine-readable retrieval index.

Speaker resolution processed 358 of 410 INFO records. 288 were deterministically resolved and 70 remain intentionally unresolved. The other 52 INFO records fall inside two stored gzip shards that the current analysis reader could not decode. They are explicitly documented in `source-integrity.json` and must be reparsed/regenerated before speaker resolution can be called fully exhaustive.

No ambiguous line is silently assigned to a speaker. No Wheels of Lull claim is silently promoted into Bethesda canon.
