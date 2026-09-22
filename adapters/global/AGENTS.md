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

## Before you edit: check who else is working

Several agents use these repositories. Announce your scope and read the inbox
BEFORE substantial edits, and report what you find to the user so they can see
the conversation:

```powershell
python "{{AGENT_OS_REPOSITORY}}\agent.py" work-inbox --project <project-id>
python "{{AGENT_OS_REPOSITORY}}\agent.py" work-check <project-id> --scope "<path you will edit>"
python "{{AGENT_OS_REPOSITORY}}\agent.py" work-claim <project-id> "<what you are doing>" --agent codex --scope "<path>"
```

If `work-check` or `work-inbox` exits non-zero there is an overlap or a waiting
note. **Tell the user what it says** -- quote the other agent's task and scope
-- then either narrow your scope or reply:

```powershell
python "{{AGENT_OS_REPOSITORY}}\agent.py" work-message <claim-id> "<reply>" --from-agent codex
python "{{AGENT_OS_REPOSITORY}}\agent.py" work-ack <note-id> --agent codex --reply "<answer>"
python "{{AGENT_OS_REPOSITORY}}\agent.py" work-release <claim-id> --note "<what changed>"
```

`agent.py context` also reports `active_work` and `messages_for_you` for the
resolved project. Surface both to the user verbatim rather than acting on them
silently: the user needs to see that agents are talking, not just that you
decided something.

This is advisory. It records and reports; it cannot stop a write. An overlap is
a conversation to have, not a lock to wait on.
