# Email Archive Semantic Deepening — Pass 003 — 2026-09-23

## Scope

Pass 003 deepens the 576-message historical RTEC HR mailbox analysis using cross-source comparison against:

- historical HR/EEO/Benefits/HR Manager duty documents;
- the current December 15, 2025 handbook-derived policy records;
- the RTEC compliance/AAP version archive;
- the reusable HR reference-form catalog.

No raw employee/applicant/case message text is promoted into GitHub.

## New findings

### 1. Recurring work cadences can now be separated from one-off reminders

Email recurrence plus independent role-document evidence establishes several historical recurring cycles with stronger confidence:

- monthly check-register verification;
- first-of-month HR reporting;
- monthly insurance invoice retrieval/AP handoff;
- annual EEO-1;
- annual state EEO recertification;
- annual Medicare creditable-coverage notice/CMS workflow;
- recurring service-anniversary recognition;
- daily/periodic attendance tracking;
- recurring payroll/time approval;
- periodic W-4/K-4 version monitoring;
- Census/QuickFacts refresh work for compliance planning.

These are **historical cadence candidates**, not automatically active schedules. Current-authority validation is required before Agent OS creates recurring tasks.

### 2. AAP chronology was reconciled

The email reminder `000085` (“AAP DUE TO STATE JAN 2022”) matched the **2018 state approval letter**, which set the next plan due **2022-01-01**.

A later **2020-12-30 state approval** superseded that schedule and set the next plan due **2024-01-30**.

The compliance archive contains a full plan family updated through **2024-06-30**.

Remaining gap: approval/submission correspondence for the 2024 cycle and the approved plan governing after June 2024.

### 3. Historical role duties are strongly corroborated by email behavior

Cross-source agreement now supports historical responsibility for:

- benefits enrollment/change administration;
- check-register review;
- FMLA notices/document tracking;
- workers-comp claim documentation and return-to-work follow-up;
- EEO-1/state certification/AAP;
- service awards;
- website job postings;
- temporary staffing/Job Shop handoffs;
- retirement/401(k);
- attendance tracking;
- monthly insurance invoices.

Where the 2025 handbook provides newer policy authority, it is explicitly preferred over the old duty document.

### 4. Form/document aliases were mapped

Email shorthand has been connected to the existing blank/reference-form library where evidence supports the mapping, including:

- FMLA Designation Notice WH-382;
- FMLA request/certification/eligibility bundle;
- Direct Deposit Form;
- Termination Letter / termination forms;
- transfer forms;
- workers-comp Wage Statement, Supervisor Statement and Witness Statement;
- employment application;
- Guardian packet candidates.

Additional document classes were identified but are not yet backed by a canonical reference artifact, including:

- First Report of Injury;
- medical/off-work statement;
- Absentee Report;
- Personal Time Taken List;
- Monthly HR Report;
- Payroll Check Register;
- Medicare Creditable Coverage Notice;
- CMS Creditable Coverage Disclosure;
- COBRA ARPA mailed-notices report;
- Kentucky New Hire upload preview/completion;
- ADP quarter-end tax/payroll reports;
- staffing agreement;
- CSR training completion certificate.

### 5. Email thread lifecycles expose completion states

Reconstructed thread families show that many HR tasks are not binary “send and done” operations. They have states such as:

- requested;
- missing document;
- resent;
- acknowledged;
- corrected;
- previewed;
- submitted;
- approved;
- restored;
- reconciled.

This matters for Agent OS: it should track external acknowledgment and closure, not just create a task.

### 6. Current Kentucky new-hire upload lifecycle was reconstructed

On 2026-05-15:

1. initial preview failed with 8 records: 7 previously submitted duplicates and 1 rejected for employer-city field validation;
2. a corrected preview succeeded with 1 acceptable, 7 previously submitted duplicates and 0 rejected;
3. final submission succeeded with the same accepted/duplicate counts and no within-file duplicate records.

The file name itself carried a 2025 date despite the 2026 submission, so filename dates must not be trusted as reporting-period authority.

### 7. Benefits-carrier history is richer than previously modeled

2016 implementation correspondence records:

- Baptist Health Plan — medical;
- Humana — dental/vision;
- The Abacus Group — voluntary life/short-term disability.

A formal Humana implementation kickoff appears in 2018.

By 2026, UnitedHealthcare correspondence explicitly references a recent implementation, while Guardian remains active for other benefits administration.

This creates a historical provider/version chain, not a single timeless benefits stack.

### 8. Historical HR title transition was gradual

Mailbox signatures show:

- EEO/Benefits Manager from 2016 through at least 2021-07-06;
- Human Resource Manager beginning by 2021-03-11 and continuing through at least 2021-09-29.

The overlap means an exact title-change date cannot be inferred from signatures alone.

### 9. Raw mailbox indexing needs a secret-redaction layer

The raw mailbox contains authentication/security messages and credential-like values alongside HR content.

The durable control is now:

- raw messages stay out of GitHub;
- secret-like values are redacted before semantic indexing or model context;
- case text remains restricted/local;
- sanitized derived knowledge and message IDs provide durable provenance.

## New durable records

- `knowledge/libraries/rtec-hr/roles/email-job-duty-corroboration-matrix-2016-2026.json`
- `knowledge/libraries/rtec-hr/automation/recurring-cadence-candidates-email-role-evidence.json`
- `knowledge/libraries/rtec-hr/forms/email-derived-form-document-alias-registry-2016-2026.json`
- `knowledge/libraries/rtec-hr/roles/professional-relationship-chronology-email-evidence-2016-2026.json`
- `knowledge/libraries/rtec-hr/processes/email-thread-lifecycle-patterns-2016-2026.json`
- `knowledge/libraries/rtec-hr/automation/email-archive-sensitive-data-retrieval-boundary.json`
- `knowledge/libraries/rtec-hr/plans/aap-email-compliance-chronology-reconciliation.json`
- `knowledge/libraries/rtec-hr/roles/hr-work-profile-synthesis-email-role-policy-2026.json`

Several existing email-derived records were also deepened.

## Remaining high-value analysis

The corpus has now been structurally covered and deeply modeled by domain. Remaining work is primarily cross-corpus enrichment rather than first-pass email reading:

1. compare every email-derived form alias against the HR-GUI fingerprint library and add missing fingerprints/rules;
2. recover exact historical spreadsheet/report schemas where safe source copies exist;
3. derive a current-vs-historical responsibility matrix for the present HR Manager role;
4. resolve provider/system ownership for 2026 benefits and payroll;
5. locate post-June-2024 AAP approval/plan evidence;
6. compare recurring email-derived task candidates against the current calendar, ADP/portal responsibilities, and user-confirmed work;
7. build restricted local retrieval so case emails can support task execution without becoming durable generalized knowledge.
