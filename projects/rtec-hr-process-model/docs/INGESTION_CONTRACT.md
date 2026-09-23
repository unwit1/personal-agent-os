# RTEC HR Process Model — ingestion contract

## Purpose

Turn supplied HR documents into a durable, privacy-safe, version-aware source corpus and operational knowledge model without turning GitHub into an employee-record repository. The supplied corpus may span roughly 20 years; historical preservation and current-policy determination are separate concerns.

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

### Full-source preservation rule

For safe position-level materials, preserve the **entire source**, not merely a summary. When practical retain both:
- the original source artifact or a lossless repository-safe representation; and
- a searchable full-text/structured mirror with stable headings/page markers.

This applies to manuals, policies, procedures, training materials, system guides, blank forms/templates, checklists, and other reference documents for the HR position. Derived records must point back to the exact source/version so future agents can search, quote, diff, and re-evaluate the evidence.

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
- document creation/revision/effective/retirement dates when available;
- temporal status: current, historical, superseded, future-effective, unknown, or conflicting;
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


## Historical corpus / temporal reasoning

The document base spans approximately two decades. Therefore:

- Treat every source as historical evidence until its effective period and currentness are established.
- Preserve obsolete and superseded documents; they are part of the process history and may explain legacy files, terminology, or decisions.
- Never silently replace an older document with a newer one. Link versions through `SUPERSEDES` / `superseded_by` relationships.
- Prefer explicit effective/revision dates over filesystem timestamps or filename dates.
- A newer document is not automatically controlling if it covers a different department, employee class, program, jurisdiction, or process scope.
- When no current authority can be established, mark the rule/currentness as `unknown` and generate a question rather than presenting it as current policy.
- When answering "how do we do this now?", prioritize current/validated sources and clearly separate historical practice.
- When analyzing why an old employee file was handled a certain way, use the source version that was effective or likely operative at that time.
