from __future__ import annotations

import hashlib
import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.browser_bridge import BridgeStore, _payload_hash
from agent_os.browser_bridge_server import build_server
import agent_os.creator_profiles as creator_profiles
import agent_os.watching as watching


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


def test_creator_follow_builds_profile_correlates_discord_and_matches_alias(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(creator_profiles, "CREATOR_DIR", tmp_path / "creators")
    monkeypatch.setattr(
        creator_profiles,
        "CREATOR_INDEX",
        tmp_path / "creators" / "index.json",
    )
    monkeypatch.setattr(watching, "WATCH_DIR", tmp_path / "watching")
    monkeypatch.setattr(
        watching,
        "WATCH_INDEX",
        tmp_path / "watching" / "index.json",
    )

    store = BridgeStore(tmp_path / "bridge.sqlite")
    store.ingest([{
        "event_id": "discord:guild:channel:1",
        "source": "discord",
        "event_type": "message",
        "source_key": "guild:channel:1",
        "occurred_at": "2026-09-25T20:00:00Z",
        "payload": {
            "author": "ModMaker",
            "text": "new release is up",
            "message_url": "https://discord.com/channels/guild/channel/1",
        },
    }])

    server, token, _ = build_server(
        "127.0.0.1",
        0,
        store=store,
        token="bridge-test-token",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    try:
        capture_url = f"http://127.0.0.1:{port}/api/v1/browser/capture"
        capture = {
            "schema_version": "browser-capture-v1",
            "source": "browser",
            "site": "youtube",
            "content_type": "follow_target",
            "source_id": "youtube:creator:@modmaker",
            "title": "ModMaker",
            "author": "ModMaker",
            "url": "https://www.youtube.com/@ModMaker",
            "canonical_url": "https://www.youtube.com/@ModMaker",
            "captured_at": "2026-09-25T21:00:00Z",
            "intent": "follow",
            "metadata": {
                "follow_target_type": "creator",
                "aliases": ["ModMaker", "@modmaker"],
                "route_id": "ModMaker",
                "profile_links": [
                    {"url": "https://github.com/modmaker", "kind": "profile"},
                ],
            },
        }
        request = urllib.request.Request(
            capture_url,
            data=json.dumps(capture).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-Agent-OS-Token": token,
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))

        creator = result["follow"]["creator"]
        assert creator["status"] == "followed"
        assert creator["discord_candidates"][0]["author"] == "ModMaker"
        assert creator["discord_candidates"][0]["message_count"] == 1
        assert any(
            link["canonical_url"] == "https://github.com/modmaker"
            for link in creator["links"]
        )

        status_url = f"http://127.0.0.1:{port}/api/v1/browser/follow/status"
        status_target = {
            "site": "github",
            "source_id": "github:creator:modmaker",
            "title": "modmaker",
            "author": "modmaker",
            "url": "https://github.com/modmaker",
            "metadata": {
                "follow_target_type": "creator",
                "aliases": ["modmaker"],
                "username": "modmaker",
            },
        }
        status_request = urllib.request.Request(
            status_url,
            data=json.dumps(status_target).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-Agent-OS-Token": token,
            },
            method="POST",
        )
        with urllib.request.urlopen(status_request, timeout=5) as response:
            status = json.loads(response.read().decode("utf-8"))

        assert status["followed"] is True
        assert status["matched_by"] == "profile_link"
        assert status["creator_id"] == creator["creator_id"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)



