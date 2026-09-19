---
name: reuse-or-automate
description: After a successful workflow, decide whether future repetitions should reuse an artifact, become deterministic code, update/create a skill, or remain ad hoc.
---

# Reuse Or Automate

Use after a repeated or potentially recurring task succeeds.

Choose one disposition:

- REUSE_ARTIFACT: a validated existing output/checkpoint can satisfy future runs.
- AUTOMATE: deterministic code can reliably replace repeated model/tool reasoning.
- UPDATE_SKILL: an existing skill should encode the reusable procedure.
- NEW_SKILL_CANDIDATE: a reusable model/tool workflow exists but needs review.
- KEEP_AD_HOC: recurrence or benefit is too low to justify maintenance.

Consider:
- recurrence;
- determinism;
- validation quality;
- context/model cost;
- privacy;
- maintenance burden;
- failure consequences.

Prefer deterministic automation over a new skill when normal code can solve the problem reliably. Do not silently promote candidates; route durable changes through the normal review/candidate process.
