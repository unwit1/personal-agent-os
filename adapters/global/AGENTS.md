# Personal Agent OS routing

For meaningful development work on the user's projects, use the Personal Agent
OS at `C:\Users\HR.RTEC\Projects\Personal Agent` before broad repository reading.
Run its `agent.py begin-task --project <project>` command with the request on stdin,
or call `agent.begin_task` through MCP, then follow
the returned project-local policy, privacy boundary, matched skills, current
state, and validation commands.

Keep context selective. Do not load raw history, all skills, business datasets,
credentials, local databases, spreadsheets, reports, or generated artifacts by
default. Project-local instructions remain authoritative.

Use an existing gateway task envelope rather than creating a duplicate task.
For further turns use `agent.continue_task`. Finish with `agent.finish_task` and
explicit sanitized decisions, evidence, validation and candidate proposals; use
`agent.abort_task` on interruption. The controlled gateway owns these calls when
it supplies the envelope. Canonical policy remains in the Agent OS repository.
Detect new project folders with `python "C:\Users\HR.RTEC\Projects\Personal Agent\agent.py" scan-projects`.
