---
name: stage-completion-handoff
description: Finish a bounded workflow stage by validating it, saving a compact checkpoint, and emitting the exact next stage, model/capability recommendation, and ready-to-use next prompt.
---

# Stage Completion Handoff

Use whenever a staged workflow reaches its configured stop condition.

1. Apply `validate-and-escalate` using the stage validator or acceptance check.
2. Record only compact durable state:
   - completed work;
   - validation result;
   - artifacts or references;
   - unresolved items;
   - relevant decisions;
   - checkpoint/state location.
3. Do not carry forward raw transcripts or unrelated project history.
4. Unless the workflow explicitly authorizes continuation, stop after the current stage.
5. Emit:
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
6. If validation fails, preserve successful work, explain the observable failure, and recommend the smallest justified escalation rather than rerunning the entire stage.
7. Never rerun a successful stage with a stronger model merely for reassurance.
8. If no escalation is likely to resolve the blocker, stop and surface the blocker rather than consuming more usage.

The handoff must be sufficient for another supported agent or a later chat to resume without the full prior conversation.
