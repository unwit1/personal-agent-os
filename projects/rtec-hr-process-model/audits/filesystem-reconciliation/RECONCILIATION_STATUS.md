# RTEC HR PC reconciliation — checkpoint report

**Checkpoint:** 2026-09-25. Phases 0–2 metadata discovery, SHA-256 hashing, and exact-source reconciliation are complete for the configured roots. Content parsing, semantic deduplication, file classification, and new Knowledge Engine ingestion have not started.

## What Agent OS already knew

- The active canonical RTEC HR corpus is `knowledge/libraries/rtec-hr/` in `personal-agent-os`; the project contract, knowledge schema, source batches, per-source manifests, reference-form catalog, role/job-description history, temporal status, restricted-evidence metadata, and gap queues are already present. No competing `knowledge/rtec/` library was found in the active project routing.
- The RTEC form catalog contains 92 records across 76 identity keys: 72 HR GUI records, 3 Applicant Dashboard records, 17 records already represented in the RTEC HR corpus, and 12 records awaiting identity review.
- Project state records six completed ingestion batches, 50 open currentness/context questions, and extensive existing coverage for correspondence, job descriptions, handbooks, spreadsheets, compliance, benefits, payroll/time, attendance/leave, recruiting, systems, and forms. Historical coverage is not proof of current authority.
- Previously cataloged PC-adjacent sets include 55 job-description archive files (51 safe sources and 4 employee-specific restricted sources), 16 Downloads XLS artifacts resolved to 11 families, 95 correspondence artifacts with explicit dispositions, and 85 job-openings archive artifacts. They were not reingested here.
- `src/agent_os/ingestion.py` supplies a metadata-only, restart-safe work ledger. The RTEC source corpus and its provenance/version model remain the ingestion authority.

## Architecture map and current integration gaps

```text
local work folders -> local-only resumable inventory -> safe-source hash reconciliation
  -> (future) deterministic extraction and restriction routing
    -> organizational candidate -> existing Knowledge Engine contract
    -> employee/restricted -> local employee-document registry -> HR GUI
    -> ambiguous/failure -> local review queue
```

- HR GUI has an Employees roster view and configurable active/terminated personnel-folder open action. Its scanner recognizes/forms-routes documents and stores page-hash dedup data locally. `document_import.py` accepts PDF, images, DOC, and DOCX for scanner conversion. A separate structured XLS/XLSX registry stages source sheets, preserves unmapped columns, blocks writes on schema drift, and uses file/sheet/row fingerprints for idempotency and row provenance.
- No first-class employee-document registry/schema was found in HR GUI. This audit has established a local-only `employee_documents` table schema for later classified entries, plus a review queue and knowledge-gap table. No employee entries have been created yet.
- Applicant Dashboard remains the restricted normalization boundary. Applicant, candidate, and pending-new-hire trees are excluded from generic filesystem traversal. R: is excluded at the user’s direction.
- Agent OS validation reports `ok: true` with no errors and 518 checks, plus one pre-existing warning: `routing adapter differs from canonical source: C:\Users\HR.RTEC\GitHub\job-applicant-dashboard\AGENTS.md`. The Applicant Dashboard integration contract and policy remain authoritative; this audit did not modify or synchronize that checkout.
- The audit’s SQLite database and append-only progress log are under ignored `.agent-local/rtec-hr-reconciliation/`. They contain path-bearing metadata and must never be committed or synced as repository artifacts.

## PC inventory and reconciliation

The inventory covered eight configured roots: Desktop, Documents, Downloads, local HR GUI data, the canonical Personal Agent OS checkout, and two HR GUI checkouts, plus an existing OneDrive root. No other mapped filesystem drives were reported by the local shell. R: was not inspected.

