# Shopping in the Executive window

Shopping Agent (`unwit1/agent-os-shopping`) stays a standalone subsystem. It owns wants, product identity,
delivered-cost math, deal scoring, watches, purchase approvals and its own data. Agent OS shows it as the
**Shopping** tab of the Executive window and never re-implements any of that.

## Start it (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File tools\Start-Shopping.ps1          # your real data
powershell -ExecutionPolicy Bypass -File tools\Start-Shopping.ps1 -Demo    # invented stores, separate folder
```

Or double-click `tools\Start Shopping.cmd`. The script expects `agent-os-shopping` and `ingester-engine`
checked out next to this repository. It installs them into a private venv only when missing, turns on the
free keyless sources on first run, prints `agent-shopping doctor`, and opens `#shopping`.
`-InstallWatchTask` adds a Task Scheduler job that runs `watch-due` every 2 hours.

Without the script: `agent-os executive window --tab shopping`.

## How it connects

| Piece | Where | Notes |
|---|---|---|
| Adapter | `src/agent_os/shopping_adapter.py` | Runs `agent-shopping --home H op NAME --args JSON`, one process per call. No Shopping imports. |
| Contract | Shopping `shopping.contract` | Host supports major version 1. Mismatch or missing op → structured error in the UI. |
| Route | `POST /api/shopping` `{op, args, request_id}` | Token header required (no GET route, so no cross-origin reads). `op: "health"` returns connection + doctor. |
| UI | `gui/shopping.js`, `gui/shopping.css` | Overview, Research & Add, Wishlist, Deals, Cart & Checkout, Orders, Diagnostics. Retailer text via `textContent` only; links limited to http(s). |
| Config | env `AGENT_SHOPPING_HOME`, `AGENT_SHOPPING_CMD`, `AGENT_SHOPPING_PROFILE` | Defaults: `~/.agent-os-shopping`; command found via PATH, installed package, or sibling checkout. |

Safety: the adapter has an allowlist (`ALLOWED_OPS`). Approval, purchase execution and candidate promotion are
not on it, and every call uses Shopping's model-safe channel, which refuses them anyway. Reads retry once on
transient failure; writes never retry by themselves, and a repeated `request_id` is answered from cache.
Research is started detached (`detach: true`) so it survives the one-shot adapter process.

## Tests

* `tests/test_shopping_adapter.py`: allowlist, argument stripping, contract negotiation, retries, timeouts,
  duplicate requests, route token, and a real-process round trip when `agent_shopping` is installed.
* `tests/e2e/shopping_ui.e2e.js`: Chromium against the real window, adapter and Shopping CLI (demo stores):
  research → save → watch → deals → price history → checkout handoff → order → restart → diagnostics →
  360 px layout → missing-install error. Run:
  `NODE_PATH=$(npm root -g) node tests/e2e/shopping_ui.e2e.js <path>/agent-os-shopping/shopping.py <outdir>`.

Not built yet: forwarding Shopping's event outbox (`export-events`) into the Agent OS event bus, and a
Shopping card in the Rescue/next-action queue.
