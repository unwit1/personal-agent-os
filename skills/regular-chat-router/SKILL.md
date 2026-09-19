---
name: regular-chat-router
description: Route substantial project or technical requests through Agent OS, minimize unnecessary work/context, use staged execution when justified, and capture evidence-backed durable findings.
---

# Regular Chat Router

For a substantial request about code, a repository, implementation, debugging,
architecture, agent workflows, research, skills, artifacts, or durable project decisions:

1. Run the Agent OS preflight/context route with the user's request and an explicit project hint when available.
2. Apply `task-complexity-triage` so trivial work stays simple and only genuinely multi-step/expensive work becomes staged.
3. Run `artifact-reuse-check` before regenerating prompts, ZIPs, reports, manifests, checkpoints, indexes, or other substantial artifacts.
4. Use the compact returned context packet; apply `context-budgeter` rather than preloading every project, skill, transcript, or historical handoff.
5. For repository work, use `targeted-repository-search` and `change-scope-minimizer` before broad inspection or edits.
6. If triage returns STAGED, use `stage-workflow-planner`. Otherwise use the smallest sufficient plan or direct action.
7. Before execution, apply `cheap-route-first`. For large collections, apply `batch-before-model` before any broad model pass.
8. Apply `privacy-reduction-pass` before external model/tool use when the project/domain contains sensitive or local-only material.
9. Execute only the current bounded stage unless the workflow explicitly authorizes continuation.
10. Load full matched skill bodies only when needed for the current action.
11. Use `research-stop-rule` for research-heavy work to avoid redundant searching after sufficient evidence is obtained.
12. Apply `validate-and-escalate` after execution. If something fails, use `failed-attempt-reuse` so only the unresolved portion is retried/escalated.
13. At a stage boundary, use `stage-completion-handoff`; compact growing state with `checkpoint-compactor` when useful.
14. When resuming, prefer `resume-from-checkpoint` over rediscovering completed work.
15. After a successful repeated workflow, apply `reuse-or-automate` and stage any durable improvement through the normal candidate/review process.
16. Stage durable, evidenced findings through `agent.capture_candidates`.

For ordinary conversation, do not retrieve project context unnecessarily. A candidate is never
canonical memory until an explicit curator workflow validates and promotes it.
