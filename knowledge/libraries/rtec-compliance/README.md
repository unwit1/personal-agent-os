# RTEC Compliance Knowledge Library

This library models RTEC's compliance obligations, plans, supporting evidence, and historical grant/application requirements that intersect with HR and organizational operations.

## Scope

The source archive supplied on 2026-09-23 contains 864 files across four major collections:

- Affirmative Action Plan (AAP)
- Equal Employment Opportunity / EEO
- Equal Employment Opportunity Plan
- Title VI / Limited English Proficiency (LEP)

The archive also contains historical applicant logs, employee-level EEO rosters, completed affirmative-action data forms, EEOC charge records, reasonable-accommodation case material, state approval letters, training materials, complaint forms, public notices, demographic data, and supporting grant/compliance artifacts.

## Privacy boundary

Person-level applicant, employee, EEO demographic, accommodation, complaint/charge, payroll, or completed voluntary-AA records are not copied into the generalized GitHub corpus.

For those sources GitHub stores only:
- an opaque source ID;
- SHA-256;
- generalized source class/collection;
- file type and size;
- privacy reason;
- provenance relationship to aggregate or procedural records.

Names embedded in restricted filenames are deliberately removed from the archive manifest.

## Safe-source preservation

Safe process/policy/manual sources should be retained in full searchable form when deterministic text extraction is available. Scanned-only PDFs are indexed by hash and page structure and may require staged OCR/visual extraction before a complete searchable mirror is available.

## Authority and versioning

This archive spans roughly two decades. No document is considered current merely because it is present.

Use:
- document revision/effective dates;
- state approval letters;
- later plan versions;
- signed policy statements;
- explicit supersession relationships;
- current user confirmation

before treating a rule as current.

## Important subdomains

- `plans/aap/` — affirmative action / EEO program history and goals
- `plans/title-vi-lep/` — Title VI, LEP, public participation, language access
- `processes/` — complaint, accommodation, monitoring, reporting, grant-compliance workflows
- `grants/` — historical grant application/compliance requirements
- `sources/` — sanitized archive/source manifests and safe searchable mirrors
- `restricted-evidence/` — metadata-only evidence for person-specific records

## Ingestion checkpoint

The initial compliance-archive intake identified:
- 864 files
- 824 unique SHA-256 hashes
- 24 exact-duplicate groups
- 275 files classified as restricted metadata-only
- 589 files safe for general compliance indexing
- 366 files that appear to be substantive compliance documents
- 208 web-export/reference assets

The archive ZIP SHA-256 is:
`9e53d3dd6ca0854172f8e71ac257555143c10720d46a8a27110c93b98d33f446`

The current GitHub connector does not upload arbitrary binary DOC/XLS/PDF files. Repository records therefore preserve hashes, provenance, searchable text where extracted, and structured knowledge. Safe originals should be synchronized later by a local Git-capable workflow. Restricted person-level originals must remain outside the generalized repository.
