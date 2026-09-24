# RTEC HR Knowledge Library

This library is the durable, privacy-safe process model for RTEC HR.

## Structure

- `plans/` — versioned historical/current plan packages such as AAP/EEO submissions and their analyses
- `processes/` — end-to-end workflows and subprocesses
- `policies/` — validated policy/rule records
- `forms/` — blank-form purpose, ownership, inputs, outputs, and workflow links
- `systems/` — ADP, Outlook/EarthLink, Office, spreadsheets, local tools, and other systems as evidenced
- `roles/` — responsibility and handoff definitions
- `exceptions/` — documented alternate paths and edge cases
- `questions/` — unresolved ambiguities and conflicts
- `automation/` — candidate automations and prerequisites
- `sources/` — full searchable safe source corpus, source manifests, version metadata, and batch indexes
- `restricted-evidence/` — metadata-only provenance for live employee/applicant/medical/incident case records; never raw case content

## Modeling rules

Every durable claim should be traceable to evidence.
Every uncertain claim should carry a validation state.
Every conflict should preserve both sides until resolved.
Every employee-specific fact should remain outside the generalized knowledge layer.
Every automation proposal should distinguish current observed process from proposed future behavior.

## Initial domains

The model can grow organically from supplied documents, including:
- recruiting and applicant intake;
- interviewing and selection;
- pre-employment requirements;
- onboarding/new hire processing;
- personnel-file maintenance;
- payroll/time/overtime interactions;
- benefits;
- attendance;
- leave/FMLA;
- workers' compensation;
- disciplinary actions;
- training/compliance;
- terminations;
- unemployment or post-employment administration;
- reporting/audits;
- document scanning, naming, filing, and retention;
- internal/external correspondence workflows.

No domain is assumed complete merely because it has a page.

## Ingestion checkpoint — batch 001

Batch 001 contains 14 source documents:
- 11 safe position-level sources preserved as full searchable representations;
- 3 live case records retained only as privacy-safe metadata/provenance;
- 15 derived process, policy, form, and role records;
- a currentness/gap queue so future sources can corroborate, conflict with, or supersede existing records.

See `sources/batches/rtec-hr-batch-001.json` and `questions/currentness-and-gaps.json`.

The current GitHub connector writes UTF-8 text records rather than arbitrary local binary artifacts. Therefore the complete searchable content and hashes are canonical in GitHub now; safe original binaries should also be synchronized later through a local Git-capable Agent OS workflow where practical. This limitation never permits live case binaries to be committed.


## AAP package — June 30, 2022

The historical RTEC AAP/EEO package built around the June 30, 2022 workforce snapshot is indexed at `plans/aap-2022-06-30/`. It includes the binder structure, full safe source mirrors, aggregate workforce/activity/availability analyses, historical complaint forms and investigation log, placement-goal analysis, and a data-quality review.

Two employee-level source rosters are retained only as restricted metadata because they contain direct identifiers and sensitive EEO/personnel attributes. The 2018 driver-orientation document included with the package was an exact duplicate of the existing canonical source and is referenced rather than duplicated.

Later AAP packages should link to this plan through explicit supersession/version relationships rather than overwriting it.


## Job-description archive — September 23, 2026

The supplied historical job-description archive is indexed under `sources/job-descriptions/` and `roles/job-description-history.json`.

The archive contains 55 observed files: 51 safe position-level/reference sources preserved as full searchable mirrors across 14 source groups, and 4 employee-specific temporary light-duty descriptions retained only as sanitized restricted metadata. Exact duplicate artifacts and materially different historical versions are preserved through provenance rather than silently overwritten.

The source set includes operational and administrative roles such as Transit Driver, Dispatcher, Area Manager, Operations Manager, Fleet Manager, Automotive Mechanic, Garage Attendant, Human Resources Manager, Information Systems Technician, Mobility Manager, Customer Service Representative, Receptionist, Bookkeeper, Food Service/Cafeteria roles, Accounts Receivable, administrative support, procurement, quality control, and temporary scanning/clerical roles, plus recruitment-context and external-sample material.

Job-description language is historical/unknown by default. Pay, benefits, FLSA classification, safety-sensitive status, qualifications, physical requirements, testing requirements, licensing, reporting relationships, and duties must be reconciled against current approved authority before operational use. See `questions/currentness-and-gaps.json` for the resulting validation queue.


## Correspondence archive - September 23, 2026

The supplied `Correspondence.zip` archive is indexed at `sources/batches/rtec-hr-correspondence-2026-09-23.json`.

