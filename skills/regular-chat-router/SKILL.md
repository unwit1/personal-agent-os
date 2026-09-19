---
name: regular-chat-router
description: Route substantial project or technical requests through Agent OS, compile only relevant context, use staged execution for multi-step work, and capture evidence-backed durable findings.
---

# Regular Chat Router

For a substantial request about code, a repository, implementation, debugging,
architecture, agent workflows, skills, or durable project decisions:

1. Run the Agent OS preflight/context route with the user's request and an explicit project hint when available.
2. Use the compact returned packet; do not preload every project, skill, transcript, or historical handoff.
3. Apply `context-budgeter` when the task has broad available context or is part of a staged workflow.
4. If the work is multi-step, expensive, long-running, or naturally separable, use `stage-workflow-planner` before substantial execution.
5. Execute only the current bounded stage unless the workflow explicitly authorizes continuation.
6. Prefer deterministic code, cached results, and approved reusable skills before model reasoning.
7. Load a full matched skill body only when its instructions are needed for the current stage.
8. Test assumptions, constraints, edge cases, evidence, and reusable automation opportunities.
9. At a stage boundary, use `stage-completion-handoff` to validate, checkpoint, stop, and emit the exact next prompt plus capability/model/effort recommendation.
10. When resuming existing work, prefer `resume-from-checkpoint` over rediscovering completed work.
11. Stage durable, evidenced findings through `agent.capture_candidates`.

For ordinary conversation, do not retrieve project context unnecessarily. A candidate is never
canonical memory until an explicit curator workflow validates and promotes it.
