---
name: checkpoint-compactor
description: Compact growing workflow/project state into a minimal canonical resume packet without losing authoritative decisions, blockers, artifacts, validation state, or provenance.
---

# Checkpoint Compactor

Use when a checkpoint or handoff has accumulated repeated or historical detail.

Preserve:
- workflow/project identity;
- current goal;
- completed validated stages;
- current/next stage;
- authoritative decisions;
- blockers and unresolved items;
- artifact references;
- validation status;
- provenance/version pointers needed to verify or resume.

Remove or replace with references:
- repeated summaries;
- superseded intermediate notes;
- raw transcripts;
- duplicate evidence;
- already-resolved discussion;
- future-stage context not yet needed.

Rules:
- never discard unresolved contradictions or failed validations;
- keep source references sufficient to recover detail later;
- do not rewrite uncertain information as confirmed fact;
- prefer canonical IDs/paths/hashes over copied content;
- produce a resume packet small enough for selective retrieval.

Compaction must reduce context size without making resumption ambiguous.
