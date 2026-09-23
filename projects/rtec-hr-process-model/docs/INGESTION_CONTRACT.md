# RTEC HR Process Model — ingestion contract

## Purpose

Turn supplied HR documents into durable, privacy-safe operational knowledge without turning GitHub into an employee-record repository.

## Intake classes

### Safe-to-model directly
Examples include:
- policy manuals;
- procedure guides;
- blank forms and templates;
- checklists;
- training materials;
- system instructions;
- vendor guidance;
- sanitized examples;
- organizational reference material.

### Restricted live records
Examples include:
- completed employee/applicant forms;
- resumes and applications;
- benefits/medical/leave records;
- disciplinary records;
- payroll or compensation records;
- background/driving-history records;
- identity documents;
- correspondence containing employee-level facts.

Restricted records may be used only when the governing task explicitly permits analysis. Their raw content and employee-level facts must not be committed to GitHub. If a process rule is inferred from a restricted record, store only the generalized rule, safe provenance, confidence, and any required review question.

## Required provenance

Every source-derived knowledge record should retain:
- sanitized `source_id`;
- safe source type/class;
- source date/version when known;
- content hash when available;
- page/section/location;
- ingestion date;
- evidence type: explicit text, structural evidence, repeated observation, or user clarification;
- confidence;
- validation state.

Do not store unsafe source filenames or verbatim excerpts containing PII.

## Claim discipline

Separate:
1. **Observed fact** — what the source explicitly says or structurally demonstrates.
2. **Interpretation** — what that evidence appears to imply about the workflow.
3. **Rule candidate** — a reusable process rule proposed from one or more observations.
4. **Canonical rule** — a validated rule safe to rely on operationally.

Use relationship labels:
- NEW
- DUPLICATE
- EXTENDS
- CONFLICTS_WITH
- DEPENDS_ON
- SUPERSEDES

## Process record expectations

A mature process record should identify, where evidence permits:
- purpose;
- trigger;
- prerequisites;
- responsible actor;
- ordered steps;
- systems used;
- required forms/documents;
- decisions/branches;
- deadlines;
- outputs;
- downstream handoffs;
- exceptions;
- controls/audit evidence;
- unresolved questions;
- automation candidates;
- source provenance.

## Conflict handling

Never resolve conflicting policies by guessing. Preserve both claims, their dates/versions/sources, mark the relationship as `CONFLICTS_WITH`, and generate a review question.

## Case-to-rule safeguard

A single employee case is not automatically a policy. Case evidence can:
- reveal that an exception exists;
- expose an undocumented branch;
- suggest a rule candidate;
- demonstrate actual system behavior.

It cannot by itself establish a universal HR rule unless the user confirms it or other evidence corroborates it.

## Writeback behavior

After substantive ingestion:
- update or create the relevant knowledge records;
- update the source manifest/index;
- attach evidence to existing rules when appropriate rather than duplicating them;
- capture unresolved questions;
- capture automation opportunities separately;
- commit a coherent sanitized checkpoint.
