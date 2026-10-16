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

The window's outstanding list is the Executive Queue (roadmap P3). `Registry.outstanding()` converts each provider item once with `agent_os.executive.window_queue.queue_item_from_window_item` into an EXEC-0 queue item (entity kind `task`, source `window:<provider>`, domain `executive-window`; the item's `why` becomes the queue `reason`, a non-negative numeric `score` becomes `priority`) and renders it back with `window_item_from_queue_item`, so the window shows what the providers produced, plus the `rank` and repeated-deferral fields described below. An item that does not convert is shown unchanged and adds no error; it is just not queued and has no `rank`. `Registry.queue()` returns the converted items as queue items, with provider errors in `errors`.

`builtin.default_registry()` attaches the local Event Bus (`.agent-local/executive/events`, the log `agent-os executive route` reads). When a bus is attached, every `outstanding()` or `queue()` call also publishes each converted item as a `task.created` event; the bus deduplicates by provider and item id, so each provider item is logged once. The persisted payload holds identifiers only (queue item id, entity id, provider, item id, kind, tab), never titles, reasons or item text, which can contain applicant names or mail subjects. Each event inherits the sensitivity of its queue entity. Sensitive and secret events are local-only. Shared window item ids from different providers are published separately for each provider entity, with that entity's own sensitivity. Publishing is best-effort: a failing Event Bus never changes the window.

### Repeated deferrals

Snoozing an item (`item.snooze`) publishes a `task.deferred` event to the local Event Bus. Its subject is the item's queue entity id, and its identifiers-only payload contains `entity_id`, `item_id`, `deferred_at`, and `until`; it contains no titles. `Registry.record_deferral` resolves the entity from items collected by earlier outstanding or queue listings, and publishing is best-effort. Item ids are the window's identity (dismiss and snooze state is keyed by them), so if two providers emit the same item id, the deferral is recorded for both entities. The count of `task.deferred` events per entity supplies the queue item's `repeated_deferrals`, which is set only when the count is above 0. Items deferred at least `window_queue.DEFERRAL_THRESHOLD` (3) times show `deferrals: N` and a `why` prefixed with `Deferred N times`.

### Queue status transitions

Dismiss (`item.dismiss`) publishes an identifiers-only `task.cancelled` event. A successful Confirm of a consequential action publishes `task.completed`. Snooze publishes `task.deferred` as described above; its deferral payload is unchanged. Each lifecycle event inherits the originating queue entity's sensitivity; sensitive and secret events are local-only. Persisted payloads remain identifiers-only: deferrals contain `entity_id`, `item_id`, `deferred_at`, and `until`; status events contain `{entity_id, item_id, status, changed_at}`. Event subjects are the queue item's entity id. If providers share a window item id, each provider entity gets its own lifecycle event and the event carries that entity's sensitivity. `window_queue.queue_statuses` gives each queue item its current `status`: the latest event wins, and an expired snooze returns to `queued`. Events are recorded only for items the window has collected in this session (best effort). The window's outstanding list is unchanged.

### Queue item provenance

`window_queue.item_provenance(queue_items, bus, item_id)` and `entity_history(bus, entity_id)` return an identifiers-only timeline of the item's Event Bus events in log order: `task.created`, `task.deferred` (including `until`), and `task.completed` / `task.cancelled` (including `status`). Each event includes `event_id`, `type`, `occurred_at`, `source`, and its persisted route decision (`route`, null until routed). The result also includes `queue_item_id`, `entity_id`, `provider`, `source`, current `status`, and `repeated_deferrals`. Titles and `why` text are never included.

`agent-os executive history <item_id> [--tab work|personal]` and the read-only MCP tool `executive_window.history` (with `item_id` and optional `tab`) expose this history. It complements `executive explain`, which gives the ranking, by answering where an item came from and what has happened to it.

### Next item and explain

`agent_os.executive.next_action` ranks the Executive Queue by priority (descending), then age_days (descending), then queue item id (ascending).

`agent-os executive next [--tab work|personal]` prints `{next, considered, why, errors}`. Selection considers eligible queue items only: items with status `completed`, `cancelled`, or currently `deferred` are skipped. An expired snooze is reduced to `queued` by `window_queue.queue_statuses`, so it is eligible again. `considered` is the number of eligible candidates ranked, and `why` explains the selected candidate (`null` when none are eligible). For example, if a higher-priority item is completed and a lower-priority item remains queued, `next` selects the queued item.

`agent-os executive explain <item_id> [--tab work|personal]` takes a queue item id or a provider (window) item id and prints `{item_id, explanation, errors}`. The explanation has `queue_item_id`, `entity_id`, `item_id`, `provider`, `source`, `kind`, `tab`, `reason`, `priority`, `age_days`, `rank`, `of`, `ranking`, and `provenance`; it is `null` for unknown ids.