def test_browser_control_session_and_command_round_trip(tmp_path: Path) -> None:
    store = BridgeStore(tmp_path / "bridge.sqlite")
    session = {
        "session_id": "browser-test-session",
        "url": "https://example.com/start",
        "title": "Example",
        "site": "example.com",
        "visibility": "visible",
        "focused": True,
        "user_agent": "pytest",
        "capabilities": {
            "protocol": "agent-os/browser-control/v1",
            "ops": ["inspect", "click", "type"],
        },
    }

    registered = store.register_session(session)
    assert registered == {"ok": True, "session_id": "browser-test-session"}

    sessions = store.list_sessions(active_within_seconds=90)
    assert sessions[0]["session_id"] == "browser-test-session"
    assert sessions[0]["active"] is True
    assert sessions[0]["focused"] is True
    assert sessions[0]["capabilities"]["protocol"] == "agent-os/browser-control/v1"

    queued = store.enqueue_command(
        "browser-test-session",
        [
            {"op": "type", "selector": "input[name=q]", "text": "skyrim mods"},
            {"op": "click", "selector": "button[type=submit]"},
        ],
        issued_by="pytest",
    )
    assert queued["state"] == "queued"

    claimed = store.claim_commands("browser-test-session")
    assert len(claimed) == 1
    assert claimed[0]["command_id"] == queued["command_id"]
    assert claimed[0]["state"] == "running"
    assert store.claim_commands("browser-test-session") == []

    completed = store.complete_command(
        queued["command_id"],
        state="completed",
        result={"actions": [{"typed": True}, {"clicked": True}]},
    )
    assert completed["state"] == "completed"
    assert completed["result"]["actions"][0]["typed"] is True


def test_browser_control_http_poll_and_result(tmp_path: Path) -> None:
    store = BridgeStore(tmp_path / "bridge.sqlite")
    server, token, _ = build_server(
        "127.0.0.1",
        0,
        store=store,
        token="browser-control-test-token",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    try:
        session_url = f"http://127.0.0.1:{port}/api/v1/browser/session"
        session_body = json.dumps({
            "session_id": "browser-http-session",
            "url": "https://example.com/",
            "title": "Example",
            "site": "example.com",
            "visibility": "visible",
            "focused": True,
            "capabilities": {"ops": ["inspect"]},
        }).encode("utf-8")
        request = urllib.request.Request(
            session_url,
            data=session_body,
            headers={
                "Content-Type": "application/json",
                "X-Agent-OS-Token": token,
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            assert json.loads(response.read().decode("utf-8"))["ok"] is True

        queued = store.enqueue_command(
            "browser-http-session",
            [{"op": "inspect"}],
            issued_by="pytest",
        )
        poll_url = (
            f"http://127.0.0.1:{port}/api/v1/browser/commands"
            "?session_id=browser-http-session"
        )
        poll_request = urllib.request.Request(
            poll_url,
            headers={"X-Agent-OS-Token": token},
            method="GET",
        )
        with urllib.request.urlopen(poll_request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["commands"][0]["command_id"] == queued["command_id"]

        result_url = f"http://127.0.0.1:{port}/api/v1/browser/command-result"
        result_request = urllib.request.Request(
            result_url,
            data=json.dumps({
                "command_id": queued["command_id"],
                "state": "approval_required",
                "result": {"risk": "purchase"},
                "error": "approval required before clicking: purchase",
            }).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-Agent-OS-Token": token,
            },
            method="POST",
        )
        with urllib.request.urlopen(result_request, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))

        assert result["state"] == "approval_required"
        assert result["result"]["risk"] == "purchase"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


class PayloadHashTests(unittest.TestCase):
    def test_equals_text_sha256_for_empty_json(self) -> None:
        """_payload_hash('{}') equals text_sha256('{}')."""
        payload = "{}"
        result = _payload_hash(payload)
        expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self.assertEqual(result, expected)
        self.assertEqual(len(result), 64)

    def test_equals_hashlib_for_simple_json(self) -> None:
        """_payload_hash returns full 64-char SHA256 digest."""
        payload = '{"key":"value"}'
        result = _payload_hash(payload)
        expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self.assertEqual(result, expected)
        self.assertEqual(len(result), 64)

    def test_canonical_json_input(self) -> None:
        """_payload_hash with canonical JSON produces correct digest."""
        payload = '{"a":1,"b":2}'
        result = _payload_hash(payload)
        expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self.assertEqual(result, expected)

    def test_non_ascii_payload(self) -> None:
        """_payload_hash handles non-ASCII JSON correctly."""
        payload = '{"text":"世界"}'
        result = _payload_hash(payload)
        expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self.assertEqual(result, expected)

    def test_full_digest_returned(self) -> None:
        """_payload_hash returns the full 64-character digest."""
        payload = '{"test":true}'
        result = _payload_hash(payload)
        self.assertEqual(len(result), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in result))
