from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

from agent_os.browser_bridge import BridgeStore
from agent_os.browser_bridge_server import build_server


def test_bridge_store_deduplicates_and_updates_revisions(tmp_path: Path) -> None:
    store = BridgeStore(tmp_path / "bridge.sqlite")
    base = {
        "event_id": "discord:guild:channel:message",
        "source": "discord",
        "event_type": "message",
        "source_key": "guild:channel:message",
        "occurred_at": "2026-09-24T20:00:00Z",
        "payload": {"text": "first"},
    }

    first = store.ingest([base])
    assert first["durable"] is True
    assert first["stored"] == [base["event_id"]]
    assert first["duplicates"] == []

    duplicate = store.ingest([base])
    assert duplicate["stored"] == []
    assert duplicate["duplicates"] == [base["event_id"]]
    assert duplicate["acknowledged"] == [base["event_id"]]

    edited = dict(base)
    edited["payload"] = {"text": "edited"}
    revision = store.ingest([edited])
    assert revision["updated"] == [base["event_id"]]
    assert revision["acknowledged"] == [base["event_id"]]

    pending = store.pending()
    assert len(pending) == 1
    assert pending[0]["payload"] == {"text": "edited"}

    assert store.mark_ingested([base["event_id"]]) == 1
    assert store.pending() == []
    assert store.stats()["by_state"]["ingested"] == 1


def test_bridge_http_ack_happens_after_durable_store(tmp_path: Path) -> None:
    store = BridgeStore(tmp_path / "bridge.sqlite")
    server, token, _ = build_server(
        "127.0.0.1",
        0,
        store=store,
        token="bridge-test-token",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/api/v1/browser/batch"
    body = json.dumps({
        "events": [{
            "event_id": "journal:test:1",
            "source": "browser-journal",
            "event_type": "view",
            "occurred_at": "2026-09-24T20:00:00Z",
            "payload": {"url": "https://example.com/page"},
        }]
    }).encode("utf-8")

    try:
        unauthenticated = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(unauthenticated, timeout=5)
            assert False, "request without bridge token should fail"
        except urllib.error.HTTPError as exc:
            assert exc.code == 401

        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Agent-OS-Token": token,
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            ack = json.loads(response.read().decode("utf-8"))

        assert ack["durable"] is True
        assert ack["acknowledged"] == ["journal:test:1"]
        assert store.stats()["events"] == 1
        assert store.pending()[0]["event_id"] == "journal:test:1"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
