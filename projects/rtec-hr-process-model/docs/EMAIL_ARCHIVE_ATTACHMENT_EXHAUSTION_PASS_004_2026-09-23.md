# Email Archive Attachment Exhaustion — Pass 004 — 2026-09-23

## Scope

Pass 004 completes the recovered PST attachment layer on top of the 576-message body analysis.

## Extraction and deduplication

- 69 messages carried attachments.
- 132 attachment payload occurrences were recovered.
- 104 unique SHA-256 payload objects remain after exact deduplication.
- 19 hashes occurred more than once, accounting for 28 repeated occurrences beyond the first copy.
- Parser errors: 0.

Exact duplicate hashes are analyzed once and linked to all message occurrences. Template similarity is never used to delete distinct completed HR records.

## Privacy triage

### Safe/reusable organizational material

Examples analyzed and modeled:
- February 2017 RTEC Employee Handbook;
- April 2018 Humana medical installation kickoff deck;
- 2020-2021 benefit contribution/scenario workbooks;
- historical blank termination-to-payroll form;
- historical blank direct-deposit form;
- June 2021 UnitedHealthcare Base and Buy Up plan summaries;
- 2021 CSR / Accounts Receivable recruiting advertisement;
- historical Budgeting Basics training invitation metadata;
- June 2026 UnitedHealthcare men's-health resources in English and Spanish.

### Restricted/local material

Completed applications, medical bills, emergency-room documents, First Report of Injury packets, doctor/ambulance records, verification-of-employment records, salary census, employee-specific enrollments, FSA receipts, workers-comp supporting documents, payroll statements, invoices/account records and person-level credential images remain local/restricted.

No employee case details from those sources were promoted into GitHub.

### Security-sensitive attachment material

ICS/calendar files can include conferencing access URLs, meeting passcodes and reschedule/access parameters. Durable knowledge retains only safe meeting/business metadata; access credentials are excluded.

## Major new findings

### UHC chronology corrected

UnitedHealthcare plan summaries were already present in June 2021. Therefore 2026 correspondence describing a recent UHC implementation does not prove first-time UHC adoption. It may represent a new plan, configuration, account transition or reimplementation.

### Humana 2018 implementation workflow

The April 2018 kickoff deck documents:
- medical effective date June 1, 2018;
- initial enrollment via enrollment spreadsheet;
- ongoing enrollment changes through Humana HRBA;
- pay-as-billed billing;
- employer-portal eBilling and bill-ready notification;
- implementation-calendar follow-up;
- later installation wrap-up/transition meeting.

### Benefits renewal was an analytical workflow

2020-2021 contribution workbooks show RTEC comparing multiple employer-contribution percentages and competing carrier combinations, considering employer and employee cost consequences, FSA funding and Guardian life/disability continuity.

### 2021 UHC plan variants

The June 2021 attachments include:
- Base Plan BW3C;
- Buy Up Plan BW24.

The plan summaries are historical plan-year documents and explicitly defer to formal coverage documents when conflicts exist.

### Historical termination control

The old Notice to Payroll form coordinated termination of:
- direct deposit;
- term life;
- health;
- dental;
- vision;
- Abacus life/disability;
- 401(k) contribution.

It included Benefits Manager preparation and Executive Director approval.

### Direct-deposit record sensitivity

The historical blank direct-deposit form collects routing/account data and requires a voided check/deposit slip. Completed copies are high-sensitivity financial records even though the blank template is safe.

### Handbook policy evolution

The 2017 handbook provides a strong historical baseline. Several core rules remained stable into 2025, while other rules changed materially.

Most important change identified in this pass:
- 2017 attendance termination threshold: 10 points.
- 2025 current handbook: termination at 6 points with a changed progressive point schedule.

Historical named EEO ownership is also superseded by later effective-dated sources.

### Image audit

All unique image attachments were visually reviewed at contact-sheet level.

The generic image layer consisted mainly of:
- logos/signature graphics;
- vendor/marketing branding;
- restricted person-level screenshots/receipts/credential images;
- social/non-work photos;
- vendor wellness resource graphics.

No previously hidden policy, blank form or major report source was found only in the generic-image layer.

## Cross-project propagation

Findings were propagated into:
- benefits administration model;
- vendor/system chronology;
- recruiting channel history;
- training/resource map;
- professional contact map;
- blank-form/reference mapping;
- policy-version history;
- mail secret/PII retrieval controls;
- HR-GUI scanner/report-gap roadmap.

## Current professional contact map

Attachment-only Humana implementation roles added:
- Steven Farmer — Sales Executive;
- Lisa Clark — Client Executive;
- Emily Fackler — Telesales Executive.

Professional-only context is retained. Employee/applicant/case profiles were not created from restricted attachments.

## Remaining source limitations

The recovered attachment layer itself is exhausted at the payload/classification level.

Remaining analytical gaps are no longer unprocessed PST content. They are missing/current-source questions such as:
- current retirement provider/workflow;
- current workers-comp carrier/administrator;
- post-June-2024 AAP approval/plan;
- authoritative live-copy designation for duplicated/migrated trackers;
- current payroll/benefits ownership boundaries;
- current EEO certification renewal after the approval expiring September 30, 2026.

These require newer authoritative sources or live system evidence rather than more mining of the same PST.
