# Google Drive ingestion contract

Status: bounded P0.4 provider adapter.

`src/agent_os/google_drive.py` is the provider-specific boundary for Google
Drive records. The provider connector owns enumeration and fetching/exporting
the canonical content bytes; the adapter owns stable identity, content
fingerprinting, ledger claims, processing, and checkpoints.

## Identity and change semantics

- A logical source record is identified by the ordered pair `(drive_scope,
  file_id)`. The scope is part of the identity so two synthetic Drive scopes
  cannot collide even when they contain the same file ID.
- Names and parent folders are metadata only. Renames and moves therefore keep
  the same ledger item ID when the file ID and scope are unchanged.
- The fetched/exported content bytes are the changed-content authority. Their
  SHA-256 fingerprint is passed to `IngestionLedger`; a changed fingerprint
  requeues the same logical item, while an unchanged fingerprint is a no-op.
- The ledger stores the source key, hashes, state, attempts, output references,
  and checkpoint metadata only. It never stores file names, parent metadata, or
  content bytes.

The adapter accepts provider-shaped records rather than importing a Drive SDK.
That keeps provider credentials and connector behavior outside the shared
ledger and makes the contract testable with the synthetic fixture at
`tests/fixtures/google_drive/synthetic_files.json`.