- 25,147 office-type file entries were recorded locally; 15,441 matched the HR path/filename relevance heuristic and were hashed.
- 497 file hashes match a SHA-256 value in safe RTEC corpus JSON. This is exact binary-hash evidence only. It does not imply that an unmatched file adds knowledge or that a matching document is current.
- 4,043 local SHA-256 duplicate groups contain 8,833 files, or 4,790 extra copies beyond one per group. Originals remain untouched. These counts describe exact-byte duplicates, not semantic/document-version identity.
- The safe corpus hash index currently contains 301 source-hash references across 198 distinct values. Thirty-three of the 497 file matches lack a populated source ID in the indexed record; their knowledge path is retained locally for review.
- By filename/path heuristic, 7,324 candidates route to employee-restricted review and 8,117 route to organizational-or-mixed review. These are not confirmed document classifications. All 15,441 remain `UNKNOWN_REVIEW` pending deterministic content extraction and privacy review.
- 41 filesystem stat/access failures remain visible: 3 permission-denied and 38 stat-failed events. They have path and phase records only in the local failure table. No content extraction/OCR has run, so there are no parser failures yet.
- Format counts among the HR-path candidates include PDF 8,199; XLS 3,642; DOC 1,370; DOCX 936; JPG 485; XLSX 368; PNG 101; plus CSV, PPT/PPTX, RTF, HTML, ZIP, and message formats. Legacy spreadsheet parsing is a major next-stage requirement.
- By metadata route, 7,324 candidates match employee-restricted path/filename terms and 8,117 match organizational-or-mixed terms. The routing is heuristic only; contents were not inspected.
- Total bytes hashed in the local HR candidate set: 28,696,604,168. Unchanged files can reuse their cached size/mtime fingerprint on future runs.

## What is new, restricted, duplicate, or unresolved

### New organizational knowledge

No new organizational knowledge has been promoted or ingested. The 14,944 hashed files without a matching safe source hash are only unmatched candidates. They may be restricted employee documents, duplicates with different binaries, old versions, irrelevant files, or genuinely new sources; extraction and classification are required before deciding.

### Employee-specific material

The file paths and hashes remain local-only. The 7,324 restricted-route count is a metadata heuristic, not a confirmed employee-file count. No names, identifiers, payroll values, benefits elections, medical details, OCR, or document text have been added to the generalized corpus. The local employee-document registry is currently empty.

### Duplicates and versions

Exact-hash duplicate groups are available in the local `duplicate_groups` view. Similar filenames, normalized text, version labels, effective dates, and authority were not evaluated. No originals were moved, renamed, or deleted.

### Files not processed

The 41 stat/access failures are explicit. Supported formats are not yet parsed in this stage; unsupported/parser/password/corrupt status must be added during extraction rather than treating these files as empty. Applicant/candidate/pending-new-hire paths, generated outputs/build trees, caches, unrelated repositories, and R: were deliberately excluded.

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

1. Add safe per-format extraction and privacy routing before any content ingestion, prioritizing the 3,642 XLS and 368 XLSX candidates. Inspect every sheet, hidden sheets, headers, formulas, named ranges, and schema drift. Keep multi-person/person-level rows restricted.
2. Add structured statuses for password-protected/corrupt/unsupported/ambiguous files; the current local failure model already provides a durable path/phase queue.
3. Build the HR GUI document list from stable local document IDs, with source path, document type/date, hash/duplicate group, current/historical status, sensitivity, and review flag. Do not show Missing/Expired until a validated requirement model exists.
4. Reconcile scanner page-hash dedup with whole-file hash groups, preserving provenance and original paths; do not auto-delete or auto-move copies.
5. Create normalized-content fingerprints only after deterministic extraction; compare content, title, effective date, and structure to determine equivalent forms and version chains.
6. Document which workflows repeatedly move data between ADP, spreadsheets, carriers, portals, and HR GUI before proposing automation.

## Resume instructions

Read `ARCHITECTURE.md`, this report, and the local log/database first. All current roots have completed discovery and all HR-path candidates have exact SHA-256 hashes. Resume with:

```powershell
python "projects\rtec-hr-process-model\audits\filesystem-reconciliation\inventory.py" --reconcile
```

The next meaningful phase is a bounded deterministic extraction/classification pass over the local `review_queue` in `.agent-local/rtec-hr-reconciliation/audit.sqlite3`. Route mixed, employee, applicant, and uncertain documents before retaining any extracted value. Do not copy this database into Git. Do not scan R:.
