# Generated adapter — canonical source: policy/CANONICAL_AGENT_POLICY.md

Before work, use `agent.begin_task` (or `agent-os begin-task --project <project>`
with the request on stdin). Consume the envelope and follow project-local policy.
Use `agent.continue_task` for further turns and `agent.finish_task` for structured
decision/evidence/validation summaries; use `agent.abort_task` for failure.
When invoked by an Agent OS gateway with a task envelope, use that task and return
postflight to its owner rather than starting another lifecycle. Load only relevant
context, preserve unrelated work, and keep private source data out of summaries.
Canonical policy: `policy/CANONICAL_AGENT_POLICY.md`. MCP/instruction adapters need
client cooperation; `agent-os run`, `codex`, and `claude` enforce the wrapper lifecycle.
