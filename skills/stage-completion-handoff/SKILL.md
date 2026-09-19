---
name: stage-completion-handoff
description: Finish a bounded workflow stage by validating it, saving a compact checkpoint, and emitting the exact next stage, model/capability recommendation, and ready-to-use next prompt.
---

# Stage Completion Handoff

Use whenever a staged workflow reaches its configured stop condition.

1. Apply `validate-and-escalate` using the stage validator or acceptance check.
2. If validation failed partially, apply `failed-attempt-reuse` before considering any rerun.
3. Record only compact durable state:
   - completed work;
   - validation result;
   - artifacts or references;
   - unresolved items;
   - relevant decisions;
   - checkpoint/state location.
4. Apply `checkpoint-compactor` when the accumulated handoff/checkpoint contains repeated or historical detail.
5. Do not carry forward raw transcripts or unrelated project history.
6. Unless the workflow explicitly authorizes continuation, stop after the current stage.
7. Emit:
   - `STAGE_COMPLETE`;
   - completed stage id/name;
   - validation: PASS, FAIL, or NEEDS_REVIEW;
   - artifacts/checkpoint;
   - unresolved items;
   - exact next stage;
   - recommended capability class chosen through `cheap-route-first`;
   - concrete model recommendation only when current availability/configuration is known;
   - recommended reasoning/effort;
   - an exact ready-to-paste next prompt.
8. Never rerun a successful stage with a stronger model merely for reassurance.
9. If no escalation is likely to resolve the blocker, stop and surface it rather than consuming more usage.
10. When the workflow is likely to recur, flag it for `reuse-or-automate`.

The handoff must be sufficient for another supported agent or a later chat to resume without the full prior conversation.