MCP tools `executive_window.next` and `executive_window.explain` return the same data, read-only and local-only. Provider errors are returned in the `errors` field. Hidden items are excluded just as in the outstanding list. The eligibility filter applies to next selection only: rank/explain continue to describe the collected queue items, including completed, cancelled, and deferred items; queue status and history retain their existing inspection behavior. Thus `considered` and `why` describe eligible candidates, while rank/explain can still inspect an item excluded from next selection.

### Provenance in explain

`agent-os executive explain <item_id>` / `next` and the MCP tools `executive_window.explain` / `executive_window.next` include a `provenance` object with `provider`, `source`, `entity_id`, `created_event_id` (the identifiers-only `task.created` Event Bus event that produced the item), and `event_ids` (all lifecycle events for the entity, in log order). No payload text is copied. `executive history` / `executive_window.history` still give the full per-event history with route decisions.

### Event routing over MCP

MCP tool `executive_routing.dispatch` routes pending Event Bus events for a consumer (default `router`), with optional event type disposition overrides in `rules`. By default, it previews routes via `routing.preview_pending` without persisting decisions or acknowledging events. With `confirm_write=true`, it behaves like `agent-os executive route`, persisting payload-free route reasons and advancing the consumer cursor. `executive_routing.reason` takes an `event_id` and is read-only; it returns the persisted route decision, matching `agent-os executive route-reason`.

### Project next actions and rank

The `projects` provider (`src/agent_os/executive/window/providers_projects.py`, registered in `builtin.default_registry()`) emits items for active projects from `projects/<id>/state.json`. For each project, it derives next action and flags via the per-project Next Action Engine, then emits one `project_decision` item per decision needed, plus at most one item of each other kind per project. If two registry entries resolve to the same project id, only the first (in registry order) is used, since item ids are built from the project id:

- `project_decision` (score 3): decision needed for the project
- `project_stalled` (score 2): project has not been updated in the configured stale-days threshold
- `project_blocked` (score 2): one item per active project when `blockers` or `waiting_on` contains at least one valid entry (a non-empty string after trimming). Its stable id is `project:<pid>:blocked`, independent of the blocking text. The `why` line has up to two sections: `Blocked by: ...` lists `blockers`, and `Waiting on: ...` lists `waiting_on`; when both are present they are separated by ` | `. It follows the normal tab and rank behavior described below. The item offers **Resume** (`project.resume`) and **Set next action** (`project.set_next_action`). Setting a next action preserves `blockers` and `waiting_on`, so the blocked item remains until those state entries are cleared.
- `project_repeatedly_deferred` (score 2): project items have been snoozed at least 3 times (`project_actions.REPEATED_DEFERRAL_THRESHOLD`), counted per project from identifiers-only `task.deferred` events via `window_queue.project_deferral_counts`. The provider reads the attached Event Bus on a best-effort basis and treats an unavailable log as 0 deferrals; it emits at most one such item per project.
- `project_no_next_action` (score 1): project has no next action or current priority recorded
- `project_vague_next_action` (score 1): the recorded next action is vague (placeholder or short "work on X" phrasing); the `why` gives the suggested concrete next action when one exists

Each item's `why` field contains the reason. Items appear on the work tab by default; a registry entry with `"tab": "personal"` places them on the personal tab instead.

These project details remain provider-local. When a project item is published to the Event Bus, the persisted `task.created` payload contains identifiers only (queue item id, entity id, provider, item id, kind, and tab); it does not include the project's title, `why` text, blocker entries, or `waiting_on` entries.

`Registry.outstanding()` adds a `rank` field to each queued item showing its position in the sorted Executive Queue: `rank = { position: <1-based rank>, of: <total ranked items>, ranking: <algorithm> }`. The window displays this rank next to the `why` context line (as `item-rank`), helping the operator see the item's priority at a glance.

## Safety model and audit

**Consequential actions** (email send, outreach, approvals) never execute on the model's say-so:

1. Model or operator calls `executive_window.run` with action + parameters.
2. The handler runs in **preview mode**, storing the result in `PendingStore`.
3. The preview is returned to the window and model (e.g., "Ready to send email to alice@example.com").
4. Only an explicit operator **Confirm** click in the window executes the action.
5. Result and confirmation are recorded in `audit.jsonl` (append-only, local only).

Non-consequential actions (dismiss, snooze) execute immediately.

**Model access control:** `claude -p --output-format json --mcp-config <file> --strict-mcp-config --allowedTools 'mcp__agent-os__*'` exposes only Agent OS MCP tools; no direct network access.

### Computer access

The chat model has no shell and no general file tools. It reaches the operator's computer only through the `computer.*` MCP tools (`src/agent_os/executive/computer.py`), in three tiers:

