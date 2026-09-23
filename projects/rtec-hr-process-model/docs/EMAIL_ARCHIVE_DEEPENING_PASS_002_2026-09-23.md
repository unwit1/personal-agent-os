# Email Archive Semantic Deepening — Pass 002 — 2026-09-23

## Purpose

This checkpoint records the second systematic pass over the 576-message RTEC HR email corpus after the full-corpus structural classification.

The goal of Pass 002 was to prevent low-frequency or poorly classified messages from being silently discarded and to deepen professional role, handoff, recruiting-channel, account-continuity, and automation context.

## Low-signal sweep

The initial classifier marked 130 messages as low-signal/unclassified.

All 130 were reviewed at the sender/subject level. A concentrated 2026 group of 92 messages was identifiable as likely unsolicited marketing/spam/phishing-style traffic by sender/domain/subject patterns. The remaining 38 were individually reviewed for process value or privacy sensitivity.

Recovered useful evidence includes:

- historical Kentucky Career Center / Focus Talent recruiting job-order lifecycle;
- a cluster of eight driver/dispatcher job orders that closed together on 2021-12-12 and could be refreshed for another 30 days;
- Indeed recruiting-platform outreach in 2021;
- a 2019 AssuredPartners introductory meeting;
- a 2021 CVIM pre-renewal contact;
- Microsoft Office 365 encrypted-message passcode use;
- Zoom meeting use for HR coordination;
- Microsoft Outlook mailbox configuration/test messages in May 2026;
- Google account appeal/restoration activity in June 2026;
- a June 2026 Google security alert showing the shared HR account used the historical individual HR mailbox as its recovery contact.

Employee-specific verification-of-employment, legal, attendance, medical/leave, discipline, and other case messages were not promoted into people profiles or generalized process rules.

## Professional profiles

The privacy-safe professional-contact map now includes 28 recurring or operationally meaningful contacts across:

- RTEC leadership/administration/finance/operations/training;
- ADP;
- Guardian;
- CVIM;
- UnitedHealthcare;
- Kentucky contract-compliance contacts;
- Indeed;
- USI Insurance Services;
- Energy Insurance Agency;
- AssuredPartners;
- The Job Shop;
- Rippling;
- Spare;
- TESCO;
- community/public-health context.

A contact is not promoted merely because a name appears once. Promotion requires stable professional context that can be separated from an employee/applicant case.

## Account continuity / security

Pass 002 identified a currentness question that should be resolved:

> The June 25, 2026 Google security message says the historical individual HR mailbox is the recovery email for the shared HR Google account.

This is recorded as a verification question, not as evidence of compromise or misconfiguration.

The archive also contains three Microsoft Outlook test messages for the historical HR mailbox in May 2026. This may reflect intentional mailbox continuity, migration, configuration, or archival work; the reason remains unresolved.

## Recruiting history

Pass 002 separates four historical recruiting channels:

1. direct/forwarded applications;
2. ridertec.org online application forms;
3. Kentucky Career Center / Focus Talent job orders;
4. Indeed outreach/platform contact.

These should be compared against the current ADP ATS process rather than treated as one still-active workflow.

## Historical task model

The 122 self-task/reminder messages were re-evaluated as workflow evidence. Conservative keyword-derived lower bounds include:

- leave/attendance: 17;
- benefits/insurance: 16;
- service anniversaries: 15;
- payroll/timesheet/tax: 10;
- discipline/legal: 8;
- EEO/AAP: 7;
- retirement/401(k): 5;
- workers comp/return-to-work: 5;
- website/documents: 4;
- training/credentials: 3;
- recruiting: 2.

Counts overlap and deliberately under-count ambiguous shorthand reminders.

This evidence is now represented as an automation candidate for converting validated historical reminders into structured Agent OS commitments/checklists.

## New/updated durable records

- `knowledge/libraries/rtec-hr/systems/email-infrastructure-access-findings-2016-2026.json`
- `knowledge/libraries/rtec-hr/processes/recruiting-channel-history-email-evidence-2016-2021.json`
- `knowledge/libraries/rtec-hr/automation/email-reminders-to-structured-task-candidate.json`
- expanded `knowledge/libraries/rtec-hr/roles/email-derived-professional-contact-map-2016-2026.json`
- expanded `knowledge/libraries/rtec-hr/roles/current-hr-role-email-evidence-2026.json`
- expanded `knowledge/libraries/rtec-hr/company/email-derived-company-profile-2016-2026.json`
- expanded `knowledge/libraries/rtec-hr/questions/email-derived-gaps-2026-09-23.json`

## Remaining deepening work

The corpus is fully structurally covered. Further semantic passes can still deepen:

- individual thread reconstruction;
- recurring-calendar/cadence inference;
- form/document alias extraction;
- professional relationship chronology;
- cross-source currentness resolution against newer policies/forms/system evidence;
- safe conversion of repeated task sequences into explicit workflow steps.

No remaining pass requires preserving raw employee/applicant case content in GitHub.
