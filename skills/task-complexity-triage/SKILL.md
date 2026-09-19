---
name: task-complexity-triage
description: Decide whether a request should stay simple, use a compact plan, or enter a staged workflow so orchestration overhead does not waste usage.
---

# Task Complexity Triage

Use before planning substantial work.

Classify the request into one of three paths:

- SIMPLE: one bounded action, little context, low risk, no meaningful handoff need.
- PLANNED: a few dependent actions that benefit from a compact plan but do not require persistent staged orchestration.
- STAGED: long-running, expensive, multi-model, multi-tool, resumable, or high-context work.

Consider:
- number of distinct actions;
- expected context size;
- need for checkpoints/resume;
- number of tools/providers;
- validation complexity;
- privacy/risk;
- likelihood that different capability classes can handle different parts.

Rules:
- do not create a staged workflow for trivial work;
- prefer a compact plan over full orchestration when it is sufficient;
- route STAGED work to `stage-workflow-planner`;
- record the chosen path and observable reason compactly.

The goal is to save usage, including avoiding unnecessary orchestration itself.
