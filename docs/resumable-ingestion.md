# Resumable ingestion ledger

Status: bounded P0.4 foundation.

`src/agent_os/ingestion.py` provides a provider-neutral local ledger for long
imports and crawls. It is deliberately metadata-only: source payloads are
hashed, not copied into the ledger, and callers should keep the JSON file in a
gitignored local directory such as `.agent-local`.

Each logical source record receives a stable item ID from `(source,
source_key)`. Its processing fingerprint combines a content SHA-256 hash with
the relevant processor version. Re-enqueuing an unchanged item is a duplicate
no-op; a changed content hash or processor version requeues the same item ID
and clears stale output references.

The persisted states are `queued`, `processing`, `processed`, and `error`.
Claims increment an attempt count. Opening a ledger recovers claims left in
`processing` by an interrupted worker, so a later worker can claim them again.
Completion is idempotent, while errors can be explicitly retried only when
marked retryable. A scalar cursor and compact metrics are persisted as a
monotonic checkpoint.

The implementation assumes one active worker per ledger. Provider adapters
(iCloud Mail, Drive, messages, feeds, and document batches) still need to
adopt these primitives in their own bounded stages; this sub-stage does not
store provider credentials, raw records, OCR text, or derived artifacts.
