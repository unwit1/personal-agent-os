---
name: regular-chat-router
description: Route substantial project or technical requests through agent.context, load only matching skill bodies when required, and stage evidence-backed durable findings as candidates.
---

# Regular Chat Router

For a substantial request about code, a repository, implementation, debugging,
architecture, agent workflows, skills, or durable project decisions:

1. Call `agent.context` with the user’s request and an explicit project hint when available.
2. Use its compact packet; do not preload every project, skill, or transcript.
3. Load a full matched skill only when its instructions are needed for the task.
4. Test assumptions, constraints, edge cases, evidence, and reusable automation opportunities.
5. Stage durable, evidenced findings through `agent.capture_candidates`.

For ordinary conversation, do not retrieve project context. A candidate is never
canonical memory until an explicit curator workflow validates and promotes it.
