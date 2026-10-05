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

## Executive Queue and Event Bus

The window's outstanding list is the Executive Queue (roadmap P3). `Registry.outstanding()` converts each provider item once with `agent_os.executive.window_queue.queue_item_from_window_item` into an EXEC-0 queue item (entity kind `task`, source `window:<provider>`, domain `executive-window`; the item's `why` becomes the queue `reason`, a non-negative numeric `score` becomes `priority`) and renders it back with `window_item_from_queue_item`, so the window shows exactly what the providers produced. An item that does not convert is shown unchanged; it is just not queued. `Registry.queue()` returns the same items as queue items.

`builtin.default_registry()` attaches the local Event Bus (`.agent-local/executive/events`, the log `agent-os executive route` reads). Each item is published once as a `task.created` event, deduplicated by provider and item id. The persisted payload holds identifiers only (queue item id, entity id, provider, item id, kind, tab), never titles, reasons or item text, which can contain applicant names or mail subjects. Publishing is best-effort: a failing Event Bus never changes the window.

### Next item and explain

`agent_os.executive.next_action` ranks the Executive Queue by priority (descending), then age_days (descending), then queue item id (ascending).

`agent-os executive next [--tab work|personal]` prints the top queue item with its full explanation.

`agent-os executive explain <item_id> [--tab work|personal]` prints the rank, position (of), priority, age_days, reason, provider, source, kind, and tab for a given queue item id; returns None for unknown ids.

MCP tools `executive_window.next` and `executive_window.explain` return the same data, read-only and local-only. Provider errors are returned in the `errors` field. Hidden items are excluded just as in the outstanding list.

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

Counties with openings replace the "Human review pending" group on the Work tab. Counties come from the Dashboard openings settings; under each county the best applicants are ranked by the existing screening and suggestion logic, limited to a configurable top N. The Dashboard tracks Transit Driver openings as open or closed per group (`transit_driver_groups` in `openings_settings.json`), not as counts: closing an opening closes the group, and a driver quitting or a new opening opens it, saved through the Dashboard's own `openings.save_settings`. Each county lists the applicants awaiting review: AI-reviewed ones first by score, then those without an AI review yet. Clicking an applicant opens a review panel with allowlisted Dashboard fields only (never EEO or self-ID data).

### Applicant decisions

| Decision | Action id |
| --- | --- |
| Review | `applicant.review` |
| Reach out (compose) | `applicant.reach_out` |
| Invite to interview (compose) | `applicant.invite_interview` |
| Email county manager (compose) | `applicant.email_manager` |
| Decline (Confirm) | `applicant.decline` |
| Hold | `applicant.hold` |
| Refresh county group | `county.refresh` |
| Change an opening (preview, then Confirm; refreshes the county group) | `county.opening_change` |

Each is registered in the action registry, so it is both an item option and a model tool.

### Natural-language opening events

Chat messages such as "we closed the opening in X", "a driver quit in Y" or "we have a new opening in Z" map to `county.opening_change` (the chat route invokes it through its alias `openings.event`, which applies to any item). The change goes through gateway methods that call the Dashboard's own openings save functions. The window previews the change and requires Confirm; after Confirm the county's group is refreshed immediately with the latest applicants to review.

## Mail intelligence items and actions

See [mail-intelligence.md](../integrations/mail-intelligence.md) and
[mail.md](../integrations/mail.md).

### Items

- **`mail_filtered`:** one item per tab with counts per primary reason and up to
  25 sample subjects/senders/reasons showing which mail was filtered out, so nothing
  disappears silently.
- **`mail_review`:** borderline (verdict `review`) threads with their reasons,
  shown alongside reply items.
- **`mail_cleanup`:** the organization plan, showing counts per category per
  account and a per-category Confirm button to move mail.

### Actions

- **`mail.organize_inbox`:** builds and caches an organization plan for each
  configured scope; dry-run, no moves. Returns `plan_written`, `generated_at`, per-category
  `counts` and `spam_filtered`; the full plan (sample subjects and target folders)
  is shown by the `mail_cleanup` item.
- **`mail.organize_apply`:** applies the plan to one category. Parameters: `account`,
  `category`. Consequential: preview (dry-run) shows what would move; Confirm
  executes the reversible IMAP moves and journals them with undo commands.

Accounts need `allow_organize` set by the operator (default off, per account) in
`.agent-local/mail/accounts.json` before any organize action can move mail. Nothing
is moved otherwise.

## Per-project Next Action Engine

See [executive-project-actions.md](executive-project-actions.md) for the EXEC-1 per-project Next Action Engine.
