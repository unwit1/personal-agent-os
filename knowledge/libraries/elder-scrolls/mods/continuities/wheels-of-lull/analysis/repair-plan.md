# Wheels of Lull Raw-Shard Repair — Completed

Status: **complete** on 2026-09-23.

The exact source `WheelsOfLull.esp` was supplied again and verified at SHA-256:

`230b102cd1ec13f2d104da8803d32c19227ef519eaca766a00b076c322aa78bb`

A fresh physical TES5 traversal reproduced the repository's original prioritized record inventory exactly: **1,090 records** in the same type counts and source ordering.

## Repaired shards

### 151-200

- path: `raw/source-records-0151-0200.jsonl.gz`
- prior corrupt Git blob: `33e190cca1894d5e1ca41758b23014af7c54af6f`
- repaired Git blob: `e0870ad5f07968319d5a614c17d820167fd67f48`
- repaired gzip SHA-256: `88efb18959daad4676dbf614e307077ad21003f2ed80959fc659261fe4e1aab7`
- records: 50
- INFO records: 25
- repair commit: `5762fbc4db9db45419038ac5898e16bd630e079a`

### 401-450

- path: `raw/source-records-0401-0450.jsonl.gz`
- prior corrupt Git blob: `b4eb58a37ebad7cd6bba931f7a92bded9b36e6f6`
- repaired Git blob: `7d77d5fdbb6c5905c1be8e4785a62fd01eb29825`
- repaired gzip SHA-256: `06458f4619b57d6633d2b8c7a6049964fb6802ba0cd81415bd810cd82e3de84d`
- records: 50
- INFO records: 27
- repair commit: `6d9d2afe29c20edef47c9e5b5a168929e98ca1a5`

Both repaired files use deterministic gzip output and expand to exactly 50 valid JSONL records.

## Speaker cross-check

The two ranges recover **52 INFO** records.

Strict CTDA policy: equality `GetIsID` or uniquely mapped equality `GetIsVoiceType` only.

- old readable baseline: 358 INFO = **288 resolved / 70 unresolved**
- independently regenerated baseline result: **288 / 70**, exact match
- repaired 52 INFO: **44 resolved / 8 unresolved**
- complete strict corpus: 410 INFO = **332 resolved / 78 unresolved**
- excluded pending repair: **0**

The eight repaired strict-unresolved records are retained as unresolved rather than inferred. Five contain Wailway/train-context dialogue but carry no strict CTDA speaker binding; three have no response text. See `speaker-repair-validation.json`.

## Post-repair exhaustiveness

After closing the raw gap, the whole 36,824-record plugin was audited for text-bearing records outside the original priority set. A separate **328-record implementation-text supplement** was added at `raw/implementation-text-supplement.jsonl.gz`. See `exhaustiveness-audit.md`.

There is no remaining raw-shard or supplied-ESP ingestion blocker. Historical BOOK provenance remains a separate external-source research track.
