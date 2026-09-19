---
name: batch-before-model
description: Preprocess, deduplicate, group, and classify many similar items before model use so only ambiguous or high-value subsets consume reasoning.
---

# Batch Before Model

Use for large collections such as files, pages, emails, messages, records, forms, crawl items, or lore sources.

1. Normalize and assign stable IDs/fingerprints.
2. Remove exact duplicates and already-processed items.
3. Apply deterministic rules, indexes, parsers, fingerprints, or cheap classifiers.
4. Group similar unresolved items into batches/clusters.
5. Send only ambiguous, novel, conflicting, or high-value subsets to model reasoning.
6. Preserve per-item provenance so batch results can be mapped back safely.
7. Validate representative and edge cases before applying a batch decision broadly.
8. Checkpoint batch progress so retries process only failed/unresolved items.

Never send an entire collection to a model when deterministic preprocessing can substantially reduce it.
