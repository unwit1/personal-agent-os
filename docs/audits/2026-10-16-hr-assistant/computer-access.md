# Audit: computer access and proactive updates in personal-agent-os

Method: read the code, ran `agent.py mcp` (tools/list returned 120 tools; called `connector.list` and `applicant.readiness`), and ran the browser-bridge, executive outbox, event-bus and window tests (71 passed). No repository files were changed.

## Bottom line
It is not a "do anything on my computer" agent today. The Executive window's chat model runs `claude -p --tools "" --allowedTools "mcp__agent-os__*"` (src/agent_os/executive/window/model_bridge.py:12,48-59). That means it has no Bash, Read, Write or Edit tools. It can only use the 120 agent-os MCP tools, and none of them read or write files, run a shell, launch apps or touch Office documents. Proactive updating is also missing: events are recorded, but nothing consumes them on a schedule to update anything.

## Capability matrix
| Capability | Status | Evidence |
|---|---|---|
| Filesystem read/write (general) | missing | No fs tool in MCP tools/list; model_bridge.py:58 `--tools ""` |
| Shell | missing (only in orchestrator coding workers) | claude_code.py:72-77 (acceptEdits, prompts=none, worktree cwd); codex_cli.py:149-155 (workspace-write, no network); workflows.py:360 runs manifest validators only |
| Launch apps | missing | Only window/server.py:410 opens Edge for its own UI |
| Office docs (Word/Excel/Outlook COM) | missing in agent-os | Exists only inside the Dashboard (job-applicant-dashboard/email_sender.py, Outlook COM) |
| Browser control | working (needs Firefox userscript + loopback bridge) | browser_bridge.py:420-447 (11 ops, http/https only); browser_bridge_server.py:21,42-77 (127.0.0.1 + token); mcp_server.py:150-187 |
| Email read (iCloud/EarthLink IMAP, PST) | working | mail/__init__.py:7-8 (read-only); mcp `mail.search/get_thread/sync` |
| Email organize (move/flag) | partial (Window action only) | mail/imap_write.py:5 (command allow-list) |
| Email send | partial | window/transport.py (SMTP + IMAP Sent copy) runs only on a Send click (window/server.py:190-205); `executive.send` goes through Dashboard `gateway.send_now` (executive/applicants.py:691) |
| Gmail / Outlook API / Sheets connectors | planned or missing | connectors/registry.json has one connector (`rtec-applicants`); mail/accounts.py:32 says "SMTP ... future approval-gated send" |
| Google Drive | partial (ledger adapter, no API client) | google_drive.py:1-6 ("The connector owns Drive enumeration"; nothing implements it) |
| Fillout | partial (health metadata only) | rtec_applicants.py:14,917 (`fillout_via_google_bridge`); sync happens in the Dashboard |
| Applicant DB (RTEC) | working read-only, unavailable on this box | mcp `applicant.*`; `applicant.readiness` returned `dashboard_database_present:false` |
| Watch graph | definitions only | watching.py (CRUD only); docs/proactive-watch-graph.md, "Planned worker pipeline" |
| Event bus + router | working, manual | executive/event_bus.py; routing.py:69-85 (`dispatch_pending` only records a disposition; preview by default) |

## Approval gating today
- **Strong (human click):** consequential Executive-window actions return a `confirm_token` and run only through `/api/confirm` (window/server.py:165). MCP deliberately has no confirming tool (mcp_server.py:977).
- **Weak (the model can approve itself):** `browser.execute approved_consequential=true` (mcp_server.py:177, 1277) and `executive.send confirm_send=true` (mcp_server.py:710; 1108-1113). These are boolean arguments the model sets on its own. The real protection is the MCP client's permission prompt, and there is none in the Window's `-p` mode with `--allowedTools mcp__agent-os__*`. The userscript adds a backstop that blocks credential fields and risky click labels (browser/extension/src/content/executor.js:24-26).
- **Config writes:** `confirm_write=true` on connector, routing and subscriber writes. This flag is also self-attested.

## Proactive-update gaps
1. **New applicant to opening pipeline to notify works only inside the Dashboard GUI.** `submission_processed` is recorded at dashboard_core.py:2420 and `check_new_applications` runs on a Tk timer (dashboard_tab.py:933). It stops when the window is closed.
2. **Agent OS only pulls.** `applicant.events` and `event_ack` (rtec_applicants.py:1012,1069) need someone to call them. No poller brings Dashboard `agent_events` into the Executive Event Bus.
3. **No path into rtec-hr.** INGESTER.yaml is batch config, and the `ingester` CLI has no watch or daemon mode. Nothing turns a new applicant, a filled opening or an HR document change into an `ingester ingest` / `reconcile` / `views` run.
4. **No scheduler anywhere.** maintenance.run("scheduled") and workflows need a manual trigger, and no Windows Task Scheduler entry or service is installed. The watch graph has no worker.

## Ranked changes
1. **Fix self-approval first.** Replace the `confirm_send` and `approved_consequential` booleans with a one-time `confirm_token` that only the Window's Confirm click (or a terminal y/N) creates. This reuses window/confirm.py PendingStore.
2. **Add a gated local-actions MCP module (`computer.*`)** instead of enabling raw Bash:
   - Unrestricted (read-only): `fs.read` and `fs.list` under allow-listed roots.
   - Auto-approved, with a journal: `fs.write` limited to new files and scratch or Documents roots, with backup-on-overwrite.
   - Preview + confirm_token: `app.open` (allow-listed executables, `os.startfile` for documents), Office via python-docx/openpyxl, plus delete, move-out-of-root, any `shell.run`, email send, and HR/applicant record edits.
   - Log every call to the access audit (rtec_applicants._audit_access pattern).
3. **Add an `agent-os watch` daemon** (Windows Task Scheduler, every 5 minutes) that:
   - polls `applicant.events`, mail sync and connector events, and publishes them to the Event Bus;
   - runs `routing.dispatch_pending`;
   - calls new consumers that turn events into proposals: refresh opening pipeline counts, queue an `ingester ingest/reconcile/views` for rtec-hr, and post a Window item or toast.
   Read and derived-index updates can run automatically. Record edits become Window items.
4. **Register the real connectors** (Gmail, Drive, Sheets, Fillout) in connectors/registry.json with scopes and credential refs, and implement the Drive enumerator that google_drive.py expects.
5. **Full Claude Code access, if wanted:** run interactive `claude` (not `-p`) in the default permission mode so writes and Bash prompt. Add a PreToolUse hook that sends Bash, Write-outside-roots, and any send or delete tool to the Window confirm queue. Never use `bypassPermissions` or `--permission-prompts none` for the user-facing agent.

## Security recommendation
Always require a human-minted approval token for:
- sending any email or message (SMTP, Outlook, browser send);
- deleting, overwriting or moving files outside scratch;
- editing HR or applicant records (status changes, rtec-hr knowledge, Dashboard DB);
- running shell commands or installs, and sharing or permission changes (Drive);
- payments and credential fields (keep the userscript block).

These can run automatically: reads, search, sync, index and views rebuilds, drafts saved locally, and proposals queued to the Window. HR data stays `work-hr-restricted` and local-only.
