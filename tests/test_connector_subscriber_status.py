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
    connector_subscriber_status,
)


class ConnectorSubscriberStatusTests(unittest.TestCase):
    def test_connector_subscriber_status_missing_cursor_file_gives_count_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            # Create events but no cursors file
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
                result = connector_subscriber_status()

            self.assertEqual(result["schema"], "personal-agent/connector-subscriber-status/v1")
            self.assertEqual(result["read_only"], True)
            self.assertEqual(result["cursor_store_malformed"], False)
            self.assertEqual(result["count"], 0)
            self.assertEqual(result["counts"]["caught_up"], 0)
            self.assertEqual(result["counts"]["behind"], 0)
            self.assertEqual(result["counts"]["cursor_ahead"], 0)
            self.assertEqual(result["subscribers"], [])

    def test_connector_subscriber_status_two_subscribers_different_lags(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            # Create 10 events
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

            # Create cursor store with two subscribers
            cursor_store = {
                "schema": "personal-agent/connector-event-cursors/v1",
                "subscribers": {
                    "subscriber-a": {"after_seq": 10},  # caught up
                    "subscriber-b": {"after_seq": 5},   # behind by 5
                }
            }
            cursors_path.write_text(json.dumps(cursor_store), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                result = connector_subscriber_status()

            self.assertEqual(result["latest_seq"], 10)
            self.assertEqual(result["count"], 2)
            self.assertEqual(result["counts"]["caught_up"], 1)
            self.assertEqual(result["counts"]["behind"], 1)
            self.assertEqual(result["counts"]["cursor_ahead"], 0)

            # Check subscribers are in sorted order
            self.assertEqual(result["subscribers"][0]["subscriber_id"], "subscriber-a")
            self.assertEqual(result["subscribers"][0]["after_seq"], 10)
            self.assertEqual(result["subscribers"][0]["lag"], 0)
            self.assertEqual(result["subscribers"][0]["caught_up"], True)
            self.assertEqual(result["subscribers"][0]["cursor_ahead"], False)

            self.assertEqual(result["subscribers"][1]["subscriber_id"], "subscriber-b")
            self.assertEqual(result["subscribers"][1]["after_seq"], 5)
            self.assertEqual(result["subscribers"][1]["lag"], 5)
            self.assertEqual(result["subscribers"][1]["caught_up"], False)
            self.assertEqual(result["subscribers"][1]["cursor_ahead"], False)

    def test_connector_subscriber_status_cursor_ahead_of_latest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            # Create 5 events
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

            # Create cursor store with subscriber ahead of latest_seq
            cursor_store = {
                "schema": "personal-agent/connector-event-cursors/v1",
                "subscribers": {
                    "subscriber-ahead": {"after_seq": 10},  # ahead of latest_seq
                }
            }
            cursors_path.write_text(json.dumps(cursor_store), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                result = connector_subscriber_status()

            self.assertEqual(result["latest_seq"], 5)
            self.assertEqual(result["count"], 1)
            self.assertEqual(result["counts"]["caught_up"], 0)
            self.assertEqual(result["counts"]["behind"], 0)
            self.assertEqual(result["counts"]["cursor_ahead"], 1)

            subscriber = result["subscribers"][0]
            self.assertEqual(subscriber["after_seq"], 10)
            self.assertEqual(subscriber["lag"], 0)  # max(5 - 10, 0) = 0
            self.assertEqual(subscriber["caught_up"], False)
            self.assertEqual(subscriber["cursor_ahead"], True)

    def test_connector_subscriber_status_malformed_cursor_file(self) -> None:
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
                result = connector_subscriber_status()

            self.assertEqual(result["cursor_store_malformed"], True)
            self.assertEqual(result["count"], 0)
            self.assertEqual(result["subscribers"], [])

    def test_connector_subscriber_status_never_writes_files(self) -> None:
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

            # Record original content and mtime
            original_events_content = events_path.read_text(encoding="utf-8")
            original_mtime = events_path.stat().st_mtime

            # Create cursor store
            cursor_store = {
                "schema": "personal-agent/connector-event-cursors/v1",
                "subscribers": {
                    "subscriber-1": {"after_seq": 3}
                }
            }
            cursors_path.write_text(json.dumps(cursor_store), encoding="utf-8")
            original_cursors_content = cursors_path.read_text(encoding="utf-8")
            original_cursors_mtime = cursors_path.stat().st_mtime

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                connector_subscriber_status()

            # Files should be unchanged
            self.assertEqual(events_path.read_text(encoding="utf-8"), original_events_content)
            self.assertEqual(cursors_path.read_text(encoding="utf-8"), original_cursors_content)
            # mtime should not change (within reasonable time delta, not exact due to filesystem precision)
            self.assertAlmostEqual(events_path.stat().st_mtime, original_mtime, delta=1)
            self.assertAlmostEqual(cursors_path.stat().st_mtime, original_cursors_mtime, delta=1)

    def test_connector_subscriber_status_sorted_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            records = []
            for i in range(3):
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

            # Create cursor store with subscribers in non-alphabetical order
            cursor_store = {
                "schema": "personal-agent/connector-event-cursors/v1",
                "subscribers": {
                    "z-subscriber": {"after_seq": 1},
                    "a-subscriber": {"after_seq": 2},
                    "m-subscriber": {"after_seq": 0},
                }
            }
            cursors_path.write_text(json.dumps(cursor_store), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                result = connector_subscriber_status()

            # Should be in sorted order
            subscriber_ids = [s["subscriber_id"] for s in result["subscribers"]]
            self.assertEqual(subscriber_ids, ["a-subscriber", "m-subscriber", "z-subscriber"])


if __name__ == "__main__":
    unittest.main()
