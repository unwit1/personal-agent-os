# RTEC HR Process Model

A provenance-backed model of how RTEC HR work is actually performed.

This project learns from process documents, policies, blank forms, templates, instructions, correspondence patterns, and user clarification. It exists to make RTEC HR work searchable, explainable, automatable, and resumable across ChatGPT, Codex, Claude, and future Personal Agent OS clients.

## Canonical boundary

GitHub is canonical for **the safe authoritative source corpus plus derived, sanitized process knowledge**.

Process documents, manuals, policies, procedure guides, blank forms/templates, training materials, system instructions, and similar position-level reference material should be preserved **in full** when they do not contain prohibited employee/applicant PII. Preserve the original file when practical and also maintain a searchable full-text/structured mirror so agents can quote, diff, search, and re-derive knowledge later.

This corpus spans roughly the last 20 years and is historical by default. Age does not make a source disposable: retain superseded material for chronology, but never assume an older source is current merely because it exists in the corpus.

Do not commit:
- employee or applicant records;
- completed forms;
- raw document images;
- raw OCR from live HR documents;
- names, addresses, identifiers, medical/leave facts, compensation values, disciplinary facts, or other employee-level PII;
- source filenames when those filenames contain employee/applicant PII.

Live personnel/applicant source records remain outside GitHub. Safe position-level process sources are stored in full under the RTEC HR source corpus, with a sanitized source ID, original/source artifact when practical, searchable text mirror, cryptographic content hash when available, date/version metadata, and page/section provenance.

## Knowledge lifecycle

Document-derived statements move through:

`extracted -> candidate -> validated -> canonical`

Additional states:
- `conflicted` — credible sources disagree;
- `superseded` — replaced by a newer policy/process;
- `case_only` — evidence describes an individual case and must not become a general rule;
- `rejected` — reviewed and determined not to represent the process.

No uncertain statement is silently promoted to canonical knowledge.

## What the model captures

The model may represent:
- processes and subprocesses;
- triggers and prerequisites;
- actors/roles and handoffs;
- forms and supporting documents;
- systems and tools;
- inputs and outputs;
- decision rules and approval gates;
- deadlines and timing rules;
- exceptions and alternate paths;
- controls, audit requirements, and record-retention behavior;
- dependencies between workflows;
- recurring manual work and automation candidates;
- unresolved questions and contradictory evidence.

## Knowledge location

Durable knowledge lives under `knowledge/libraries/rtec-hr/`.
Project state and ingestion rules live under `projects/rtec-hr-process-model/`.
The reusable record contract lives in `schemas/rtec-hr-knowledge-v1.schema.json`.

## Initial workflow

For each supplied document:

1. Determine whether it is safe process evidence or contains live employee/applicant PII.
2. If live PII is present, do not commit the document, raw OCR, or employee-level facts.
3. Assign a sanitized source ID, determine source date/effective period/currentness, and capture safe provenance.
4. If it is a safe process/manual/policy/reference source, preserve the source in full and create or update its searchable text mirror.
5. Extract explicit process claims separately from interpretation.
6. Link claims to existing workflows, forms, systems, roles, and rules.
7. Classify each claim as NEW, DUPLICATE, EXTENDS, CONFLICTS_WITH, DEPENDS_ON, or SUPERSEDES existing knowledge.
8. Compare dates/versions and preserve supersession chains; newer does not automatically mean authoritative when scope differs.
9. Record unresolved questions when evidence is incomplete, ambiguous, undated, or conflicts with later material.
10. Promote only corroborated or user-confirmed knowledge to validated/canonical state, with explicit currentness status.
11. Capture automation opportunities separately from factual process rules.
12. Commit coherent sanitized checkpoints so other agents can resume without rereading every source.


## Cross-project reference forms

Reusable blank/reference forms and templates from related HR projects are indexed in `knowledge/libraries/rtec-hr/forms/reference-form-catalog.json`. Usage and authority rules are documented in `projects/rtec-hr-process-model/docs/REFERENCE_FORM_CONTEXT.md`.

Agents should consult this catalog when identifying forms, aliases, fields, page structure, workflow inputs/outputs, scanner fingerprints, and missing process evidence. Form presence is contextual evidence only; it does not by itself establish current policy or an effective workflow rule.
