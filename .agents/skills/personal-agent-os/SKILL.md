---
name: personal-agent-os
description: Route meaningful development work through the user's Personal Agent OS when starting, resuming, or updating one of their local or GitHub projects, using compact economical execution by default.
---

# Personal Agent OS

The canonical repository is `C:\Users\HR.RTEC\Projects\Personal Agent` with
private remote `https://github.com/unwit1/personal-agent-os`.

Before project work, start the Agent OS lifecycle with the request and an explicit
project hint when available, or consume the envelope supplied by a controlled gateway:

```powershell
python "C:\Users\HR.RTEC\Projects\Personal Agent\agent.py" begin-task --project <project-id> --prompt-file <request-file>
```

Follow returned privacy constraints and project-local policy. Never broaden access
to excluded business data merely because a project is registered. Use
`continue-task` for later turns and structured `finish-task` or `abort-task` at
the end. Do not create a duplicate lifecycle when the gateway owns the task.

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

After material work, return explicit sanitized decisions, evidence, validation,
remaining work, and candidate updates through postflight; the lifecycle creates a
compact handoff when justified. Run `python agent.py validate`, commit coherent
Agent OS changes, and synchronize the private remote when the active request permits.

Use `python agent.py scan-projects` to detect new or moved local project folders.
Register a new project conservatively: index documentation and code metadata,
not runtime data, secrets, personal records, databases, or generated artifacts.
