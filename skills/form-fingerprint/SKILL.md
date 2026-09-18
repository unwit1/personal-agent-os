---
name: form-fingerprint
description: Build a privacy-safe structural fingerprint for an unknown or changed work form without retaining completed values or raw document text.
---

# Form Fingerprint

Keep only page count, generic title tokens, section labels, field labels, boolean layout features, and a deterministic label hash. Strip filled values after delimiters and reject sensitive patterns. Use the fingerprint for matching and candidate review, never as a copy of the submitted form.
