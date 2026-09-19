---
name: stage-workflow-planner
description: Break a substantial multi-step task into bounded, resumable stages that use the cheapest appropriate capability and define validation, stop conditions, checkpoints, and the next handoff.
---

# Stage Workflow Planner

Use when a request is too large or heterogeneous to execute efficiently as one continuous model task.

1. Resolve the project and compile only the context needed to plan the workflow.
2. Split the work into the smallest coherent stages that can be independently validated and resumed.
3. For each stage record:
   - goal;
   - required inputs/context;
   - preferred execution path;
   - capability class: deterministic, fast, balanced, reasoning, or frontier;
   - suggested reasoning/effort level;
   - allowed tools;
   - expected outputs/artifacts;
   - validator or acceptance check;
   - stop condition;
   - checkpoint location;
   - next stage.
4. Prefer deterministic code, cache, and approved skills before model calls.
5. Do not assign a stronger capability when a cheaper path can satisfy the validator.
6. Do not preload future-stage context into the current stage.
7. Make every long-running stage restart-safe and idempotent where practical.
8. If a stage cannot be safely decomposed further, state why.

The plan is a routing artifact, not a commitment to run every stage in one session.
