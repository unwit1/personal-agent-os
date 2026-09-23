# Email Archive Ingestion — 2026-09-23

## Scope

This ingestion models a flattened historical RTEC HR mailbox corpus containing **576 unique messages** spanning **2016-04-28 through 2026-06-26**.

The source archive was derived from two PST files that were flattened and deduplicated before analysis. The email corpus itself is **not committed to GitHub** because it contains employee/applicant/case material and other sensitive information.

## Privacy boundary

The RTEC HR knowledge-library rules continue to apply:

- no raw employee/applicant email bodies;
- no raw case narratives;
- no medical, leave, discipline, compensation, beneficiary, address, identifier, or applicant-record details;
- no indiscriminate contact dump;
- no generalization of a one-off case into policy.

Only process-level findings, professional role relationships, system/vendor context, sanitized counts, and provenance IDs are promoted.

## Corpus checkpoint

- 576 unique messages
- observed years: 2016, 2017, 2018, 2019, 2020, 2021, 2026
- 122 messages classified as informal HR self-task/reminder records
- 10 messages classified as restricted applicant-record material
- 32 messages flagged as potential employee-case material
- 13 messages classified as personal/non-work
- raw text retained outside GitHub

Source hashes are recorded in:
`knowledge/libraries/rtec-hr/sources/batches/rtec-hr-email-archive-2016-2026-2026-09-23.json`.

## Major findings

### HR work model

The historical mailbox shows a broad HR function spanning:

- benefits administration;
- payroll/time/tax coordination;
- leave, attendance and FMLA;
- workers compensation and return-to-work;
- EEO-1, affirmative-action and contract-compliance work;
- recruiting/applicant intake;
- retirement/401(k) administration;
- unemployment and new-hire reporting;
- service-anniversary tracking;
- HR forms, packets, website content and document maintenance.

The archive strongly demonstrates that historical HR work was deadline- and follow-up-heavy. Email was repeatedly used as an informal task queue rather than merely as correspondence.

### Organization and handoffs

HR repeatedly coordinated with executive leadership, finance/IT, procurement/administration, training/compliance and operations, plus external payroll, benefits, insurance, state-agency and HR-technology contacts.

The durable handoff model lives at:
`knowledge/libraries/rtec-hr/roles/hr-handoff-network-email-evidence-2016-2026.json`.

### Systems

The archive shows a layered and changing HR technology environment rather than evidence of one continuous all-in-one platform. Systems and relationships include ADP, Guardian, CVIM, iSolved/Infinisource, UnitedHealthcare, Kentucky new-hire/unemployment portals, 3CX, Google tooling and a 2026 Rippling evaluation/contact.

A vendor contact, demo or meeting invitation is explicitly **not** treated as implementation evidence.

### People profiles

A privacy-safe professional contact map was created for recurring internal role holders and external professional contacts. These profiles contain only job/organizational context and recurring work relationships.

The exhaustive raw header/contact index remains outside GitHub because it includes one-off identities and contacts that may be linked to employee/applicant cases.

## Current 2026 signals

The archive directly supports current activity involving:

- the shared RTEC HR mailbox;
- Guardian benefits-account administration;
- ADP quarter-end/payroll-related communications;
- iSolved account/billing communications;
- Kentucky unemployment and new-hire portals;
- UnitedHealthcare account contacts;
- RTEC 3CX and Google tooling;
- HR-technology/vendor evaluation.

These current signals do not establish every historical HR task as part of the current HR manager's duties. Historical scope is marked as inherited/to-verify until current sources corroborate it.

## Derived records

- `knowledge/libraries/rtec-hr/processes/email-derived-hr-work-patterns-2016-2026.json`
- `knowledge/libraries/rtec-hr/systems/email-derived-system-vendor-timeline-2016-2026.json`
- `knowledge/libraries/rtec-hr/company/email-derived-company-profile-2016-2026.json`
- `knowledge/libraries/rtec-hr/roles/current-hr-role-email-evidence-2026.json`
- `knowledge/libraries/rtec-hr/roles/email-derived-professional-contact-map-2016-2026.json`
- `knowledge/libraries/rtec-hr/roles/hr-handoff-network-email-evidence-2016-2026.json`
- `knowledge/libraries/rtec-hr/questions/email-derived-gaps-2026-09-23.json`

## Next semantic-deepening passes

The structural pass covered every message. Further passes should continue to deepen the same corpus without weakening privacy boundaries:

1. thread/subject-family reconstruction;
2. role-to-role handoff sequence extraction;
3. recurring deadline/cadence recovery;
4. form/document references and aliases;
5. current-vs-historical supersession comparison against policies, job descriptions and later HR sources;
6. automation-candidate extraction from repeated reminders;
7. safe professional-contact enrichment where multiple messages establish a stable work relationship;
8. spam/phishing/low-value-mail triage analysis for the current shared mailbox.

Every deeper claim should remain linked to message archive IDs and should be promoted only when recurrence or an independent safe source supports it.
