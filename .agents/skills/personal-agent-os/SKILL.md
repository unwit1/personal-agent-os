---
name: personal-agent-os
description: Route meaningful development work through the user's Personal Agent OS when starting, resuming, or updating one of their local or GitHub projects, using compact economical execution by default.
---

# Personal Agent OS

The canonical repository is `{{AGENT_OS_REPOSITORY}}` with
private remote `https://github.com/unwit1/personal-agent-os`.

Before meaningful project work, identify the project and compile focused context:

```powershell
python "{{AGENT_OS_REPOSITORY}}\agent.py" identify "<project-path>"
python "{{AGENT_OS_REPOSITORY}}\agent.py" context <project-id> "<task>"
```

Follow returned privacy constraints and project-local policy. Never broaden access
to excluded business data merely because a project is registered.

Default economy flow:
1. triage complexity so simple work stays simple;
2. check for reusable artifacts/checkpoints;
3. retrieve only current-task context;
4. use targeted repository search and minimal change scope when coding;
5. stage only genuinely multi-step/expensive work;
6. prefer deterministic/cache/skill execution before model reasoning;
7. batch bulk items before model use;
8. validate and preserve partial success before escalation;
9. compact/checkpoint at stage boundaries;
10. emit the exact next prompt and recommended capability/model/effort;
11. resume later from checkpoint instead of rediscovering completed work;
12. convert repeated successful work into reusable artifacts, automation, or reviewed skills.

After material work, update durable project state or create a compact handoff when
it would help the next agent. Run `python agent.py validate`, commit coherent Agent
OS changes, and synchronize the private remote when the active request permits.

Use `python agent.py scan-projects` to detect new or moved local project folders.
Register a new project conservatively: index documentation and code metadata,
not runtime data, secrets, personal records, databases, or generated artifacts.

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
