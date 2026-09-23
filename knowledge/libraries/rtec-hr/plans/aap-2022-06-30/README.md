# RTEC AAP package — workforce snapshot 2022-06-30

This folder models a historical RTEC Affirmative Action Plan / EEO analysis package built around a workforce snapshot dated **June 30, 2022**.

## Temporal interpretation

The source set is historical. The narrative discusses anticipated openings for fiscal year **July 2022 through June 2023**, while several source files were saved or revised in late 2022 or 2023. Therefore:

- `2022-06-30` is the workforce/analysis snapshot date, not necessarily the final binder assembly or submission date;
- file metadata dates do not automatically establish policy effective dates;
- this package must not be treated as current AAP/EEO methodology or current workforce data;
- later AAP/EEO plans should supersede this package for current practice while preserving it for historical comparison.

## Binder structure evidenced by the supplied index/dividers

The package defines these sections:

1. Employment Practices
2. Workforce Analysis
3. Job Group Analysis
4. Personnel Activity Data
5. Placement of Incumbents in Job Groups
6. Comparing Incumbency to Availability
7. Determining Availability
8. Narrative Descriptions / Good Faith Efforts
9. Title VII Investigations
10. Sample Ads and Brochures
11. Commonwealth of Kentucky Certifications

The supplied insert sheets additionally identify **Goals and Timetables from the Previous Program Submission** and **Annual Placement Goals** as part of the analysis sequence.

## Source handling

Safe aggregate analyses, templates, and plan-assembly materials are preserved as complete searchable representations under:

`knowledge/libraries/rtec-hr/sources/aap-2022-06-30/`

Two employee-level roster workbooks are intentionally **not** reproduced in GitHub. They contain direct identifiers and sensitive EEO/personnel fields. Only privacy-safe metadata, hashes, schema descriptions, and aggregate relationships are retained under `restricted-evidence/`.

The supplied 2018 Driver Training & Orientation document is byte-for-byte identical to the source already ingested as `rtec-hr-2018-driver-training-orientation` (SHA-256 `c1c8c564...`), so this plan references the existing canonical source rather than storing a duplicate.

## Important data-quality warning

The 2022 source package contains apparent percentage-scale inconsistencies in some minority/veteran availability and incumbency fields. These are preserved exactly as historical source values and separately flagged for review. No source value is silently corrected.

## Derived records

See:
- `analysis/workforce-and-incumbency.json`
- `analysis/availability-and-placement-goals.json`
- `analysis/personnel-activity.json`
- `analysis/title-vii-and-complaint-process.json`
- `analysis/data-quality-findings.json`
- `process/aap-compilation-workflow.json`
