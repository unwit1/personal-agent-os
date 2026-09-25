# RTEC HR PC reconciliation — checkpoint report

**Checkpoint:** 2026-09-25. Metadata discovery, SHA-256 exact-source reconciliation, and first-pass deterministic extraction are complete for eight configured local roots (15,441 of 15,441 candidates). Cache-only OCR is operational; status is 12 complete, 5 restricted samples, 0 failures, and 6,392 pending. A larger batch was interrupted after memory reached about 1.1 GB; completed files remained checkpointed. OCR images are now downsampled to a 2,600-pixel maximum edge before processing. Content/version reconciliation, classification review, and any new Knowledge Engine ingestion remain outstanding. No new source has been ingested into the Knowledge Engine.

## What Agent OS already knew

- The active canonical RTEC HR corpus is `knowledge/libraries/rtec-hr/` in `personal-agent-os`; the project contract, knowledge schema, source batches, per-source manifests, reference-form catalog, role/job-description history, temporal status, restricted-evidence metadata, and gap queues are already present. No competing `knowledge/rtec/` library was found in the active project routing.
- The RTEC form catalog contains 92 records across 76 identity keys: 72 HR GUI records, 3 Applicant Dashboard records, 17 records already represented in the RTEC HR corpus, and 12 records awaiting identity review.
- Project state records six completed ingestion batches, 50 open currentness/context questions, and extensive existing coverage for correspondence, job descriptions, handbooks, spreadsheets, compliance, benefits, payroll/time, attendance/leave, recruiting, systems, and forms. Historical coverage is not proof of current authority.
- Previously cataloged PC-adjacent sets include 55 job-description archive files (51 safe sources and 4 employee-specific restricted sources), 16 Downloads XLS artifacts resolved to 11 families, 95 correspondence artifacts with explicit dispositions, and 85 job-openings archive artifacts. They were not reingested here.
- `src/agent_os/ingestion.py` supplies a metadata-only, restart-safe work ledger. The RTEC source corpus and its provenance/version model remain the ingestion authority.

## Architecture map and current integration gaps

```text
local work folders -> local-only resumable inventory -> safe-source hash reconciliation
  -> deterministic extraction and conservative restriction routing
    -> organizational candidate -> existing Knowledge Engine contract
    -> employee/restricted -> local employee-document registry -> HR GUI
    -> ambiguous/failure -> local review queue
```

- HR GUI has an Employees roster view and configurable active/terminated personnel-folder open action. Its scanner recognizes/forms-routes documents and stores page-hash dedup data locally. `document_import.py` accepts PDF, images, DOC, and DOCX for scanner conversion. A separate structured XLS/XLSX registry stages source sheets, preserves unmapped columns, blocks writes on schema drift, and uses file/sheet/row fingerprints for idempotency and row provenance.
- No first-class employee-document registry/schema was found in HR GUI. This audit has established local-only `employee_documents`, extraction, review, and knowledge-gap tables. The first pass has created 3,041 restricted-document metadata rows with null employee identity and `document_type=unknown`; no person match is inferred.
- Applicant Dashboard remains the restricted normalization boundary. Applicant, candidate, and pending-new-hire trees are excluded from generic filesystem traversal. R: is excluded at the user’s direction.
- Agent OS validation reports `ok: true` with no errors and 518 checks, plus one pre-existing warning: `routing adapter differs from canonical source: C:\Users\HR.RTEC\GitHub\job-applicant-dashboard\AGENTS.md`. The Applicant Dashboard integration contract and policy remain authoritative; this audit did not modify or synchronize that checkout.
- The audit’s SQLite database and append-only progress log are under ignored `.agent-local/rtec-hr-reconciliation/`. They contain path-bearing metadata and must never be committed or synced as repository artifacts.

## PC inventory and reconciliation

The inventory covered eight configured roots: Desktop, Documents, Downloads, local HR GUI data, the canonical Personal Agent OS checkout, two HR GUI checkouts, and an existing OneDrive root. No other mapped filesystem drives were reported by the local shell. R: was not inspected and remains excluded at the user's direction.

