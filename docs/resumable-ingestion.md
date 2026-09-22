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

The first adapter seam is iCloud Mail: `mail.sync()` delegates fetched
RFC822 records to `mail.sync_records()`, which commits the local SQLite index
before marking each ledger item processed. Synthetic fixture tests cover
idempotent re-import, changed content for the same UID, interruption recovery,
and checkpoint continuation. Provider adapters for Drive, messages, feeds, and
document batches remain provider-specific, but the shared document layer now
has an `extract_batch()` seam that applies the same ledger to local page
extraction while reusing `extract_page()` and its OCR cache. Its fixture tests
cover idempotent re-import, changed page bytes, interruption recovery, and
checkpoint continuation. The canonical local search index also now exposes
`index.rebuild_documents()`: unchanged source documents are skipped, changed
documents are reindexed, and a deleted derived SQLite index is repaired from
source without trusting the ledger as canonical state. The local structured
profile importer also routes `profile.index_facts()` through the ledger: its
gitignored fact cache reuses unchanged canonical profile sources, requeues
changed JSON, and resumes claims interrupted between checkpointed sources.
The local candidate-record reader likewise routes per-record JSON through a
project-scoped ledger, preserving the review/promotion boundary while tracking
changed records, idempotent reads, and interrupted directory scans.
The local improvement-record reader now uses the same seam for project-scoped
`IMP-*.json` scans, so status/search/capture reads can resume after an
interruption without copying improvement content into the ledger.
The local change-record reader now follows the same project-scoped pattern for
`CR-*.json` scans, preserving the existing lifecycle, deduplication, and safe
projection behavior while making reads incremental and restart-safe.
The context compiler's project handoff reader now uses the same metadata-only
ledger for canonical handoff JSON, preserving newest-first retrieval while
recording interrupted scans and completed source files.
The sanitized local form registry reader now uses its own ledger item and
checkpoint as well, preserving the existing form-routing privacy boundary
while detecting changed registry content and recovering interrupted reads.
The currently covered local seams are therefore mail fixtures, document page
batches, canonical index rebuilds, profile sources, candidate records,
improvement records, change records, project handoffs, and the sanitized form
registry. Workflow run state is intentionally excluded because its existing
stage checkpoint/state machine is already the canonical resumability boundary.
Drive archive, text-message, feed, and other provider adapters still require
their own source-specific identity and changed-content semantics before they
can safely be added here.
The implementation assumes one active worker per ledger and does not store
provider credentials, raw records, OCR text, or derived artifacts in the
ledger.