| Tier | MCP tool | Runs |
| --- | --- | --- |
| Free (read-only) | `computer.list`, `computer.read`, `computer.search` | immediately |
| Automatic, logged | `computer.write_draft` | immediately; new file under `drafts_root` only, never overwrites (`name-v2.md`, `name-v3.md`, ...) |
| Window Confirm | `computer.write`, `computer.move`, `computer.delete`, `computer.open`, `computer.run` | only after the operator clicks Confirm |

The Confirm-tier tools never act themselves. They run the guard and preview now, park a pending confirmation in `PendingStore` (the same mechanism `executive.approve` and `executive.send` use), and reply `Waiting for you to click Confirm in the command center.` The confirm token stays on disk and is never returned to the model. The window shows each request as a consequential action on a `computer_request` item (`actions_computer.py`: `computer.write_file`, `computer.move_file`, `computer.delete_file`, `computer.open_path`, `computer.run_command`). Previews show:

- `write_file`: a unified diff against the current file. The write is refused if the file changed after the preview. An existing file is copied to `<name>.bak` first.
- `move_file`: the source and target. A move never overwrites, and both paths must lie under the allowed roots.
- `delete_file`: the path. Confirm moves it into the Agent OS trash (default `.agent-local/executive/trash`) with a `.origin.json` sidecar that records the original path. Nothing is hard-deleted.
- `open_path`: the path and the opener (`os.startfile` on Windows, `xdg-open` on Linux).
- `run_command`: the exact argv and cwd. Commands run with no shell, a 120 s timeout, stdin closed, and stdout/stderr each capped at 20,000 characters. The tool refuses command strings, arguments that contain shell metacharacters (`; & | < > $` backtick, newline), shell interpreters (`cmd`, `powershell`, `pwsh`, `bash`, `sh`, `wsl`, ...) and `.bat`/`.cmd` programs. The cwd must be under an allowed root; it defaults to the first root.

**Config:** `~/.agent-os/computer.json` (override the location with `$AGENT_OS_COMPUTER_CONFIG`):

```json
{
  "allowed_roots": ["C:/Users/me/Documents", "C:/Users/me/Desktop"],
  "drafts_root": "C:/path/to/personal-agent-os/.agent-local/executive/drafts",
  "trash_root": "C:/path/to/personal-agent-os/.agent-local/executive/trash"
}
```

Defaults: `allowed_roots` is the user's Documents, Desktop and Downloads folders, where they exist. `drafts_root` is `<repo>/.agent-local/executive/drafts`, and `trash_root` is `<repo>/.agent-local/executive/trash`.

**Path guard:** every path is expanded and resolved (symlinks and `..`) before use. It must lie under an allowed root; relative paths start at the first root. Escapes are refused, whether by `..`, by an absolute path outside the roots, or by a symlink that points outside. Search never follows directory symlinks and skips file symlinks that leave the roots.

**Reads:** `.txt`, `.md`, `.csv` and `.json` are read as text. `.docx`, `.xlsx` and `.pdf` are read when python-docx, openpyxl or pypdf is installed. Files over 2 MB, and files of any other type, return metadata only. Search returns at most 100 results.

**Audit:** every call, including previews and refusals, appends `{ts, op, path, ok}` to `<window home>/computer-audit.jsonl`. Failures add the error type, `run_command` adds the program name, and moves add the target. File contents never go into this audit.

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

## Proactive watcher

`agent-os executive watch --once` runs one sweep; `agent-os executive watch --interval 300` loops.
`tools/install-executive-watcher.ps1` registers a per-user Task Scheduler task (every 5 minutes, no admin
rights, idempotent; `-Uninstall` removes it) so the assistant stays current without the Dashboard open.

Each sweep (`executive/watcher.py: sweep_once`):

- pulls pending Dashboard applicant events (`rtec_applicants.pending_events`), publishes each to the Event Bus
  as a local-only `communication.received` / `context.changed` event, and acknowledges it in the Dashboard
  only after the publish succeeded (a failed publish is retried next sweep; republishing dedups by id);
- runs `executive.routing` over pending events;
- notes RTEC-HR knowledge file changes (mtime/count vs. last sweep; set `RTEC_HR_KNOWLEDGE_DIR` to override the
  registry checkout) as a `context.changed` event with `payload.kind = knowledge_refresh_needed`. Ingestion
  is never run automatically, and the first sweep only records a baseline;
- writes `watcher-state.json` in the window home (last sweep, counts, per-source status, errors).

It never sends and never edits Dashboard records. A missing Dashboard DB or RTEC-HR checkout shows up as
`sources.<name>: unavailable` rather than an error. `watcher.watcher_items()` yields a single `watcher_status`
command-center item, only when the last sweep had errors or new events.

## Per-project Next Action Engine

See [executive-project-actions.md](executive-project-actions.md) for the EXEC-1 per-project Next Action Engine.
