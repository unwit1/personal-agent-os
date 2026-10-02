# Agent OS Executive Window

**Status:** Implementation guide for the Executive window component (2026-10).

The Executive window is a local desktop application that aggregates outstanding work across Agent OS providers, allows the operator to pick actions, and connects to Claude via the Claude Code CLI (in headless mode) to execute those actions as MCP tools.

## What the window shows

The window displays a Web UI served by Python on `127.0.0.1` only, launched as an Edge `--app` window by a desktop launcher. It has two tabs:

- **Work tab:** Outstanding applicant actions from the Executive module (needs-action groups from `executive.needs_action()` with their suggestions from `executive.suggestions()`), plus open approval gates from the orchestrator.
- **Personal tab:** Email threads that look like they need a reply, from the locally synced mail index (no network fetches in the window).

Beside the tabs is a **chat panel** where the model converses with the operator, calling registered actions as tools.

## Item and action schemas

**Outstanding Item** (from a provider):

```json
{
  "id": "string",                          // Unique ID from the provider
  "tab": "work|personal",                  // Where it appears
  "title": "string",                       // Summary for the item list
  "why": "string",                         // Why it matters
  "source": "string",                      // Which provider/system
  "due": "ISO 8601 or null",              // Deadline if any
  "age_days": "integer or null",          // How long it's been outstanding
  "options": [
    {
      "action_id": "string",               // Registered action ID
      "label": "string",                   // Button text in the UI
      "consequential": true|false          // Requires Confirm to execute
    }
  ]
}
```

**Action** (in the registry):

```json
{
  "id": "string",                          // Unique action identifier
  "label": "string",                       // UI and model-visible label
  "tab": "work|personal|any",              // Which tab(s) this applies to
  "handler": "python_function",            // Callable that executes the action
  "consequential": true|false              // If true, model can only return a preview; Confirm required
}
```

## Providers and actions

### Adding a provider

A **provider** is a source of outstanding items. Register a new provider with:

```python
from agent_os.executive.window import registry

registry.register_provider(
    name="my_provider",
    tab="work",  # or "personal"
    handler=my_fetch_function
)
```

`my_fetch_function` should return a list of Item dicts. Providers are called each time the window refreshes. They must:
- Run locally (no network calls).
- Return items quickly (<1s).
- Never trigger model calls or AI reviews.

Initial providers: Applicant Executive needs-action groups + suggestions, orchestrator approval gates, mail thread candidates.

### Adding an action

Register a new action with:

```python
from agent_os.executive.window import registry

registry.register_action(
    id="my_action",
    label="My Action Label",
    tab="work",
    handler=my_action_handler,
    consequential=False  # Set True if sending mail, records, approvals
)
```

Once registered, the action:
- Appears as a button option on relevant items in the UI.
- Is exposed to the model as an MCP tool (`executive_window.run`), discoverable via the MCP server.
- Can be triggered by the operator clicking its button or by the model calling the tool.

## Safety model

### Consequential actions

**Consequential** actions (sending email, recording applicant outreach, approving orchestrator gates) never run on the model's decision alone. The flow is:

1. Operator or model requests the action via a button click or tool call.
2. The `executive_window.run` MCP tool **executes the handler in preview mode**, storing the result in `PendingStore`.
3. The preview (e.g., "Ready to send email to X with subject Y") is returned to the window and model.
4. Only if the operator clicks the **Confirm** button in the window is the preview executed as a final action.
5. The action result and confirmation are recorded in `audit.jsonl`.

Non-consequential actions (dismissing an item, snoozing) run immediately without confirmation.

### Model access control

The Claude model runs headless via `claude -p --resume <session-token>` with:

- Only the `mcp__agent-os__*` tools exposed (filtered allowlist in the MCP server).
- No direct network access; all calls are through Agent OS MCP.
- No access to applicant internal keys, EEO data, self-ID fields, or other restricted columns.

### Privacy rules for applicant data

The Applicant Executive projects applicants onto an allowlist:

```python
_VIEW_FIELDS = ("applicant_ref", "name", "position", "submitted", "status", "county", "city")
```

- `applicant_ref`: opaque reference only (never Dashboard's internal key).
- `name`, `position`, `status`, `county`, `city` only when needed for outreach content.
- **Forbidden in all Executive output, outbox, audit, and prompts:** `aa_pdf_path`, race/ethnicity, sex/gender self-ID, veteran or disability self-ID, any other AAP data.

Restricted fields must be stripped even if present in Dashboard responses.

## Connected model and CLI invocation

The window launches the Claude Code CLI in headless mode, maintaining one `--resume` session per window conversation:

```bash
claude -p --resume <session-token> <<EOF
{
  "messages": [ ... ],
  "tools": [ ... MCP schema for executive_window.run and other allowed tools ... ]
}
EOF
```

- `claude -p` outputs JSON to stdout.
- `--resume <session-token>` maintains conversation context (from `profile/.claude-sessions/<session-token>`).
- The MCP bridge (`mcp_server.py`) registers `executive_window.run` as a tool.
- All model tool calls are translated to `PendingStore` entries; the window renders them as action previews.

## Server binding and loopback security

The Python server binds to `127.0.0.1:<random>` only (no external network):

```python
from flask import Flask
app = Flask(__name__)
app.run(host="127.0.0.1", port=<random>)
```

The session token (`profile/.claude-sessions/<session-token>.json`) is:
- Generated per window launch.
- Stored locally (never sent externally).
- Used to maintain model context across multiple tool calls.
- Deleted when the window closes.

## Launch methods

### Via Python CLI

```bash
python agent.py executive window
```

This starts the Flask server on `127.0.0.1`, prints the URL and session token, and opens an Edge app window.

### Via desktop launcher

```cmd
@echo off
cd C:\Users\HR.RTEC\GitHub\personal-agent-os
python agent.py executive window
```

Store as `tools/executive-window.cmd` and pin to the desktop for single-click launch.

## Audit logging

All consequential action confirmations are recorded in `audit.jsonl` (gitignored, local only):

```json
{
  "timestamp": "2026-10-02T12:34:56Z",
  "action_id": "email.send",
  "item_id": "thread-123",
  "operator_confirmed": true,
  "preview": { ... },
  "result": { ... }
}
```

Audit entries are appended only (never modified or deleted). They provide a complete record of operator decisions and action outcomes.

## Known limitation: email.send

The `email.send` action (composing and sending a new email) currently **saves a draft instead of sending**:

- `email.send` renders the draft to `.agent-local/executive/drafts/`.
- The operator opens the draft in Outlook to review and send.
- No outbound SMTP transport is integrated yet.

This is a placeholder pending mail transport architecture. Applicant outreach emails use the Dashboard's `email_sender.send_now()` and go through Outlook natively.
