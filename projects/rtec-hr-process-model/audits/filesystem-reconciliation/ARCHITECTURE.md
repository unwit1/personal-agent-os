# RTEC HR filesystem reconciliation

Status: architecture, metadata inventory, exact-hash reconciliation, and first-pass deterministic extraction are complete for configured roots. Cache-only OCR is operational with 12 files complete, 1 restricted sample, and 6,396 files still queued; review/reconciliation remain outstanding.

## Canonical locations and existing capabilities

- **Personal Agent OS / Knowledge Engine:** `personal-agent-os` repository.
- **Canonical RTEC HR domain:** `knowledge/libraries/rtec-hr/`. The current repository and project state use this location; no competing `knowledge/rtec/` library is present in the active project routing.
- **Project contract and durable state:** `projects/rtec-hr-process-model/README.md`, `docs/INGESTION_CONTRACT.md`, and `state.json`.
- **Knowledge record schema:** `schemas/rtec-hr-knowledge-v1.schema.json`.
- **Reusable incremental work ledger:** `src/agent_os/ingestion.py`, with metadata-only `IngestionLedger`, stable work/item IDs, content and processor fingerprints, interruption recovery, and a gitignored local storage convention. This audit uses its own SQLite inventory because file paths and hashes are employee-sensitive metadata and need local-only joins/querying.
- **Existing source/provenance records:** `knowledge/libraries/rtec-hr/sources/`, batch JSON under `sources/batches/`, per-source `manifest.json`, source mirrors, policy/process/form/system/role records, plus explicit restricted metadata under `restricted-evidence/`. The latter is not read by the generic knowledge hash index.
- **Forms:** `forms/registry.json` is the Agent OS-wide runtime form-routing registry (currently empty); RTEC's actual source-of-truth catalog is `knowledge/libraries/rtec-hr/forms/reference-form-catalog.json` and domain-specific form records.
- **Job descriptions:** `sources/job-descriptions/manifest.json`, source mirrors, `roles/job-description-history.json`, and batch records.
- **Existing version/currentness and gaps:** record-level `temporal_status`, source dates, supersession links, `questions/currentness-and-gaps.json`, and domain-specific gap queues. Historical by default; age or mtime is not authority.
- **Existing spreadsheet record:** `sources/batches/rtec-hr-downloads-spreadsheets-2026-09-24.json`, restricted evidence metadata, reusable field contracts, spreadsheet document-type definitions, and a coverage ledger. It records the earlier 16 XLS artifacts and their safe/restricted dispositions; this is a reconciliation target, not a reingestion request.
- **Restricted evidence:** already-separated metadata-only manifests and aggregate findings. Do not promote employee-specific facts into the generalized library.

## Connected application boundary

- **HR GUI:** the registered `HR GUI` checkout is the local scanner and HR desktop app. `PROJECT_GUIDE.md` makes its local settings, live data, scanner state, employee overrides, OCR output, and logs local-only. Its Employees module reads a configured employee roster and opens configured active/terminated personnel folders. It does not currently expose a first-class employee-document registry/schema.
- **HR GUI document intake:** `hrgui/core/document_import.py` converts PDF/image/Word files into scanner PDFs. The scanner classifies/renames/routes files; `config/routing.json` maps recognized forms to modules. `assets/structured_spreadsheet_import_registry.json` defines a separate direct XLS/XLSX path: source sheets are staged, unknown columns are retained/reported, schema drift blocks normalized writes, and source-hash/sheet/row fingerprints provide idempotency. Scanner page-hash dedup and spreadsheet row provenance are separate from a durable employee-document registry.
- **Applicant Dashboard:** the registered `job-applicant-dashboard` checkout is a restricted applicant normalization layer. Its project policy forbids generic reads/indexes of live applicant artifacts; the only allowed connection is the explicit whitelisted administrative adapter. This filesystem pass excludes its live applicant stores and payloads.
- **Existing local-only storage:** Agent OS `.agent-local/` is gitignored. HR GUI live files/settings are under the workstation's `Documents/HR Automation Local/HR GUI/` boundary. The audit database and logs are stored only under the ignored Agent OS `.agent-local/rtec-hr-reconciliation/` directory. Never copy that directory into a tracked artifact or cloud share.

## Reconciliation data flow

```text
workstation work roots
  -> resumable local metadata inventory (SQLite; paths, metadata, cached SHA-256)
  -> exact raw hash match against safe RTEC source/provenance records
  -> local duplicate groups and review queue
  -> deterministic format extraction and privacy routing
      -> safe organizational candidates -> existing Knowledge Engine contract
      -> employee-specific/restricted -> local employee-document registry
      -> ambiguous/failed -> local review queue
  -> sanitized context-completeness report and GUI integration recommendation
```

Exact hash equality can establish `ALREADY_INGESTED_EXACT` only when the comparable Knowledge Engine value is a raw-source SHA-256. Normalized-text hashes, semantic families, duplicate notes, and source IDs are kept distinct and never asserted as exact binary matches. Filename similarity or mtime alone cannot establish equivalence, authority, currentness, or employee identity.

## Initial gaps and decisions

1. No general PC inventory/reconciliation checkpoint was found in the project state. The existing ingestion ledger is a reusable resumability foundation, but it does not inventory filesystem roots or reconcile files to RTEC provenance.
2. No standalone employee-document registry exists in HR GUI. Existing roster, personnel-folder paths, scanner routing, and form rules are useful integration points, but missing/current/expired status must remain unknown until an explicit requirement model exists.
3. Scanner intake is centered on PDF/image/Word conversion. XLS/XLSX import schemas exist separately, so the scanner's document conversion and structured spreadsheet ingestion are distinct paths.
4. Applicant files are explicitly out of scope for generic indexing; use only the approved Applicant Dashboard adapter for a separately authorized administrative workflow.
5. The audit extracts locally into memory for hashes, structural metadata, and privacy signal codes. Raw text and detected values are not persisted. OCR is cache-only, has network downloads disabled, and saves page hashes/counts/signal codes only. Every extraction result remains review-required; no organizational knowledge has been written.

## Resumption

Read `RECONCILIATION_STATUS.md`, then `.agent-local/rtec-hr-reconciliation/audit.sqlite3` and `audit.log`. First-pass extractions are complete. Continue with `inventory.py --ocr --ocr-limit 5 --ocr-pages-per-file 10`; pages and files resume from the local OCR ledger. Directories and hashes are cached. Never put path-bearing database/log contents in Git. The live database is intentionally absent from this repository and is not committed.
