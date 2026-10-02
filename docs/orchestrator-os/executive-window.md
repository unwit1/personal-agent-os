# Agent OS Executive Window

A local desktop window showing all outstanding work across providers. The operator picks actions; a connected Claude model executes them as MCP tools, with consequential actions requiring explicit operator Confirm.

## What the window shows

Two tabs of outstanding items, each with action buttons and a chat panel:

- **Work tab:** applicant needs-action groups and suggestions from the Applicant Executive, plus open approval gates.
- **Personal tab:** email threads needing replies from the locally synced mail index (no network fetches).

Each item has a title, why line, source, and optional buttons for registered actions.

## Schemas

**Item** (returned by providers):
```
{
  id: string,                    # unique from provider
  tab: "work" | "personal",
  title: string,                 # summary for list
  why: string,                   # context line
  source: string,                # where it came from
  due/age: string,               # optional deadline or age
  options: [
    { action_id: string, label: string, consequential: bool }
  ]
}
```

**Action** (registered with `register_action`):
```
{
  id: string,                    # unique action identifier
  label: string,                 # UI button label
  tab: "work" | "personal" | "any",
  handler: fn(item, params, *, confirm: bool),  # receives item context
  consequential: bool            # if True, preview-only until Confirm
}
```

## Providers and actions

Register a new provider — a function that returns a list of items for that tab:

```python
from agent_os.executive.window import registry

registry.register_provider(name="my_provider", fn=my_fetch_function)
```

Providers are called each time the window refreshes. A provider function must return a list of outstanding items locally (no network calls).

Register a new action — appears as a button and as an MCP tool:

```python
registry.register_action(id="my_action", label="...", tab="work", handler=fn, consequential=True)
```

Once registered, the action:
- Appears as a button option on matching items in the UI.
- Is exposed to the model as an MCP tool (`executive_window.run`).

## Safety model and audit

**Consequential actions** (email send, outreach, approvals) never execute on the model's say-so:

1. Model or operator calls `executive_window.run` with action + parameters.
2. The handler runs in **preview mode**, storing the result in `PendingStore`.
3. The preview is returned to the window and model (e.g., "Ready to send email to alice@example.com").
4. Only an explicit operator **Confirm** click in the window executes the action.
5. Result and confirmation are recorded in `audit.jsonl` (append-only, local only).

Non-consequential actions (dismiss, snooze) execute immediately.

**Model access control:** `claude -p --output-format json --mcp-config <file> --strict-mcp-config --allowedTools 'mcp__agent-os__*'` exposes only Agent OS MCP tools; no direct network access.

**Privacy:** Applicant data is allowlisted to `_VIEW_FIELDS = ("applicant_ref", "name", "position", "submitted", "status", "county", "city")`. Forbidden: internal keys, EEO, self-ID, AAP data.

## Server and connection

Python server on `127.0.0.1:8770` (default; configurable with `--port`), using stdlib `http.server` (not Flask). Per-launch session token on all requests. No external network binding.

Claude CLI runs headless in the chat panel, `--resume <token>` for multi-turn conversation. Tool calls return previews; Confirm executes them.

## Launch

```bash
python agent.py executive window
# or
tools/executive-window.cmd
```

Opens Edge `--app` window on the local server.

## Known: email.send

The `email.send` action saves a draft (no outbound SMTP yet); operator opens it in Outlook to review and send. Applicant outreach goes through the Dashboard's mail module.
