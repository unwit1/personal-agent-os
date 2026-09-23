# Wheels of Lull Raw-Shard Repair

Two stored gzip shards must be regenerated before speaker resolution can be exhaustive:

1. `raw/source-records-0151-0200.jsonl.gz`
2. `raw/source-records-0401-0450.jsonl.gz`

## Deterministic repair procedure

1. Verify `WheelsOfLull.esp` SHA-256 is `230b102cd1ec13f2d104da8803d32c19227ef519eaca766a00b076c322aa78bb`.
2. Re-run the same canonical TES5 parser used for ingestion.
3. Select the original prioritized source records 151-200 and 401-450 in the same physical-source ordering.
4. Serialize UTF-8 JSONL using the existing source-record schema.
5. Compress with a standard deterministic gzip writer.
6. Replace only the two bad shard files.
7. Verify each shard expands to exactly 50 JSONL records.
8. Re-run strict CTDA speaker resolution for the 52 INFO records contained in those ranges.
9. Merge those rows into the speaker-resolution index without changing already resolved rows unless the source evidence proves a correction is required.

## Current bounded gap

- Total INFO: 410
- Processed: 358
- Deterministically resolved: 288
- Readable but unresolved: 70
- Awaiting shard regeneration: 52

No source claim or speaker identity from the excluded ranges should be inferred merely to fill the gap.
