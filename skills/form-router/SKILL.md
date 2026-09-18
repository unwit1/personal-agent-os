---
name: form-router
description: Triage a work-related form attachment using a compact sanitized fingerprint and load only a matching form skill when confidence is high.
---

# Form Router

Screen attachments cheaply. Do not fingerprint non-work documents. For work forms, use only template labels and structural features, compare with `forms/registry.json`, and load at most one high-confidence form skill. Unknown or changed forms may create a sanitized local candidate; never retain the source document, completed values, raw OCR, or personal data. Google is not a form-intake storage or fallback path.
