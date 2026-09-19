---
name: stage-workflow-planner
description: Break a substantial multi-step task into bounded, resumable stages that use the cheapest appropriate capability and define validation, stop conditions, checkpoints, and the next handoff.
---

# Stage Workflow Planner

Use only after `task-complexity-triage` determines that full staged orchestration is justified.

1. Resolve the project and compile only the context needed to plan the workflow.
2. Run `artifact-reuse-check` so existing validated plans/artifacts/checkpoints are reused where possible.
3. Split the work into the smallest coherent stages that can be independently validated and resumed.
4. For each stage record:
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
5. Apply `cheap-route-first` to every stage.
6. For repository stages, prefer `targeted-repository-search` and `change-scope-minimizer`.
7. For bulk collections, include `batch-before-model` preprocessing.
8. For sensitive domains, require `privacy-reduction-pass` before any external model/tool path.
9. Pair every stage with `validate-and-escalate`; use `failed-attempt-reuse` when only part fails.
10. Do not preload future-stage context into the current stage.
11. Make long-running stages restart-safe and idempotent where practical.
12. When only part needs stronger reasoning, isolate and escalate that portion instead of rerunning the entire stage.
13. Add `research-stop-rule` to research-heavy stages.
14. If a stage cannot be safely decomposed further, state why.

The plan is a routing artifact, not a commitment to run every stage in one session.
