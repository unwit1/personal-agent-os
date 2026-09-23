# RTEC State Fiscal Year 2017 transit grant corpus

This directory models three historical RTEC grant-application binders:

- FTA Section 5310 — Enhanced Mobility of Seniors and Individuals with Disabilities
- FTA Section 5311 — Rural Area Formula Program
- FTA Section 5339 — Bus and Bus Facilities

All three are historical State Fiscal Year 2017 application records. Their cover sheets are dated April 1, 2016. They are evidence of RTEC's grant, compliance, operations, procurement, civil-rights, accessibility, planning, safety, and recordkeeping practices during that period and must not be assumed to describe current requirements.

## Scan reality

These are image-only scanned PDFs rather than searchable PDFs.

Actual PDF page counts:
- Section 5310: 305 pages
- Section 5311: 533 pages
- Section 5339: 183 pages
- Total: 1,021 pages

The conversation file viewer exposed only the first 150 rendered pages of each source, so ingestion is being performed in restart-safe page/section batches based on the application checklists plus direct scan inspection.

## Canonical source identities

See `source-manifest.json`.

The original PDFs are retained by source hash and attachment provenance. The current GitHub connector cannot directly copy large binary PDFs from the conversation runtime, so GitHub stores the complete source identity, section/page maps, searchable transcriptions/extractions produced during ingestion, and derived knowledge. Safe binary originals should later be synchronized by the local Git-capable Agent OS workflow.

## Deduplication

The grant binders reuse many of the same standard assurances, certifications, civil-rights documents, safety policies, and other attachments. Repeated material should resolve to a single canonical compliance source whenever identity can be established; grant-specific records should link to it by source/page rather than creating redundant knowledge.

A low-resolution page-similarity pass across all 1,021 pages found extensive repeated material across the binders. This is used only as a discovery aid; canonical deduplication requires text/content verification or a sufficiently strong document identity match.

## Related compliance archive

The uploaded `!Compliance.zip` contains the historical/current working corpus that produced many of the documents referenced in these grants. It is indexed at:

`knowledge/libraries/rtec-hr/compliance/archive-index/`

Particularly relevant historical sources already located include:
- RTEC EEO/Affirmative Action Plan covering the 2015–2018 period;
- Title VI and Limited English Proficient Plan revised September 2016;
- 2016 EEO certification renewal/approval materials;
- ADA complaint process;
- Title VI complaint and investigation forms;
- manager/supervisor EEO training material.

These will be promoted into canonical compliance source records and linked back to the grant pages that require or contain them.
