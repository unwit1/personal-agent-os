# RTEC HR Knowledge Library

This library is the durable, privacy-safe process model for RTEC HR.

## Structure

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
