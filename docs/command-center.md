# Command Center: one app for every plan, project and agent

Status: design and build spec, 2026-10-14. Operator decisions (this date):
extend Agent OS rather than adopt Paperclip or Hermes; Tailscale for viewing
from other devices; commit and merge the orchestrator work onto main's line
(branch `agent-os/command-center`).

## What it is

One local app, opened as a desktop window (an Edge app window, as the
Executive window already is), that combines:

| Tab | What it shows and does |
|---|---|
| **Today** | The existing Executive window: Work/Personal outstanding items, options, confirms. |
| **Projects** | Every registered project: latest Agent OS handoff, git branch and sync state (ahead/behind/dirty), sensitive flag, local Claude and Codex sessions, Claude cloud sessions. Resume a session in Claude, Codex or the cloud; send a task to a Claude cloud session. |
| **Runs** | The orchestrator control GUI (runs, foreman, model services), embedded. |
| **Chat** | Talk directly to any configured model (Claude, Codex, NanoGPT, OpenRouter free models). Several conversations at once, each optionally tied to a project, so Agent OS context is attached automatically. |
| **Usage** | Every plan's usage windows (`orchestrate headroom --all`): Claude, Codex, NanoGPT, OpenRouter free quota, one-time credits and saved resets with advice, cloud sessions. |

Consequential actions (sending, cloud submits, redeeming) keep the existing
preview-then-Confirm flow. Nothing is redeemed or purchased by the app.

## Why not Paperclip or Hermes

- **Paperclip** (MIT, Node + React, org chart, budgets, Claude Code/Codex
  adapters) is a company layer over agents. It does not read subscription
  usage windows, and its budgets are dollar budgets, not 5-hour/weekly
  plan windows. Borrow: org-chart/goal tracing and per-agent budgets as
  ideas for a later Projects view.
- **Hermes Agent** (MIT, desktop app, gateway, memory, many providers)
  would become a second canonical memory beside Agent OS, and it is not built
  around Claude Code and Codex subscriptions. A community PR adds NanoGPT
  account limits, the same signal headroom.py reads. Borrow: bot/remote
  session ideas; Hermes can also use Agent OS as an MCP server.
- Agent OS already owns the policy gates, the sensitive-data boundary, the
  provider registry and plan headroom; the app is a front door to them.

## Free and prepaid capacity it uses

| Source | Mechanism | Limits |
|---|---|---|
| Claude Code cloud-session credit | `orchestrate cloud submit` (cloud_lane.py) | $100 Pro / $250 Max promo, expires 2026-11-04, spent before plan limits; afterwards cloud sessions count against the plan |
| Saved usage resets | Usage tab advice + link (plan_extras.py) | Claude "Reset for free" (expires 2026-10-22); Claude Code `/limit-reset` (5-hour window only); Codex banked resets via `/usage`. Redeemed in the vendor UI only |
| OpenRouter `:free` models | FreeComputeBroker (`free_routing_enabled`), Chat tab | 1,000 requests/day with $10 lifetime credits (this account), 20/minute |
| NanoGPT subscription | foreman, Chat tab | 60M input units/week, overage blocked |
| ChatGPT unlimited chat | **Not automated.** OpenAI's terms prohibit automated access to the ChatGPT app. The sanctioned route is the reverse: ChatGPT developer-mode connector to Agent OS's MCP server (needs a public HTTPS endpoint; Plus support is inconsistently documented). Later stage. |

Sensitive projects (model_profile.DEFAULT_SENSITIVE_REPOS) never reach a
third-party host, a per-token API, a free model or a cloud session.

## Cross-PC and cross-device

- **Canonical state** stays in Git (Agent OS repository: handoffs,
  checkpoints, project state). The Projects tab shows each repository's
  ahead/behind and offers Sync (pull; push only with a Confirm).
- **Sessions**: Claude cloud sessions and Remote Control are reachable from
  claude.ai and the Claude app on any device; `claude --teleport ID` pulls a
  cloud session onto any PC.
- **This PC**: "Keep this PC awake while work runs" (Windows
  `SetThreadExecutionState`) while orchestrator runs, chats or cloud submits
  are in flight. Tailscale makes the app reachable from your own devices only;
  the server stays bound to loopback and `tailscale serve` proxies to it.

## Build spec (for the implementing agent)

Work in this repository, branch `agent-os/command-center`. Match the
surrounding code: stdlib HTTP servers, no new web framework, no build step,
plain JS in `gui/`. Every new module gets unittest tests under `tests/` with
no network and no real CLI calls (fake runners/openers).

### 1. `src/agent_os/executive/chat_hub.py`

- `providers(registry=None) -> list[dict]`: one entry per enabled provider in
  `agent_os.orchestrator.router.ProviderRegistry` whose adapter is
  `claude_code`, `codex_cli` or `openai_api`, plus a synthetic
  `openrouter-free` entry listing the free broker's catalog slugs
  (`free_dispatch.FreeInputs.load_default().catalog["models"][*]["slug"]`)
  when `secrets://openrouter/default` is configured. Each entry: `id`,
  `label`, `adapter`, `models` (unique values of `models`), `default_model`,
  `sensitive_ok` (`model_profile.sensitive_problem(entry) is None`),
  `headroom` (state from `usage_hub.plans`).
