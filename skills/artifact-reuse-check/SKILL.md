---
name: artifact-reuse-check
description: Check whether a usable result, prompt package, ZIP, report, checkpoint, handoff, cache entry, or project artifact already exists before creating or regenerating it.
---

# Artifact Reuse Check

Use before generating a new artifact or repeating substantial project work.

1. Search the current project state, checkpoints, handoffs, canonical Git files, known generated artifacts, and valid caches for an existing result.
2. Prefer exact identity/fingerprint matches first, then semantically equivalent artifacts.
3. Verify freshness, provenance, compatibility, and validation status before reuse.
4. Reuse the existing artifact when it satisfies the current request.
5. If only part is stale, update or regenerate the smallest necessary portion.
6. Do not duplicate ZIPs, prompts, reports, manifests, indexes, or summaries merely because they were created in another session.
7. If no reusable artifact exists, proceed normally and make the new artifact discoverable for future reuse.

Return a compact decision: REUSE, PARTIAL_REUSE, or CREATE_NEW, plus the relevant artifact reference.
