---
name: failed-attempt-reuse
description: Preserve successful partial work from a failed attempt and retry only the smallest unresolved portion instead of restarting the whole task or stage.
---

# Failed Attempt Reuse

Use after a validator, test, tool call, or stage attempt fails.

1. Separate successful outputs from failed or uncertain outputs.
2. Preserve validated artifacts, caches, parsed data, test results, and completed subtasks.
3. Identify the smallest failing unit and its observable failure.
4. Reuse all unaffected prior work.
5. Retry or escalate only the failing unit when practical.
6. Invalidate prior work only when a dependency/version change proves it unsafe.
7. Update the checkpoint with:
   - reusable successful work;
   - invalidated work;
   - unresolved failure;
   - next targeted retry/escalation.

Do not restart a full workflow because one component failed.