The batch contains 95 file artifacts. Nine safe position-level artifacts were consolidated into eight searchable source families, while 86 employee-level disciplinary, medical, incident, schedule, leave-case, and participant-list artifacts are retained only as privacy-safe hash/class metadata under `restricted-evidence/correspondence-2026-09-23.json`.

Derived knowledge includes the legacy employee-evaluation template, historical disciplinary point/reference material, a 2015 vacation-adjacent personal/sick-leave rule candidate, 2016 administrative time/leave routing, a 2015 CSR client-assistance instruction, a 2021 rotation-schedule absence rule, 2021 unemployment-fraud guidance, a 2021 preventive-vaccination event process, historical disciplinary-log/AAP reporting structure, and a content-first document-classification rule.

Notable ingestion findings: the supplied `Disciplinary steps` workbook is a blank violation matrix with no embedded offense-point values; the archive contains long-running fiscal-year disciplinary logs and AAP-sorted derivatives; and filenames are not reliable authority for type or date, so content-derived titles/dates should take precedence with mismatch logging. Historical policy, benefits, external-link, vendor, point-system, and routing statements remain version-aware evidence rather than current operational authority.


## Historical HR email archive — September 23, 2026

A flattened and deduplicated HR mailbox corpus of **576 unique messages** spanning **April 2016 through June 2026** has been structurally ingested. The raw PII-bearing email corpus remains outside GitHub; only sanitized process, organization, system, role, professional-contact and currentness findings are canonicalized here.

The corpus exposed 11 recurring HR workflow families and **122 historical self-task/reminder messages**, showing that email itself functioned as an informal task and follow-up system. Durable findings include benefits administration, payroll/time/tax coordination, leave/FMLA, workers compensation/return-to-work, EEO/AAP reporting, recruiting, retirement/401(k), unemployment/new-hire reporting, service-anniversary tracking, HR document/website maintenance, and cross-role/vendor handoffs.

Current 2026 evidence confirms active interaction with the shared RTEC HR mailbox, ADP, Guardian, iSolved, Kentucky employment-reporting portals, UnitedHealthcare, 3CX and Google tooling. Rippling is recorded only as vendor-evaluation/contact evidence, not as an implemented system.

See:
- `sources/batches/rtec-hr-email-archive-2016-2026-2026-09-23.json`
- `processes/email-derived-hr-work-patterns-2016-2026.json`
- `systems/email-derived-system-vendor-timeline-2016-2026.json`
- `company/email-derived-company-profile-2016-2026.json`
- `roles/current-hr-role-email-evidence-2026.json`
- `roles/email-derived-professional-contact-map-2016-2026.json`
- `roles/hr-handoff-network-email-evidence-2016-2026.json`
- `questions/email-derived-gaps-2026-09-23.json`
- `../../../projects/rtec-hr-process-model/docs/EMAIL_ARCHIVE_INGESTION_2026-09-23.md`

Email-derived historical practices remain version-aware evidence and must not override current policy, system authority or user-confirmed workflow ownership.


### Email-archive deepening index

The consolidated discovery index for the sanitized email-derived knowledge is `sources/email-archive-derived-index-2026-09-23.json`. It links the domain-specific benefits, payroll/time/tax, leave/FMLA, workers' compensation, EEO/AAP, recruiting, retirement, unemployment, Kentucky new-hire, system/vendor, account-continuity, training/reference, company, role, professional-contact, handoff, mailbox-transition, automation-candidate, and validation-question records.

Every one of the 576 unique messages received a structural classification pass, and the initial low-signal bucket received a separate review. Semantic records remain currentness-gated and privacy-safe; raw employee/applicant/case email content is not canonicalized in GitHub.


## Correspondence archive — exhaustive analysis checkpoint

The September 23, 2026 correspondence archive has completed an exhaustive source-level analysis. All 95 supplied artifacts have an explicit disposition: 9 safe artifacts consolidated into 8 reusable source families and 86 restricted artifacts covered through privacy-safe metadata, aggregate analysis and generalized process/policy records. All 33 individual warning/counseling files map to at least one generalized knowledge theme.

The disciplinary corpus contains 1,193 populated fiscal event rows. From 2016-2017 onward the historical “disciplinary” register also functions as a vehicle-incident ledger. AAP-sorted workbooks are treated as separate derived versions because cross-year reconciliation found omitted/extra occurrences, hard-coded subtotal rows and classification changes; notably, one 2016-2017 derivative systematically recodes many EEO categories. No formulas were detected in the 29 disciplinary/AAP/verbal-warning workbooks.

Legacy import must preserve stable source-row identity, raw values and schema/version provenance. Employee+date and employee+date+reason are not safe deduplication keys because legitimate same-date multi-record groups exist. Current-state gaps are tracked in `questions/currentness-and-gaps.json`; rereading this archive is not expected to resolve those gaps without newer authoritative sources.

