# Dealing with Daedra claims

This directory contains evidence-backed claim bundles and normalized retrieval layers for `tes.mod.dealing-with-daedra`.

## Current claim corpus

- **341** sequential numeric claims: `dwd-001` through `dwd-341`
- **18** specialized named claims for Eraamion and Book-of-Curses page/full-book mechanics
- **359** total indexed claim records
- **0** missing numeric IDs after recovery
- **0** duplicate claim IDs in the consolidated index

## Retrieval layers

- `claim-index.jsonl` — consolidated retrieval index with proposition, original subject/predicate/object, confidence, evidence, source bundle, and normalized relationship fields.
- `claim-relations.jsonl` — normalized contradiction, perspective, chronology, terminology, and uncertainty-boundary relations.
- `contradiction-index.jsonl` — explanatory source for the seven structured conflict edges.
- `unresolved-identity-index.jsonl` — explanatory source for seven identity/inference boundaries.

The individual `claim-seeds-*.jsonl` files remain provenance-bearing source bundles and should not be deleted after consolidation.

## Recovered historical claims

Two earlier pass-13 claim files were later overwritten because filenames were reused. Git history preserved the original rows.

Recovered files:
- `claim-seeds-13i-family-recovered.jsonl` — dwd-187 through dwd-190
- `claim-seeds-13k-drelas-recovered.jsonl` — dwd-200 through dwd-204

See `../analysis/claim-seed-recovery-02.md`.

## Write policy

1. Never reuse an existing claim-seed filename for a new batch.
2. Prefer a descriptive unique suffix when pass/batch numbering could collide.
3. Preserve original evidence and confidence language when adding a claim to the consolidated index.
4. Do not convert unresolved identity or partisan testimony into neutral fact merely because it appears in the index.
5. Relationship normalization belongs in the derived index/relation layer; source bundles remain immutable provenance whenever practical.
