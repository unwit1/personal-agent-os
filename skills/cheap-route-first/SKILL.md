---
name: cheap-route-first
description: Choose the cheapest reliable execution path for a task or workflow stage, preferring deterministic code, cache, and approved skills before any model escalation.
---

# Cheap Route First

Use before executing a substantial task or staged workflow step.

Evaluate execution paths in this order:

1. deterministic utility or normal code;
2. valid cached result;
3. approved reusable skill;
4. fast/cheap model capability;
5. balanced model capability;
6. reasoning capability;
7. frontier/high-reasoning capability only when justified.

Skills are instruction-only today, so the caller applies a matched skill; the orchestrator never executes one. A skill becomes orchestrator-executable only by shipping a command that passes the approved-command gate and being declared as a task's deterministic route (docs/orchestrator-os/task-cache-route.md section 9).

Rules:

- Do not use an LLM when deterministic code can satisfy the validator with comparable or better reliability.
- Do not recompute work when a valid cache/checkpoint already exists.
- Do not load a stronger model merely because it is available.
- Use current task risk, ambiguity, validation difficulty, and expected reasoning depth to choose the starting capability.
- Prefer bounded preprocessing to reduce model context before escalation.
- Treat separately billed API use as an alternate execution cost, not a free optimization.
- Record the selected route and observable reason in compact form when practical.
- If the cheapest route fails validation, hand control to `validate-and-escalate` instead of blindly retrying.

The objective is the cheapest path that can reliably pass validation, not the cheapest path regardless of correctness.
