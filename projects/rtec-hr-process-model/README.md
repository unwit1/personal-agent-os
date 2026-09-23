# RTEC HR Process Model

A provenance-backed model of how RTEC HR work is actually performed.

This project learns from process documents, policies, blank forms, templates, instructions, correspondence patterns, and user clarification. It exists to make RTEC HR work searchable, explainable, automatable, and resumable across ChatGPT, Codex, Claude, and future Personal Agent OS clients.

## Canonical boundary

GitHub is canonical for **derived, sanitized process knowledge**.

Do not commit:
- employee or applicant records;
- completed forms;
- raw document images;
- raw OCR from live HR documents;
- names, addresses, identifiers, medical/leave facts, compensation values, disciplinary facts, or other employee-level PII;
- source filenames when those filenames contain employee/applicant PII.

Raw source documents remain outside GitHub. A source may be represented in GitHub by a sanitized source ID, safe document class/title, cryptographic content hash when available, date/version metadata, and page/section provenance.

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
3. Assign a sanitized source ID and capture safe provenance.
4. Extract explicit process claims separately from interpretation.
5. Link claims to existing workflows, forms, systems, roles, and rules.
6. Classify each claim as NEW, DUPLICATE, EXTENDS, CONFLICTS_WITH, DEPENDS_ON, or SUPERSEDES existing knowledge.
7. Record unresolved questions when evidence is incomplete or ambiguous.
8. Promote only corroborated or user-confirmed knowledge to validated/canonical state.
9. Capture automation opportunities separately from factual process rules.
10. Commit coherent sanitized checkpoints so other agents can resume without rereading every source.
