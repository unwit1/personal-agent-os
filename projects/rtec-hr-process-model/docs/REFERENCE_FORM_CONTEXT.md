# Cross-project reference form context

This document connects reusable blank/reference forms and templates from other HR projects to the canonical RTEC HR Process Model.

## Canonical catalog

The machine-readable inventory is:

- `knowledge/libraries/rtec-hr/forms/reference-form-catalog.json`

Current imported source sets:

- **HR-GUI:** 72 reference-library records from `assets/reference_fingerprint_manifest.csv`.
- **job-applicant-dashboard:** 3 reusable application/interview/denial-template sources from `Templates/`.
- **RTEC HR Process Model:** 10 form records preserved in the canonical HR corpus, including the visually checked Guardian enrollment reference, five blank orientation/training references discovered in work email, and the unchanged official Kentucky AOC-RU-004 Records Check Request. The five July 15, 2026 orientation documents are preserved with searchable OCR in `knowledge/libraries/rtec-hr/sources/rtec-hr-new-hire-orientation-packet-2026-07-15/`; the government form and its extraction are in `knowledge/libraries/rtec-hr/sources/ky-aoc-ru-004-criminal-record-request/`.

The catalog contains **85 provenance records**, **74 confirmed identity keys**, and **7 sources awaiting identity/deduplication review**. The five orientation documents have possible related HR-GUI catalog entries; full HR-GUI originals are unavailable for content-hash comparison, so these matches remain candidates. The state form is an external reference mentioned in a historical email; its proposed use in an RTEC packet remains unconfirmed. Repeated sources are preserved as multi-source provenance rather than discarded.

The orientation packet's scanned PDFs were visually checked as blank, including signature/name/date fields. The searchable text was created with local OCR and is only a search aid; the unchanged PDFs control. Their effective dates and currentness are unknown. One drug-and-alcohol page is explicitly page 18 of 20 and is preserved only as a fragment. The bus-safety page includes time-sensitive legal/statistical statements that were not independently validated.

The official Kentucky AOC-RU-004 form is preserved exactly as published, labeled Rev. 12-22; its official listing was checked on 2026-09-23. Kentucky Court of Justice guidance says alteration beyond completion is prohibited. The email thread asking about replacing an older packet form does not show approval or implementation. Do not customize it or treat it as an approved RTEC workflow. It contains blank SSN, driver's-license, and date-of-birth fields; completed applicant forms and data stay outside this repository.

## How agents should use these forms

Reference forms are contextual evidence for:

- form names and aliases;
- field/section structure;
- expected page counts and page order when known;
- terminology and document-family recognition;
- likely workflow inputs/outputs;
- scanner/classifier training and deterministic form routing;
- identifying missing process documentation.

A form's existence **does not establish that its language or workflow is current policy**. Currentness, effective dates, supersession, and operational authority must be determined separately from policy/process evidence.

## Source boundaries

### HR-GUI

The HR-GUI reference manifest tracks 72 blank/reference documents across categories including 401(k), benefits, disciplinary, FMLA, interviews, job descriptions, letters, Medicare, new hire, payroll, performance, pre-employment, terminations, training, transfers, and workers' compensation.

The scanner repository contains fingerprints and reference metadata, but most original reference artifacts are maintained outside the committed repository. Therefore the HR Process Model imports their identity, mapping, page/text metadata, and provenance now, while marking the full source artifact as not yet mirrored.

### job-applicant-dashboard

The repository contains reusable source artifacts for:

- `Templates/Application/Job Application Template.docx`
- `Templates/Application/Interview Checklist for Safety Sensitive Applicants.docx`
- `Templates/RTEC_Denial_Letter_Templates.docx`

Backup copies under template backup folders are not treated as separate form identities unless a later hash/content comparison proves they are materially different.

The Job Application Template is especially useful because HR-GUI's audit previously identified Employment Application as a missing/insufficient blank reference.

## Mapping discipline

Use the HR-GUI mapping labels as evidence, not unquestioned truth:

- `verified_label` — strong form-identity evidence;
- `safe_semantic_map` — candidate canonical mapping requiring normal validation;
- `unmapped` — preserve the source identity and proposed name; do not guess a canonical type.

Known suspicious mappings remain review items rather than canonical facts. In particular, the HR-GUI audit flagged `STD Claim Form.pdf` being mapped to `EE Guardian Packet` as needing review.

## Privacy boundary

Only blank/reference forms, templates, sanitized process references, and safe metadata belong in this catalog. Completed employee/applicant forms, identity documents, medical/leave case records, background results, disciplinary case records, compensation data, and other employee-level PII remain outside the canonical GitHub corpus.

## Next ingestion behavior

When a referenced original becomes available:

1. verify it is a safe blank/reference source;
2. compute a content hash;
3. preserve the full source or a lossless repository-safe representation;
4. create a searchable full-text/structured mirror;
5. link it to the catalog entry instead of creating an untracked duplicate;
6. compare versions and preserve supersession/history;
7. extract process claims separately from form identity;
8. keep uncertain process implications at candidate status until validated.
