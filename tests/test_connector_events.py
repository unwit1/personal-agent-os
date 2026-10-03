from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.connectors import (
    EVENT_SCHEMA,
    _append_connector_event,
    connector_events,
    register_connector,
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


class ConnectorEventTests(unittest.TestCase):
    def test_append_event_creates_parent_directory_and_appends_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "nested" / "connector-events.jsonl"
            self.assertFalse(events_path.parent.exists())

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                connector = valid_connector()
                result = _append_connector_event("connector.added", connector)

            self.assertTrue(result)
            self.assertTrue(events_path.exists())

            line = events_path.read_text(encoding="utf-8").strip()
            record = json.loads(line)
            self.assertEqual(record["schema"], EVENT_SCHEMA)
            self.assertEqual(record["event"], "connector.added")
            self.assertEqual(record["connector_id"], "google-drive-work")
            self.assertEqual(record["provider_id"], "google-drive")
            self.assertEqual(set(record["capabilities"]), {"files.read", "files.search"})
            self.assertEqual(record["surfaces"], ["agent-os-mcp"])
            self.assertTrue(record["at"].endswith("Z"))

    def test_append_event_never_includes_secrets_scopes_or_privacy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                connector = valid_connector()
                connector["id"] = "google-drive-personal"
                connector["privacy_domain"] = "personnel"
                _append_connector_event("connector.added", connector)

            line = events_path.read_text(encoding="utf-8").strip()
            content = line
            self.assertNotIn("secret_ref", content)
            self.assertNotIn("scopes", content)
            self.assertNotIn("privacy_domain", content)
            self.assertNotIn("drive.readonly", content)
            self.assertNotIn("personnel", content)
            self.assertNotIn("keyring:", content)

    def test_append_event_returns_false_on_oserror(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use a path inside a file (not a directory)
            events_path = Path(tmpdir) / "file.txt"
            events_path.write_text("content")
            bad_path = events_path / "nested"

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", bad_path):
                connector = valid_connector()
                result = _append_connector_event("connector.added", connector)

            self.assertFalse(result)

    def test_connector_events_returns_empty_when_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                result = connector_events()

            self.assertEqual(result["schema"], "personal-agent/connector-events/v1")
            self.assertEqual(result["count"], 0)
            self.assertEqual(result["items"], [])
            self.assertEqual(result["malformed"], 0)

    def test_connector_events_rejects_invalid_limit(self) -> None:
        for limit in ("50", True, 0, 501, -1):
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    connector_events(limit=limit)

    def test_connector_events_accepts_valid_limits(self) -> None:
        for limit in (1, 50, 500):
            with self.subTest(limit=limit):
                # Should not raise
                with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", Path("/nonexistent")):
                    result = connector_events(limit=limit)
                self.assertEqual(result["limit"], limit)

    def test_connector_events_rejects_invalid_connector_id(self) -> None:
        with self.assertRaises(ValueError):
            connector_events(connector_id="INVALID")

    def test_connector_events_filters_by_connector_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

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

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                all_result = connector_events()
                filtered_result = connector_events(connector_id="connector-1")

            self.assertEqual(all_result["count"], 3)
            self.assertEqual(filtered_result["count"], 1)
            self.assertEqual(filtered_result["items"][0]["connector_id"], "connector-1")
            self.assertEqual(filtered_result["connector_filter"], "connector-1")

    def test_connector_events_respects_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

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

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                result = connector_events(limit=10)

            self.assertEqual(result["count"], 10)
            self.assertEqual(result["limit"], 10)
            # Should be the last 10 items
            self.assertEqual(result["items"][0]["connector_id"], "connector-90")
            self.assertEqual(result["items"][-1]["connector_id"], "connector-99")

    def test_connector_events_skips_malformed_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

            content = "\n".join([
                json.dumps({"schema": EVENT_SCHEMA, "event": "connector.added", "connector_id": "valid-1", "provider_id": "p1", "capabilities": [], "surfaces": [], "at": "2026-09-23T12:00:00Z"}, sort_keys=True),
                "{invalid json",
                "",
                json.dumps({"schema": "wrong-schema", "connector_id": "valid-2"}, sort_keys=True),
                "not a dict at all",
                json.dumps({"schema": EVENT_SCHEMA, "event": "connector.added", "connector_id": "valid-3", "provider_id": "p3", "capabilities": [], "surfaces": [], "at": "2026-09-23T12:00:00Z"}, sort_keys=True),
            ])
            events_path.write_text(content, encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                result = connector_events()

            self.assertEqual(result["count"], 2)
            self.assertEqual(result["malformed"], 4)
            self.assertEqual(result["items"][0]["connector_id"], "valid-1")
            self.assertEqual(result["items"][1]["connector_id"], "valid-3")

    def test_register_connector_appends_event_on_add(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors.REGISTRY_PATH", Path(tmpdir) / "registry.json"), \
                 patch("agent_os.connectors.load_connector_registry") as mock_load:

                mock_load.return_value = {"schema": "personal-agent/connector-registry/v1", "version": 1, "connectors": []}

                connector = valid_connector()
                result = register_connector(connector, confirm_write=True)

            self.assertTrue(result["written"])
            self.assertTrue(result["event_recorded"])

            line = events_path.read_text(encoding="utf-8").strip()
            record = json.loads(line)
            self.assertEqual(record["event"], "connector.added")

    def test_register_connector_appends_event_on_update(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors.REGISTRY_PATH", Path(tmpdir) / "registry.json"), \
                 patch("agent_os.connectors.load_connector_registry") as mock_load:

                connector = valid_connector()
                mock_load.return_value = {"schema": "personal-agent/connector-registry/v1", "version": 1, "connectors": [connector]}

                updated = valid_connector()
                updated["scopes"] = ["drive.readonly", "drive.metadata"]

                result = register_connector(updated, confirm_write=True, replace_existing=True)

            self.assertTrue(result["written"])
            self.assertTrue(result["replaced"])
            self.assertTrue(result["event_recorded"])

            line = events_path.read_text(encoding="utf-8").strip()
            record = json.loads(line)
            self.assertEqual(record["event"], "connector.updated")

    def test_register_connector_reports_failed_event_append(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors.REGISTRY_PATH", Path(tmpdir) / "registry.json"), \
                 patch("agent_os.connectors.load_connector_registry") as mock_load, \
                 patch("agent_os.connectors._append_connector_event", return_value=False):

                mock_load.return_value = {"schema": "personal-agent/connector-registry/v1", "version": 1, "connectors": []}
                result = register_connector(valid_connector(), confirm_write=True)

            self.assertTrue(result["written"])
            self.assertFalse(result["event_recorded"])
            self.assertFalse(events_path.exists())

    def test_connector_events_projects_documented_fields_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"
            record = {
                "schema": EVENT_SCHEMA,
                "event": "connector.added",
                "connector_id": "x",
                "provider_id": "p",
                "capabilities": [],
                "surfaces": [],
                "at": "2026-01-01T00:00:00Z",
                "secret_ref": "keyring:leak",
            }
            events_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                result = connector_events()

            self.assertNotIn("secret_ref", result["items"][0])
            self.assertEqual(result["items"][0]["connector_id"], "x")
            self.assertIn("seq", result["items"][0])
            self.assertEqual(result["items"][0]["seq"], 1)

    def test_register_connector_no_event_on_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                connector = valid_connector()
                result = register_connector(connector, confirm_write=False)

            self.assertFalse(result["written"])
            self.assertFalse(events_path.exists())

    def test_register_connector_no_event_on_idempotent_no_op(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path), \
                 patch("agent_os.connectors.REGISTRY_PATH", Path(tmpdir) / "registry.json"), \
                 patch("agent_os.connectors.load_connector_registry") as mock_load:

                connector = valid_connector()
                mock_load.return_value = {"schema": "personal-agent/connector-registry/v1", "version": 1, "connectors": [connector]}

                result = register_connector(connector, confirm_write=True)

            self.assertFalse(result["written"])
            self.assertTrue(result["idempotent"])
            self.assertFalse(events_path.exists())

    def test_event_record_includes_sorted_capabilities_and_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                connector = valid_connector()
                connector["capabilities"] = ["z-capability", "a-capability", "m-capability"]
                connector["registrations"] = [
                    {"surface_id": "zulu", "state": "desired"},
                    {"surface_id": "alpha", "state": "desired"},
                    {"surface_id": "mike", "state": "desired"},
                ]
                _append_connector_event("connector.added", connector)

            line = events_path.read_text(encoding="utf-8").strip()
            record = json.loads(line)
            self.assertEqual(record["capabilities"], ["a-capability", "m-capability", "z-capability"])
            self.assertEqual(record["surfaces"], ["alpha", "mike", "zulu"])

    def test_event_timestamp_is_iso8601_with_z(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                connector = valid_connector()
                _append_connector_event("connector.added", connector)

            line = events_path.read_text(encoding="utf-8").strip()
            record = json.loads(line)

            self.assertTrue(record["at"].endswith("Z"))
            # Should be parseable as ISO 8601
            parsed = datetime.fromisoformat(record["at"].replace("Z", "+00:00"))
            self.assertIsNotNone(parsed)

    def test_append_event_appends_to_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                connector1 = valid_connector()
                connector1["id"] = "connector-1"
                _append_connector_event("connector.added", connector1)

                connector2 = valid_connector()
                connector2["id"] = "connector-2"
                _append_connector_event("connector.updated", connector2)

            lines = events_path.read_text(encoding="utf-8").strip().split("\n")
            self.assertEqual(len(lines), 2)
            record1 = json.loads(lines[0])
            record2 = json.loads(lines[1])
            self.assertEqual(record1["connector_id"], "connector-1")
            self.assertEqual(record1["event"], "connector.added")
            self.assertEqual(record2["connector_id"], "connector-2")
            self.assertEqual(record2["event"], "connector.updated")

    def test_connector_events_rejects_invalid_after_seq(self) -> None:
        for after_seq in ("0", True, -1):
            with self.subTest(after_seq=after_seq):
                with self.assertRaises(ValueError):
                    connector_events(after_seq=after_seq)

    def test_connector_events_accepts_valid_after_seq(self) -> None:
        for after_seq in (None, 0, 1, 100):
            with self.subTest(after_seq=after_seq):
                with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", Path("/nonexistent")):
                    result = connector_events(after_seq=after_seq)
                self.assertEqual(result["after_seq"], after_seq)

    def test_connector_events_adds_seq_to_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

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

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                result = connector_events()

            for i, item in enumerate(result["items"]):
                self.assertIn("seq", item)
                self.assertEqual(item["seq"], i + 1)

    def test_connector_events_cursor_forward_pagination(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

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

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                # First page (backward compat: last 3 items)
                result1 = connector_events(limit=3, after_seq=None)
                self.assertEqual(result1["count"], 3)
                self.assertEqual(result1["after_seq"], None)
                self.assertEqual(result1["latest_seq"], 10)
                self.assertEqual(result1["has_more"], False)
                self.assertEqual(result1["next_after_seq"], 10)
                self.assertEqual(result1["cursor_reset"], False)
                # Last 3 items (seq 8, 9, 10)
                self.assertEqual([item["seq"] for item in result1["items"]], [8, 9, 10])

                # Cursor-based page 1
                result2 = connector_events(limit=3, after_seq=0)
                self.assertEqual(result2["count"], 3)
                self.assertEqual(result2["after_seq"], 0)
                self.assertEqual(result2["latest_seq"], 10)
                self.assertEqual(result2["has_more"], True)
                self.assertEqual(result2["next_after_seq"], 3)
                self.assertEqual(result2["cursor_reset"], False)
                self.assertEqual([item["seq"] for item in result2["items"]], [1, 2, 3])

                # Cursor-based page 2
                result3 = connector_events(limit=3, after_seq=3)
                self.assertEqual(result3["count"], 3)
                self.assertEqual(result3["after_seq"], 3)
                self.assertEqual(result3["has_more"], True)
                self.assertEqual(result3["next_after_seq"], 6)
                self.assertEqual([item["seq"] for item in result3["items"]], [4, 5, 6])

                # Cursor-based page 3 (more items exist after)
                result4 = connector_events(limit=3, after_seq=6)
                self.assertEqual(result4["count"], 3)
                self.assertEqual(result4["after_seq"], 6)
                self.assertEqual(result4["has_more"], True)
                self.assertEqual(result4["next_after_seq"], 9)
                self.assertEqual([item["seq"] for item in result4["items"]], [7, 8, 9])

                # Cursor-based page 4 (final page)
                result5 = connector_events(limit=3, after_seq=9)
                self.assertEqual(result5["count"], 1)
                self.assertEqual(result5["after_seq"], 9)
                self.assertEqual(result5["has_more"], False)
                self.assertEqual(result5["next_after_seq"], 10)
                self.assertEqual([item["seq"] for item in result5["items"]], [10])

    def test_connector_events_cursor_reset_on_invalid_cursor(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

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

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                result = connector_events(limit=10, after_seq=100)

            self.assertEqual(result["count"], 0)
            self.assertEqual(result["has_more"], False)
            self.assertEqual(result["next_after_seq"], 5)
            self.assertEqual(result["cursor_reset"], True)
            self.assertEqual(result["items"], [])

    def test_connector_events_cursor_with_connector_id_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

            records = []
            for i in range(10):
                records.append({
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": "connector-1" if i % 2 == 0 else "connector-2",
                    "provider_id": "google-drive",
                    "capabilities": [],
                    "surfaces": [],
                    "at": "2026-09-23T12:00:00Z",
                })

            events_path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                # Backward compat: last 2 items with filter
                # connector-1 appears at lines: 1, 3, 5, 7, 9
                result1 = connector_events(limit=2, connector_id="connector-1", after_seq=None)
                self.assertEqual(result1["count"], 2)
                self.assertEqual(result1["has_more"], False)
                self.assertEqual([item["connector_id"] for item in result1["items"]], ["connector-1", "connector-1"])
                # Last 2 items with connector-1 are at seq 7, 9
                self.assertEqual([item["seq"] for item in result1["items"]], [7, 9])

                # Cursor-based with filter: first 2 items for connector-2
                # connector-2 appears at lines: 2, 4, 6, 8, 10
                result2 = connector_events(limit=2, connector_id="connector-2", after_seq=0)
                self.assertEqual(result2["count"], 2)
                self.assertEqual(result2["has_more"], True)
                self.assertEqual([item["connector_id"] for item in result2["items"]], ["connector-2", "connector-2"])
                self.assertEqual([item["seq"] for item in result2["items"]], [2, 4])

    def test_connector_events_cursor_with_malformed_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

            content = "\n".join([
                json.dumps({"schema": EVENT_SCHEMA, "event": "connector.added", "connector_id": "valid-1", "provider_id": "p1", "capabilities": [], "surfaces": [], "at": "2026-09-23T12:00:00Z"}, sort_keys=True),
                "{invalid json",
                "",
                json.dumps({"schema": EVENT_SCHEMA, "event": "connector.added", "connector_id": "valid-2", "provider_id": "p2", "capabilities": [], "surfaces": [], "at": "2026-09-23T12:00:00Z"}, sort_keys=True),
            ])
            events_path.write_text(content, encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                result = connector_events(limit=10, after_seq=0)

            self.assertEqual(result["latest_seq"], 4)
            self.assertEqual(result["malformed"], 2)
            self.assertEqual(result["count"], 2)
            # seq values should be from the actual lines in the file (1, 4)
            self.assertEqual([item["seq"] for item in result["items"]], [1, 4])


if __name__ == "__main__":
    unittest.main()
