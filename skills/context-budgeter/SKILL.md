---
name: context-budgeter
description: Minimize model context for a task or workflow stage by selecting only relevant project, profile, memory, skill, and evidence slices within an explicit budget.
---

# Context Budgeter

Use before substantial model work, especially staged workflows.

1. Start from the task/stage goal, not from all available history.
2. Reuse valid checkpoint/artifact summaries instead of raw source history when possible.
3. Include only context necessary to perform the current stage, obey privacy/project policy, preserve authoritative decisions, and validate the result.
4. Prefer compact canonical state, summaries, exact references, IDs, and targeted repository/search excerpts over raw transcripts or full documents.
5. Exclude unrelated projects, future-stage material, superseded duplicates, unnecessary skill bodies, and history already represented by validated checkpoint state.
6. Retrieve more context only when a concrete gap blocks execution or validation.
7. Apply `privacy-reduction-pass` before external model/tool use for sensitive domains.
8. When measurable, record approximate context size and source classes used.
9. If the stage exceeds its context budget, split it, preprocess/batch deterministically, or replace raw material with retrieval references rather than silently expanding context.

The objective is the smallest sufficient context packet, not the smallest packet regardless of correctness.