- 25,147 office-type file entries were recorded locally; 15,441 matched the HR path/filename relevance heuristic and were hashed.
- 30 file hashes match corpus fields explicitly named `source_sha256` or `file_sha256`; these are the confirmed exact source/file matches. Another 467 hashes match generic `sha256` or `content_sha256` fields whose binary-versus-text semantics are unspecified. Those remain `HASH_MATCH_UNVERIFIED`, not exact-ingestion matches.
- 4,043 local SHA-256 duplicate groups contain 8,833 files, or 4,790 extra copies beyond one per group. Originals remain untouched. These counts describe exact-byte duplicates, not semantic/document-version identity.
- 7,497 parsed files have normalized-text hashes. They form 2,525 exact normalized-text duplicate candidate groups with 5,768 members (3,243 extra copies). These are text-equivalence candidates: images, formatting, formulas, metadata, or other non-text structure can differ. They are not merged or treated as the same authoritative document.
- Existing Knowledge Engine source hashes represent source/binary fingerprints; no normalized-text source-hash convention is available for a safe apples-to-apples comparison. The audit therefore does not label a normalized-text match as already represented without a compatible provenance fingerprint.
- The safe corpus hash index contains 301 hash references across 198 distinct values. Twenty-three of the 30 confirmed exact matches lack a populated source ID; nine of the unverified matches also lack one. Their knowledge paths remain local for review.
- By filename/path heuristic, 7,324 candidates route to employee-restricted review and 8,117 to organizational-or-mixed review. These initial routes are not confirmed classifications.
- First-pass extraction is complete for all 15,441 candidates. Results: 1,636 safe-organizational candidates; 3,072 employee-restricted classifications; 654 mixed/uncertain; 2,158 parsed but unknown; 6,409 OCR-required; 1,394 unsupported formats; 69 empty-text; 37 parse failures; 12 corrupt; and 21 archive-review. Every classification remains review-required. None has been promoted to generalized knowledge.
- The local employee-document registry contains 3,055 rows. All have unknown document type and null employee key; records retain minimum-necessary path/hash/provenance and signal codes only. Raw document text and detected values are not stored in the audit database or log.
- 41 filesystem stat/access failures remain visible: 3 permission-denied and 38 stat-failed events. The 6,409 OCR-required files are mostly scanned PDFs and images. The cached EasyOCR worker has processed 12 files completely and sampled 5 restricted documents; no OCR failures were recorded and 6,392 files remain in the resumable OCR queue. Network downloads are disabled and text stays in memory only. The worker downsamples input images to limit memory. The 1,394 unsupported files are predominantly legacy `.doc` files; `.ppt` and `.msg` are also present. No silent-empty assumption is made.
- Format counts among the HR-path candidates include PDF 8,199; XLS 3,642; DOC 1,370; DOCX 936; JPG 485; XLSX 368; PNG 101; plus CSV, PPT/PPTX, RTF, HTML, ZIP, and message formats. Legacy spreadsheet parsing is a major next-stage requirement.
- By metadata route, 7,324 candidates match employee-restricted path/filename terms and 8,117 match organizational-or-mixed terms. The routing is heuristic only; contents were not inspected.
- Total bytes hashed in the local HR candidate set: 28,696,604,168. Unchanged files can reuse their cached size/mtime fingerprint on future runs.

## What is new, restricted, duplicate, or unresolved

### New organizational knowledge

No new organizational knowledge has been promoted or ingested. The 14,944 files without a matching safe corpus hash remain unmatched candidates. Of the 15,441 extracted files, 1,636 are provisional safe-organizational candidates and still require human/provenance/currentness review. They may be duplicates with different binaries, old versions, irrelevant files, or genuinely new sources.

### Employee-specific material

The file paths, hashes, sheet headers, and employee registry remain local-only. The 7,324 restricted-route count is a metadata heuristic, not a confirmed employee-file count. No names, identifiers, payroll values, benefits elections, medical details, OCR, or document text have been added to the generalized corpus.

### Duplicates and versions

Exact-hash duplicate groups are available in the local `duplicate_groups` view; exact normalized-text groups are in `normalized_duplicate_groups`. Similar filenames, version labels, effective dates, and authority have not been reconciled. No originals were moved, renamed, or deleted.

### Files not processed or requiring review

All candidates have first-pass extraction records. OCR-required, unsupported, empty-text, parser-failed, corrupt, and archive-review outcomes are separately represented. The parser currently handles text, PDF embedded text, DOCX, XLS/XLSX/XLSM, CSV/TSV, HTML, RTF, PPTX, EML, and ZIP metadata. Applicant/candidate/pending-new-hire paths, generated outputs/build trees, caches, unrelated repositories, and R: were deliberately excluded.

## Context-completeness matrix — initial baseline

This matrix reflects the current tracked knowledge state, not conclusions from file contents newly parsed by this audit.

