# RTEC HR source corpus

This directory is the authoritative source archive for safe position-level RTEC HR documents.

## Storage contract

For process manuals, policies, procedures, training/reference material, blank forms/templates, checklists, and system instructions:

1. Preserve the complete source whenever repository privacy rules permit.
2. Preserve the original artifact when practical.
3. Maintain a full searchable text/structured mirror.
4. Record content hash, source/version/revision/effective dates, ingestion date, and temporal status.
5. Keep superseded versions; never overwrite history.
6. Link versions and derived process/rule records back to exact source IDs.
7. Never place live employee/applicant records or employee-level PII here.

## Temporal status

Every source should be classified as one of:

- current
- historical
- superseded
- future_effective
- unknown
- conflicting

The corpus spans roughly 20 years, so `unknown` is preferred over falsely treating undated material as current.

## Suggested layout

`sources/<source-id>/manifest.json`
`sources/<source-id>/original.<ext>` when safe/practical
`sources/<source-id>/fulltext.md` or another lossless searchable representation
`sources/<source-id>/derived-links.json`

Source IDs should be stable across renamed copies of the same source/version when content hashes demonstrate identity.
