# Personal Agent OS routing

For meaningful development work on the user's projects, use the Personal Agent
OS at `{{AGENT_OS_REPOSITORY}}` before broad repository reading.
Run its `agent.py context` command for the target project and task, then follow
the returned project-local policy, privacy boundary, matched skills, current
state, and validation commands.

Keep context selective. Do not load raw history, all skills, business datasets,
credentials, local databases, spreadsheets, reports, or generated artifacts by
default. Project-local instructions remain authoritative.

After material work, update durable state or a compact handoff when justified.
Detect new project folders with `python "{{AGENT_OS_REPOSITORY}}\agent.py" scan-projects`.
