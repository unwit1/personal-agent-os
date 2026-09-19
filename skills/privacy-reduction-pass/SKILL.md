---
name: privacy-reduction-pass
description: Reduce sensitive material to the minimum safe structural metadata needed for an external model/tool, or keep the task local/manual when safe reduction is impossible.
---

# Privacy Reduction Pass

Use before any external model/tool receives material from a sensitive or local-only domain.

1. Identify the minimum information required for the current task.
2. Remove or replace with safe references:
   - names and direct identifiers;
   - credentials/secrets;
   - raw documents/images;
   - raw OCR/full message bodies;
   - employee/applicant/payroll data;
   - private completed field values;
   - unrelated sensitive context.
3. Prefer sanitized structure such as form type, field labels, geometry, counts, generic categories, hashes that cannot expose private content, and abstract failure codes.
4. Re-check project/domain policy before transmission.
5. If the task cannot be represented safely, keep it local/manual instead of weakening the privacy boundary.
6. Record only the sanitized representation and provenance needed for validation.

Privacy reduction is not permission expansion.
