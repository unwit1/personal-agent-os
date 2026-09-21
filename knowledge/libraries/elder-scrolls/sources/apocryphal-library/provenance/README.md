# Incremental provenance overlays

These files record small, reviewable provenance-verification batches for the Apocryphal Library corpus.

## Merge rule

For a FormID present in one of the numbered batch files, the **highest-numbered batch containing that FormID supersedes the baseline status in `../provenance-triage.json`**. This lets provenance work proceed in small commits without rewriting the large 784-record baseline ledger on every pass.

Only evidence-backed promotions are allowed. Generic titles, ambiguous notes, and records not explicitly identified by a source remain unresolved.

## Batches

- `batch-001.json` — first 10 alphabetical titles; official-game, developer-text, mod-original, and unresolved classifications.