- `send(conversation_id, provider_id, model, text, project=None, home=...)
  -> {"reply", "error", "provider", "model", "usage"}`:
  - Refuse (error, no call) when `project` is sensitive
    (`model_profile.is_sensitive({}, <project path>)` via the project
    registry) and the provider is not `sensitive_ok`.
  - `claude_code`: reuse `executive.window.model_bridge` (Agent OS MCP
    tools, `--resume` per conversation) with `--model <model>`.
  - `codex_cli`: `codex exec --json --skip-git-repo-check -s read-only -m
    <model>` with the Agent OS MCP server configured through `-c
    mcp_servers.agent-os.command=<python>` and `-c
    mcp_servers.agent-os.args=[<repo>/agent.py, "mcp"]`; prompt carries the
    last 10 turns. Parse the final agent message from the JSONL events.
  - `openai_api` and `openrouter-free`: POST `chat/completions` through the
    provider's base URL and `secret_ref` (reuse
    `orchestrator.adapters.http_api` helpers or `endpoints.url`). Prepend a
    system message built from `agent_os.chat.context(query=text,
    project_hint=project, token_budget=1500)` when a project is set. Send
    history (last 20 turns). Never add vendor provider-selection parameters.
  - Persist conversations as JSON under `<window home>/chats/<id>.json`
    (title, provider, model, project, turns with timestamps).
- `conversations(home)`, `conversation(home, id)`, `delete(home, id)`.

### 2. `src/agent_os/executive/projects_view.py`

- `projects() -> list[dict]` from `agent_os.registry.canonical_projects()`:
  `id`, `name`, `path` (resolved local path, None if missing), `sensitive`,
  `git` (`branch`, `ahead`, `behind`, `dirty` count; skip when not a repo),
  `handoff` (latest Agent OS handoff summary for the project:
  `agent_os.chat.latest_project_handoff`), `claude_sessions` (ids and
  modified times from `~/.claude/projects/<cwd-slug>/*.jsonl`; never read
  message text), `codex_sessions` (ids and times from
  `~/.codex/sessions/**/*.jsonl` whose first `session_meta` event has a
  matching `cwd`; read only that first line), `cloud_sessions`
  (`orchestrator.cloud_lane.sessions` filtered by repo path).
- `resume_command(kind, session_id, path)`: `claude --resume ID`, `codex
  resume ID`, or `claude --teleport ID`, run in a new console window
  (`subprocess.Popen([...], cwd=path, creationflags=CREATE_NEW_CONSOLE)`).

### 3. Executive window server and UI

In `src/agent_os/executive/window/server.py` add (token-checked POSTs,
Host-checked as today):

- `GET /api/usage` -> `orchestrator.usage_hub.summary()`.
- `POST /api/extras` `{id, status}` -> `plan_extras.set_status`.
- `POST /api/open-url` `{url}`: `webbrowser.open` only for `https://`
  URLs on `claude.ai`, `chatgpt.com`, `nano-gpt.com`, `openrouter.ai`,
  `github.com`.
- `GET /api/chat/providers`, `GET /api/chat/conversations`,
  `GET /api/chat/conversation?id=`, `POST /api/chat/send`,
  `POST /api/chat/delete`.
- `GET /api/projects`; `POST /api/projects/resume` `{kind, session_id,
  project}`.
- `POST /api/cloud/preview` `{project, task}` -> preflight result plus a
  one-time confirm token (reuse `PendingStore`); `POST /api/confirm` with that
  token runs `cloud_lane.submit`. A cloud submit is consequential.
- `GET /api/config` -> `{"orchestrator_url": ..., "keep_awake": bool,
  "remote_hosts": [...]}`; `POST /api/config` `{keep_awake}`.
- Remote hosts: `build_server(..., remote_hosts=())` adds each
  `host[:port]` to the allowed Host set. Binding stays loopback-only.

`gui/executive.html` / `gui/executive.js` / `gui/style.css`: add a tab bar
(Today, Projects, Runs, Chat, Usage); Today is the current page content.
Runs embeds `orchestrator_url` in an iframe. Chat: conversation list,
provider and model selects (disabled options for providers not
`sensitive_ok` when the chosen project is sensitive, with a tooltip),
project select, message log, input. Usage: a card per plan (state colour,
windows with percent bars and reset times), the free quota, extras with
"Open" and "Mark used", advice lines, cloud sessions with links. Keep the
existing visual style and dark/light handling.

### 4. `agent-os app` (in `src/agent_os/cli.py`)

Starts the orchestrator control GUI server (the same code `agent-os
orchestrate gui` uses, in a background thread, loopback, its own port) and the
Executive window server (passing `orchestrator_url`), opens the Edge app
window, and holds the keep-awake request while
`orchestrator` runs are active or a chat/cloud request is in flight
(`src/agent_os/executive/keep_awake.py`: `ctypes.windll.kernel32.
SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)`; no-op off
Windows; released on exit). Flags: `--no-window`, `--port`,
`--remote-host HOST` (repeatable).

### 5. Docs and checks

Add `agent-os app` to the README command list, and keep
`docs/orchestrator-os/COMMANDS.md` and `tests/test_command_reference.py`
passing. Run `python -m pytest tests -q -p no:cacheprovider` for the new and
touched test files; report results.

## Sources

Claude cloud sessions and `--cloud` (code.claude.com/docs/en/claude-code-on-the-web); routines and the `/fire` API (code.claude.com/docs/en/routines); cloud-credit promotion (ghacks.net, 2026-09-26); Claude saved reset and `/limit-reset` (madrobot.blog 2026-09-23; explainx.ai); Codex banked resets (developersdigest.tech; openclawdc.com); OpenRouter free limits (openrouter.zendesk.com; truefoundry.com); ChatGPT developer mode (zuplo.com; speakeasy.com); Paperclip (github.com/paperclipai/paperclip; betterstack.com); Hermes Agent (releasebot.io/updates/nousresearch/hermes-agent).
