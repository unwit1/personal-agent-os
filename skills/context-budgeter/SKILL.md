---
name: context-budgeter
description: Minimize model context for a task or workflow stage by selecting only relevant project, profile, memory, skill, and evidence slices within an explicit budget.
---

# Context Budgeter

Use before substantial model work, especially staged workflows.

1. Start from the task/stage goal, not from all available history.
2. Include only context that is necessary to:
   - perform the current stage;
   - obey project/privacy policy;
   - preserve authoritative decisions;
   - validate the result.
3. Prefer compact canonical state, summaries, exact references, and identifiers over raw transcripts or full documents.
4. Exclude:
   - unrelated projects;
   - future-stage material;
   - superseded duplicates;
   - skill bodies that are not needed;
   - raw history already represented by validated checkpoint state.
5. Retrieve more context only when a concrete gap blocks execution or validation.
6. Respect privacy zones before model invocation.
7. When measurable, record the approximate context size and source classes used so later optimization can compare workflows.
8. If the stage exceeds its context budget, split the stage or replace raw material with deterministic preprocessing/retrieval rather than silently expanding context.

The objective is the smallest sufficient context packet, not the smallest packet regardless of correctness.