See:
- `sources/batches/rtec-hr-correspondence-2026-09-23.json`
- `restricted-evidence/correspondence-2026-09-23.json`
- `restricted-evidence/disciplinary-register-aggregate-2008-2026.json`
- `processes/aap-disciplinary-derivative-integrity.json`
- `automation/disciplinary-register-normalization.json`


## Current operational discovery index — September 23, 2026

The historical email/PST source is now exhausted at the structural, attachment,
deduplication and major-domain semantic level. Current operations should enter
through `sources/current-operational-derived-index-2026-09-23.json`, not by
assuming the email archive remains the best current source.

Current/live evidence now includes:

- active 2026 FMLA and Attendance trackers;
- ADP-derived attendance input;
- current benefits-plan comparison work;
- current county/openings planning;
- the 2025 Kentucky EEO certification expiring September 30, 2026;
- the canonical Fillout -> Google bridge -> Applicant Dashboard recruiting pipeline;
- the restricted Applicant Dashboard -> Personal Agent OS adapter contract;
- current public ridertec.org content/security/version-drift findings.

### Applicant pipeline

The canonical current recruiting data path is:

```text
Fillout
-> Google Sheet/Drive transport
-> process_applications.py
-> application/resume + separate restricted self-ID artifact
-> download_log.csv
-> dashboard.db
-> restricted Agent OS applicant adapter
```

Agent OS must not independently ingest raw Fillout applicant rows. It uses
whitelisted administrative projections from the Dashboard layer. Restricted
self-ID remains outside ordinary recruiting tools. The agent may help organize,
summarize, track documents/status/scheduling and prepare user-directed
administrative drafts, but it does not rank applicants or make employment
decisions.

### Public website currentness

Current public pages have material version drift across English/localized
surfaces, recruiting content, service-area facts, compliance documents and
named-role information. A current public instruction page also exposed
credential-like kiosk values; those values are not stored here and should be
treated as compromised until rotated/removed.

See:

- `systems/public-website-eeo-titlevi-currentness-drift-2026-09-23.json`
- `systems/public-recruiting-website-currentness-drift-2026-09-23.json`
- `systems/public-website-company-recruiting-audit-2026-09-23.json`
- `compliance/public-website-compliance-document-drift-2026-09-23.json`
- `security/public-website-security-sensitive-exposure-audit-2026-09-23.json`
- `automation/public-website-currentness-monitor-candidate.json`

The open current-authority queue remains
`questions/currentness-and-gaps.json`.


## Downloads spreadsheet cleanup — September 24, 2026

A loose set of **16 legacy XLS artifacts** from the user's Downloads folder was classified and integrated under `sources/batches/rtec-hr-downloads-spreadsheets-2026-09-24.json`. The set resolves to eleven logical source families after semantic duplicate handling.

Two blank historical benefits-administration import templates were added to the reusable reference-form catalog: an employee demographic import template and an Infinisource FSA/HSA/transit/parking enrollment import template. Their field/validation semantics are preserved as historical system evidence, not current authority.

Nine employee/subscriber-level benefits artifacts are restricted: FSA account-balance detail, Delta Dental/vision consolidated billing workbooks from 2020–2024, and a dependent-termination export. Only safe report structure, calculation definitions, hashes, dates and document-type evidence were promoted; no names, SSNs, subscriber IDs, dates of birth, individual balances or individual billed amounts were retained.

Three aggregate/external reference datasets were cataloged separately: a Commonwealth of Kentucky MWBE certified-vendor listing marked as of January 16, 2020; Kentucky county population change/ranks for 2000–2010; and U.S. Census 2000 DP-2/DP-3/DP-4 social, economic and housing profiles. These are historical reference data and do not establish current HR policy.

Document routing learned from this batch is explicit: multi-person benefits reports belong in restricted benefits-administration context and must not be auto-filed to one employee; blank import spreadsheets are contextual reference forms; census/MWBE/population workbooks are external reference datasets.

See:
- `sources/batches/rtec-hr-downloads-spreadsheets-2026-09-24.json`
- `restricted-evidence/downloads-spreadsheets-2026-09-24.json`
- `forms/downloads-spreadsheet-document-types-2026-09-24.json`
- `systems/historical-benefits-data-import-contracts-2018.json`
- `processes/historical-benefits-billing-reconciliation.json`
- `sources/reference-data/downloads-reference-data-2026-09-24.json`
- `questions/downloads-spreadsheets-currentness-2026-09-24.json`
