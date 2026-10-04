from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.connectors import (
    EVENT_SCHEMA,
    _append_connector_event,
    connector_events,
    connector_subscriber_ack,
    connector_subscriber_poll,
)


def valid_connector() -> dict:
    return {
        "id": "google-drive-work",
        "provider": {"id": "google-drive", "name": "Google Drive"},
        "capabilities": ["files.search", "files.read"],
        "scopes": ["drive.readonly"],
        "health": {"status": "unknown", "checked_at": None},
        "privacy_domain": "work",
        "registrations": [{"surface_id": "agent-os-mcp", "state": "desired"}],
        "secret_ref": "keyring:agent-os/google-drive-work",
    }


class ConnectorSubscriberTests(unittest.TestCase):
    def test_connector_subscriber_poll_valid_subscriber_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            records = []
            for i in range(5):
                records.append({
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": f"connector-{i}",
                    "provider_id": "google-drive",
                    "capabilities": [],
                    "surfaces": [],
                    "at": "2026-09-23T12:00:00Z",
                })

            events_path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                result = connector_subscriber_poll("my-subscriber")

            self.assertEqual(result["schema"], "personal-agent/connector-subscriber-poll/v1")
            self.assertEqual(result["subscriber_id"], "my-subscriber")
            self.assertEqual(result["stored_after_seq"], 0)
            self.assertEqual(result["cursor_store_malformed"], False)
            self.assertEqual(result["count"], 5)
            self.assertEqual(result["items"][0]["seq"], 1)

    def test_connector_subscriber_poll_rejects_invalid_subscriber_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            with patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                with self.assertRaises(ValueError):
                    connector_subscriber_poll("INVALID")

    def test_connector_subscriber_poll_respects_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            records = []
            for i in range(100):
                records.append({
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": f"connector-{i}",
                    "provider_id": "google-drive",
                    "capabilities": [],
                    "surfaces": [],
                    "at": "2026-09-23T12:00:00Z",
                })

            events_path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                result = connector_subscriber_poll("my-subscriber", limit=10)

            self.assertEqual(result["count"], 10)
            self.assertEqual(result["limit"], 10)

    def test_connector_subscriber_poll_with_cursor(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            records = []
            for i in range(10):
                records.append({
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": f"connector-{i}",
                    "provider_id": "google-drive",
                    "capabilities": [],
                    "surfaces": [],
                    "at": "2026-09-23T12:00:00Z",
                })

            events_path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records), encoding="utf-8")

            # Create cursor store with subscriber at seq 5
            cursor_store = {
                "schema": "personal-agent/connector-event-cursors/v1",
                "subscribers": {
                    "my-subscriber": {"after_seq": 5}
                }
            }
            cursors_path.write_text(json.dumps(cursor_store), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                result = connector_subscriber_poll("my-subscriber", limit=3)

            self.assertEqual(result["stored_after_seq"], 5)
            self.assertEqual(result["count"], 3)
            # Should get items 6, 7, 8 (after seq 5)
            self.assertEqual([item["seq"] for item in result["items"]], [6, 7, 8])

    def test_connector_subscriber_poll_never_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            records = []
            for i in range(5):
                records.append({
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": f"connector-{i}",
                    "provider_id": "google-drive",
                    "capabilities": [],
                    "surfaces": [],
                    "at": "2026-09-23T12:00:00Z",
                })

            events_path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                connector_subscriber_poll("my-subscriber")

            # Cursor file should NOT be created
            self.assertFalse(cursors_path.exists())

    def test_connector_subscriber_poll_malformed_cursor_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            records = []
            for i in range(5):
                records.append({
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": f"connector-{i}",
                    "provider_id": "google-drive",
                    "capabilities": [],
                    "surfaces": [],
                    "at": "2026-09-23T12:00:00Z",
                })

            events_path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records), encoding="utf-8")
            cursors_path.write_text("{invalid json", encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                result = connector_subscriber_poll("my-subscriber")

            self.assertEqual(result["cursor_store_malformed"], True)
            self.assertEqual(result["stored_after_seq"], 0)

    def test_connector_subscriber_ack_invalid_subscriber_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            with patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path), \
                 patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", Path("/nonexistent")):
                with self.assertRaises(ValueError):
                    connector_subscriber_ack("INVALID", 0)

    def test_connector_subscriber_ack_invalid_seq(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            # Create 5 events (latest_seq = 5)
            records = []
            for i in range(5):
                records.append({
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": f"connector-{i}",
                    "provider_id": "google-drive",
                    "capabilities": [],
                    "surfaces": [],
                    "at": "2026-09-23T12:00:00Z",
                })

            events_path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                # seq > latest_seq should raise
                with self.assertRaises(ValueError):
                    connector_subscriber_ack("my-subscriber", 100)

                # seq < 0 should raise
                with self.assertRaises(ValueError):
                    connector_subscriber_ack("my-subscriber", -1)

                # bool should raise
                with self.assertRaises(ValueError):
                    connector_subscriber_ack("my-subscriber", True)

    def test_connector_subscriber_ack_preview_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            records = []
            for i in range(5):
                records.append({
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": f"connector-{i}",
                    "provider_id": "google-drive",
                    "capabilities": [],
                    "surfaces": [],
                    "at": "2026-09-23T12:00:00Z",
                })

            events_path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                result = connector_subscriber_ack("my-subscriber", 3, confirm_write=False)

            self.assertEqual(result["schema"], "personal-agent/connector-subscriber-ack/v1")
            self.assertEqual(result["subscriber_id"], "my-subscriber")
            self.assertEqual(result["previous_after_seq"], 0)
            self.assertEqual(result["after_seq"], 3)
            self.assertEqual(result["preview"], True)
            self.assertEqual(result["written"], False)
            # Should not create cursor file in preview mode
            self.assertFalse(cursors_path.exists())

    def test_connector_subscriber_ack_write_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            records = []
            for i in range(5):
                records.append({
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": f"connector-{i}",
                    "provider_id": "google-drive",
                    "capabilities": [],
                    "surfaces": [],
                    "at": "2026-09-23T12:00:00Z",
                })

            events_path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                result = connector_subscriber_ack("my-subscriber", 3, confirm_write=True)

            self.assertEqual(result["written"], True)
            self.assertEqual(result["preview"], False)
            self.assertEqual(result["previous_after_seq"], 0)
            self.assertEqual(result["after_seq"], 3)
            self.assertTrue(cursors_path.exists())

            # Verify cursor was written
            cursor_store = json.loads(cursors_path.read_text(encoding="utf-8"))
            self.assertEqual(cursor_store["schema"], "personal-agent/connector-event-cursors/v1")
            self.assertEqual(cursor_store["subscribers"]["my-subscriber"]["after_seq"], 3)

    def test_connector_subscriber_ack_seq_zero_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            records = []
            for i in range(5):
                records.append({
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": f"connector-{i}",
                    "provider_id": "google-drive",
                    "capabilities": [],
                    "surfaces": [],
                    "at": "2026-09-23T12:00:00Z",
                })

            events_path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                result = connector_subscriber_ack("my-subscriber", 0, confirm_write=True)

            self.assertEqual(result["written"], True)
            self.assertEqual(result["after_seq"], 0)

    def test_connector_subscriber_ack_update_existing_cursor(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            records = []
            for i in range(10):
                records.append({
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": f"connector-{i}",
                    "provider_id": "google-drive",
                    "capabilities": [],
                    "surfaces": [],
                    "at": "2026-09-23T12:00:00Z",
                })

            events_path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records), encoding="utf-8")

            # Create initial cursor store
            cursor_store = {
                "schema": "personal-agent/connector-event-cursors/v1",
                "subscribers": {
                    "my-subscriber": {"after_seq": 3}
                }
            }
            cursors_path.write_text(json.dumps(cursor_store), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                result = connector_subscriber_ack("my-subscriber", 7, confirm_write=True)

            self.assertEqual(result["previous_after_seq"], 3)
            self.assertEqual(result["after_seq"], 7)

            # Verify cursor was updated
            updated_store = json.loads(cursors_path.read_text(encoding="utf-8"))
            self.assertEqual(updated_store["subscribers"]["my-subscriber"]["after_seq"], 7)

    def test_connector_subscriber_ack_multiple_subscribers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            records = []
            for i in range(10):
                records.append({
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": f"connector-{i}",
                    "provider_id": "google-drive",
                    "capabilities": [],
                    "surfaces": [],
                    "at": "2026-09-23T12:00:00Z",
                })

            events_path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                # Create first subscriber
                result1 = connector_subscriber_ack("subscriber-1", 3, confirm_write=True)
                self.assertEqual(result1["written"], True)

                # Create second subscriber
                result2 = connector_subscriber_ack("subscriber-2", 5, confirm_write=True)
                self.assertEqual(result2["written"], True)

            # Verify both cursors exist
            cursor_store = json.loads(cursors_path.read_text(encoding="utf-8"))
            self.assertEqual(cursor_store["subscribers"]["subscriber-1"]["after_seq"], 3)
            self.assertEqual(cursor_store["subscribers"]["subscriber-2"]["after_seq"], 5)

    def test_connector_subscriber_ack_idempotent_on_same_seq(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            records = []
            for i in range(5):
                records.append({
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": f"connector-{i}",
                    "provider_id": "google-drive",
                    "capabilities": [],
                    "surfaces": [],
                    "at": "2026-09-23T12:00:00Z",
                })

            events_path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                # First write
                result1 = connector_subscriber_ack("my-subscriber", 3, confirm_write=True)
                self.assertEqual(result1["written"], True)

                # Second write with same seq
                result2 = connector_subscriber_ack("my-subscriber", 3, confirm_write=True)
                self.assertEqual(result2["written"], False)
                self.assertEqual(result2.get("idempotent"), True)

    def test_connector_subscriber_ack_malformed_cursor_store_raises_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            records = []
            for i in range(5):
                records.append({
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": f"connector-{i}",
                    "provider_id": "google-drive",
                    "capabilities": [],
                    "surfaces": [],
                    "at": "2026-09-23T12:00:00Z",
                })

            events_path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records), encoding="utf-8")
            cursors_path.write_text("{invalid json", encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                with self.assertRaises(ValueError) as ctx:
                    connector_subscriber_ack("my-subscriber", 3, confirm_write=True)

                self.assertIn("malformed", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
