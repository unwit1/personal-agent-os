---
name: personal-agent-os
description: Route meaningful development work through the user's Personal Agent OS when starting, resuming, or updating one of their local or GitHub projects.
---

# Personal Agent OS

The canonical repository is `C:\Users\HR.RTEC\Projects\Personal Agent` with
private remote `https://github.com/unwit1/personal-agent-os`.

Before meaningful project work, identify the project and compile focused context:

```powershell
python "C:\Users\HR.RTEC\Projects\Personal Agent\agent.py" identify "<project-path>"
python "C:\Users\HR.RTEC\Projects\Personal Agent\agent.py" context <project-id> "<task>"
```

Follow the returned privacy constraints and project-local policy. Never broaden
access to excluded business data merely because a project is registered.

After material work, update durable project state or create a handoff when it
would help the next agent. Run `python agent.py validate`, commit coherent Agent
OS changes, and synchronize the private remote when the active request permits.

Use `python agent.py scan-projects` to detect new or moved local project folders.
Register a new project conservatively: index documentation and code metadata,
not runtime data, secrets, personal records, databases, or generated artifacts.