| HR area | Existing knowledge and source coverage | Currentness / unresolved context | Forms/templates | HR GUI / automation | Initial gap status |
|---|---|---|---|---|---|
| Recruiting / applicant intake | Current Fillout → Google transport → Applicant Dashboard → restricted Agent OS adapter is documented | Current dashboard is the canonical restricted layer; no generic raw applicant indexing | Catalog includes 3 Applicant Dashboard records | Dashboard is the workflow system; integration is whitelist-only | Good architecture coverage; applicant sources excluded from this filesystem pass |
| Onboarding / new hire | Blank orientation/training sources and current HR GUI new-hire module are represented | End-to-end ownership, record placement, and current system-of-record need reconciliation | Existing reference forms/catalog | HR GUI has New Hires module and scanner routes | Partial workflow context; pending-new-hire payloads excluded |
| Job descriptions / roles | 55 archived files; 51 safe role sources and 4 restricted employee-specific items | Current approvals, reporting relationships, and time-sensitive requirements remain gated | Role documents cataloged | Scanner/form routing only | Historical versions preserved; current authority open |
| Benefits / retirement | Historical spreadsheet families, blank import contracts, current plan comparison references, carriers/vendors | Current election hub and FSA/COBRA administration authority unresolved | Blank benefits import templates present | Benefits module and structured spreadsheet registry; no complete document inventory | Mixed current/historical coverage; source-of-record gaps remain |
| Payroll / time / tax | ADP references, historical adjustment/import evidence, current attendance inputs | Which changes enter ADP versus an external payroll workflow remains a context question | Time/payroll forms are cataloged | Payroll reports/importers exist in related tools; detailed business rules remain bounded | Partial; no employee data parsed by this audit |
| Leave / FMLA | Current FMLA tracker evidence and historical vendor inquiry | Current administrator, case workflow, deadlines, and filing destinations unresolved | Existing FMLA forms/evidence | HR GUI has a routed FMLA stub | High-value process gap |
| Attendance / discipline | Current six-point attendance rule and trackers; historical disciplinary/AAP data quality modeled | July 2021 adoption/version conflicts remain; current manual handoffs need validation | Warning/discipline forms represented | Disciplinary module; attendance tracker stub | Policy history present; operational workflow still needs reconciliation |
| Workers’ compensation / safety | Safety policy/training and injury-documentation candidates exist | Case workflow, authoritative system, and medical-record boundaries require validated handling | Safety and claim artifacts represented | Workers’ compensation stub | Workflow and GUI integration incomplete |
| EEO / AAP / compliance | 2022 plan package, 2025 certification, 864-file compliance archive, historical version chains | FY2017 grant extraction and some source promotion remain in progress | Complaint/investigation forms cataloged | Reporting support partial | Broad source coverage; currentness/source-level promotion still open |
| Personnel records / retention | Personnel process records, roster metadata, and archive evidence exist | Retention schedules and authoritative personnel-file contents require source validation | Reference catalog present | Employees module opens configured folders; no document registry | Registry integration gap confirmed |
| Training / systems / vendors | Historical and current reference maps exist across the corpus | Some system ownership/current vendor authority remains unresolved | Training/reference materials present | Scanner and app modules support portions of the workflow | Needs current source reconciliation |

## Missing context already recorded in the system

The existing 50-question currentness/gap queue remains canonical. High-value open items identified in current project state include the current FMLA administrator and leave workflow; adoption/currentness of the July 2021 attendance-policy proposal and tracked handbook versions; approval/supersession of driver handbooks; deeper FY2017 grant section transcription; and review of six distinct PST sources not yet imported into the local mail index. This audit did not silently close any of those questions.

## Scanner, GUI, and automation opportunities

1. Continue safe, cache-only OCR for the 6,392 remaining files in bounded batches. Restricted-route documents are sampled for at most two pages; OCR results remain review-required and local-only.
2. Review normalized-text duplicate groups and spreadsheet structural metadata for every sheet, including hidden sheets, headers, formulas, named ranges, and schema drift; keep person-level rows restricted.
3. Add `.doc`/`.ppt` local conversion support only if a trusted converter is already installed; otherwise leave those files in the explicit unsupported-format queue.
4. Review safe-organizational candidates against exact source hashes, normalized text fingerprints, titles, effective dates, and existing source records before any Knowledge Engine write.
5. Build HR GUI document lists from stable local IDs, with type/date, hash/duplicate group, current/historical state, sensitivity, and review flag. Do not show Missing/Expired until requirements are validated.
6. Reconcile scanner page-hash dedup with whole-file hash groups, preserving provenance and original paths; do not auto-delete or auto-move copies.
7. Document workflows that repeatedly move data between ADP, spreadsheets, carriers, portals, and HR GUI before proposing automation.

## Resume instructions

Read `ARCHITECTURE.md`, this report, and the local log/database first. All configured roots, candidate hashes, and first-pass extraction records are complete. Continue OCR/reconciliation with bounded batches; `--ocr` resumes by page and does not download models:

```powershell
python "projects\rtec-hr-process-model\audits\filesystem-reconciliation\inventory.py" --ocr --ocr-limit 5 --ocr-pages-per-file 10
```

The next meaningful phase is continued OCR, followed by exact/normalized-content reconciliation and human review of safe-organizational candidates. Route mixed, employee, applicant, and uncertain documents before retaining any extracted value. Do not copy this database into Git. Do not scan R:.
