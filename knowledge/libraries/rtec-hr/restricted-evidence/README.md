# Restricted case evidence

This directory records privacy-safe metadata for live employee/applicant/incident case documents that contributed evidence to the RTEC HR process model.

## Hard boundary

Do not store here:
- raw case documents;
- raw OCR or transcriptions;
- employee/applicant names;
- addresses, identifiers, dates of birth, medical details, compensation or beneficiary details;
- detailed incident narratives;
- PII-bearing source filenames.

A restricted source record may retain only what is needed to support provenance and deduplication:
- stable sanitized source ID;
- generalized document/case class;
- cryptographic hash;
- page count;
- scan/ingestion date;
- privacy classification;
- high-level process evidence that does not identify the person or reproduce case facts.

A single case is never sufficient to establish a universal RTEC policy. Any derived workflow remains a candidate until corroborated by process documents, repeated evidence, or user confirmation.
