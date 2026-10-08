"""Real Agent OS bridge on a temp database for the extension e2e test.

Prints one JSON line per step on stdout. Never touches the user's bridge DB
or token.
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


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="aos-bridge-e2e-"))
    store = BridgeStore(tmp / "bridge.sqlite")
    server, token, _ = build_server("127.0.0.1", 0, store=store, token="e2e-token")
    threading.Thread(target=server.serve_forever, daemon=True).start()
    emit(event="ready", port=server.server_address[1], token=token)

    sessions = wait(lambda: store.list_sessions(), 20)
    if not sessions:
        emit(event="fail", reason="no session registered")
        return 1
    session = sessions[0]
    emit(event="session", session=session)

    first = store.enqueue_command(session["session_id"], [
        {"op": "inspect"},
        {"op": "type", "selector": "#q", "text": "skyrim"},
        {"op": "click", "selector": "#buy"},
    ], issued_by="e2e")
    emit(event="first", status=wait(lambda: finished(store, first["command_id"]), 20))

    second = store.enqueue_command(session["session_id"], [
        {"op": "click", "selector": "#buy"},
    ], issued_by="e2e", approved_consequential=True)
    emit(event="second", status=wait(lambda: finished(store, second["command_id"]), 20))

    third = store.enqueue_command(session["session_id"], [
        {"op": "type", "selector": "#pw", "text": "not-a-real-password"},
    ], issued_by="e2e", approved_consequential=True)
    emit(event="third", status=wait(lambda: finished(store, third["command_id"]), 20))

    fourth = store.enqueue_command(session["session_id"], [{"op": "close_tab"}], issued_by="e2e")
    emit(event="fourth", status=wait(lambda: finished(store, fourth["command_id"]), 20))

    def snapshot():
        rows = store.pending(limit=50) if hasattr(store, "pending") else []
        return [r for r in rows if r.get("source") == "content-filters"]

    emit(event="filters", rows=wait(snapshot, 20) or [])
    server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
