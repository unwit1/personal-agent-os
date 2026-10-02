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

## Applicant workflow

Full contract: [executive-applicant-workflow.md](executive-applicant-workflow.md). The compose panel is the primary send path for applicant and manager outreach in this workflow; see section 11.1 of the contract for which senders are available.

### Compose and Send panel

Whenever the Executive plans an email (applicant outreach, interview invite, manager email, reply), the window opens an editable compose panel with To, Subject, Body, a From account picker and a Send button. Nothing sends without that Send click. Send calls `POST /api/send`, which uses a `SendTransport`: `SmtpImapTransport` (SMTP submission with the account credential from the keyring, then an IMAP APPEND copy to the Sent folder) or `FakeTransport` in tests. The transport runs in the window server's own process. Any failure is shown clearly as **NOT SENT**. After a successful applicant send the applicant's Dashboard status is updated through the gateway (`record_applicant_sent`, `set_applicant_status`), never raw SQL.

### County openings groups

Counties with openings replace the "Human review pending" group on the Work tab. Counties come from the Dashboard openings settings; under each county the best applicants are ranked by the existing screening and suggestion logic, limited to a configurable top N. Clicking an applicant opens a review panel with allowlisted Dashboard fields only (never EEO or self-ID data).

### Applicant decisions

| Decision | Action id |
| --- | --- |
| Review | `applicant.review` |
| Reach out (compose) | `applicant.reach_out` |
| Invite to interview (compose) | `applicant.invite_interview` |
| Email county manager (compose) | `applicant.email_manager` |
| Decline (Confirm) | `applicant.decline` |
| Hold | `applicant.hold` |
| Refresh a county | `county.refresh` |
| Change an opening | `county.opening_change` |

Each is registered in the action registry, so it is both an item option and a model tool.

### Natural-language opening events

Chat messages such as "we closed the opening in X", "a driver quit in Y" or "we have a new opening in Z" map to `county.opening_change`. The change goes through gateway methods that call the Dashboard's own openings save functions. The window previews the change and requires Confirm; after Confirm the county's group is refreshed immediately with the latest applicants to review.
