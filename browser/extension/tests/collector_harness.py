"""Real Agent OS bridge on a temp database for the Shopping collector e2e test.

Plays Agent OS Shopping's side: finds the session that advertises
``shopping_collector``, sends it collector commands, and (when agent-os-shopping
is installed) parses the result with Shopping's own parser. One JSON line per step.
"""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

from agent_os.browser_bridge import BridgeStore  # noqa: E402
from agent_os.browser_bridge_server import build_server  # noqa: E402


def emit(**payload) -> None:
    print(json.dumps(payload), flush=True)


def wait(predicate, timeout: float):
    deadline = time.time() + timeout
    while time.time() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.2)
    return None


def finished(store: BridgeStore, command_id: str):
    status = store.command_status(command_id)
    return status if status["state"] not in {"queued", "running"} else None


def collector(store: BridgeStore):
    for session in store.list_sessions():
        caps = session.get("capabilities") or {}
        if isinstance(caps, str):
            caps = json.loads(caps or "{}")
        if caps.get("shopping_collector"):
            return session
    return None


def run(store: BridgeStore, session_id: str, actions: list[dict]):
    command = store.enqueue_command(session_id, actions, issued_by="agent-os-shopping")
    return wait(lambda: finished(store, command["command_id"]), 30)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="aos-collector-e2e-"))
    store = BridgeStore(tmp / "bridge.sqlite")
    server, token, _ = build_server("127.0.0.1", 0, store=store, token="e2e-token")
    threading.Thread(target=server.serve_forever, daemon=True).start()
    emit(event="ready", port=server.server_address[1], token=token)

    session = wait(lambda: collector(store), 30)
    if not session:
        emit(event="fail", reason="no collector session registered")
        return 1
    emit(event="session", session=session, all=[s["session_id"] for s in store.list_sessions()])
    sid = session["session_id"]

    # The exact shape browser_collection.BrowserCollectorProvider.collect_steps sends.
    read = run(store, sid, [
        {"op": "navigate", "url": "https://www.walmart.com/search?q=usb+c+cable"},
        {"op": "wait", "selector": "[data-item-id]", "timeout_ms": 15000},
        {"op": "scroll", "times": 1},
        {"op": "extract", "kind": "jsonld"},
        {"op": "extract", "kind": "tiles", "selector": "[data-item-id]", "limit": 10,
         "fields": {"title": "[data-automation-id=product-title]", "price": "[itemprop=price]@content",
                    "link": "a@href", "image": "img@src"}},
        {"op": "extract", "kind": "groups", "container": ".tile_group", "start": ':has(a[href*="/pd/"] img[alt])',
         "limit": 30, "fields": {"title": 'a[href*="/pd/"] img@alt', "price": '[aria-label^="Actual Price"]@aria-label',
                                 "link": 'a[href*="/pd/"]@href'}},
    ])
    parsed = None
    try:
        from agent_shopping.browser_collection import parse_collection

        result = (read or {}).get("result") or {}
        listings = parse_collection(result.get("steps") or [], page_url=result.get("url") or "", retailer="walmart.com",
                                    provider="browser:walmart.com", observed_at="2026-10-30T12:00:00+00:00")
        parsed = [{"title": l.title, "price": str(l.price) if l.price else None} for l in listings]
    except ImportError:
        parsed = "agent-os-shopping not installed"
    emit(event="read", status=read, parsed=parsed)

    emit(event="refused", status=run(store, sid, [{"op": "navigate", "url": "https://www.walmart.com/"},
                                                 {"op": "click", "selector": "#buy"}]))

    emit(event="go-captcha")                       # the test swaps the page for a human check
    emit(event="captcha", status=run(store, sid, [{"op": "extract", "kind": "jsonld"}]))

    # Paused: Shopping must no longer find a collector, and the tab must not pick up work.
    emit(event="paused-session", collector=collector(store),
         session=next((s for s in store.list_sessions() if s["session_id"] == sid), None))
    queued = store.enqueue_command(sid, [{"op": "extract", "kind": "meta"}], issued_by="agent-os-shopping")
    time.sleep(6)
    emit(event="paused", status=store.command_status(queued["command_id"]))
    server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
