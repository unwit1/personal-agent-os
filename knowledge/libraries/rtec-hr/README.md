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
