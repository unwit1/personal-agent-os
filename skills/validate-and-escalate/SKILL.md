---
name: validate-and-escalate
description: Validate a task or workflow stage and escalate only when observable failure, ambiguity, conflict, or risk justifies a stronger execution path.
---

# Validate And Escalate

Use after an execution attempt or before deciding to rerun work with a stronger capability.

1. Run the stage's explicit validator, tests, schema checks, acceptance criteria, or evidence checks.
2. Return one status:
   - PASS;
   - FAIL;
   - NEEDS_REVIEW.
3. If PASS:
   - accept the result;
   - do not rerun with a stronger model for reassurance;
   - checkpoint and hand off normally.
4. If FAIL or NEEDS_REVIEW:
   - record the observable failure or unresolved ambiguity;
   - identify whether the failure came from missing context, tool failure, deterministic logic, model reasoning, conflicting evidence, or risk policy;
   - fix missing/incorrect inputs before increasing model strength;
   - choose the smallest justified escalation.
5. Escalation may increase one dimension at a time when practical:
   - retrieve a narrowly targeted context slice;
   - invoke a missing skill/tool;
   - retry a failed deterministic operation;
   - move from deterministic/fast to balanced;
   - move from balanced to reasoning;
   - use frontier/high-reasoning only when lower routes cannot satisfy validation.
6. Never discard successful prior stage outputs; preserve them and escalate only the unresolved portion when possible.
7. Record the escalation reason and new capability recommendation for telemetry/handoff.
8. If no stronger route is likely to resolve the issue, surface the blocker instead of consuming more model usage.

Escalation is evidence-driven, not automatic.
