from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.connectors import EVENT_SCHEMA
from agent_os.surfaces import _connector_event_summary, health


class ConnectorEventSummaryTests(unittest.TestCase):
    def test_missing_events_file_returns_available_true_with_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

            with patch("agent_os.surfaces._connector_event_summary") as mock_summary:
                # First, let's test the actual implementation with a missing file
                with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                    result = _connector_event_summary()

            self.assertTrue(result["available"])
            self.assertEqual(result["latest_seq"], 0)
            self.assertEqual(result["window"], 0)
            self.assertEqual(result["counts_by_event"]["connector.added"], 0)
            self.assertEqual(result["counts_by_event"]["connector.updated"], 0)
            self.assertEqual(result["counts_by_event"]["connector.removed"], 0)
            self.assertIsNone(result["last_event_at"])
            self.assertEqual(result["changed_connector_ids"], [])
            self.assertTrue(result["read_only"])

    def test_jsonl_file_with_multiple_events_returns_correct_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

            records = [
                {
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": "google-drive-1",
                    "provider_id": "google-drive",
                    "capabilities": ["files.read", "files.search"],
                    "surfaces": ["claude-code"],
                    "at": "2026-09-23T12:00:00Z",
                },
                {
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": "slack-1",
                    "provider_id": "slack",
                    "capabilities": ["messages.read"],
                    "surfaces": ["claude-code"],
                    "at": "2026-09-23T12:01:00Z",
                },
                {
                    "schema": EVENT_SCHEMA,
                    "event": "connector.updated",
                    "connector_id": "google-drive-1",
                    "provider_id": "google-drive",
                    "capabilities": ["files.read", "files.search", "files.write"],
                    "surfaces": ["claude-code"],
                    "at": "2026-09-23T12:02:00Z",
                },
                {
                    "schema": EVENT_SCHEMA,
                    "event": "connector.removed",
                    "connector_id": "slack-1",
                    "provider_id": "slack",
                    "capabilities": ["messages.read"],
                    "surfaces": [],
                    "at": "2026-09-23T12:03:00Z",
                },
            ]

            events_path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                result = _connector_event_summary()

            self.assertTrue(result["available"])
            self.assertEqual(result["latest_seq"], 4)
            self.assertEqual(result["window"], 4)
            self.assertEqual(result["counts_by_event"]["connector.added"], 2)
            self.assertEqual(result["counts_by_event"]["connector.updated"], 1)
            self.assertEqual(result["counts_by_event"]["connector.removed"], 1)
            self.assertEqual(result["last_event_at"], "2026-09-23T12:03:00Z")
            self.assertEqual(sorted(result["changed_connector_ids"]), ["google-drive-1", "slack-1"])

    def test_malformed_lines_do_not_break_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

            content = "\n".join([
                json.dumps({
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": "valid-1",
                    "provider_id": "p1",
                    "capabilities": [],
                    "surfaces": [],
                    "at": "2026-09-23T12:00:00Z",
                }, sort_keys=True),
                "{invalid json",
                "",
                json.dumps({
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": "valid-2",
                    "provider_id": "p2",
                    "capabilities": [],
                    "surfaces": [],
                    "at": "2026-09-23T12:01:00Z",
                }, sort_keys=True),
            ])
            events_path.write_text(content, encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                result = _connector_event_summary()

            self.assertTrue(result["available"])
            self.assertEqual(result["window"], 2)
            self.assertEqual(result["counts_by_event"]["connector.added"], 2)
            self.assertGreater(result["malformed"], 0)

    def test_summary_has_exact_key_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                result = _connector_event_summary()

            expected_keys = {"schema", "available", "latest_seq", "window", "malformed",
                           "counts_by_event", "last_event_at", "changed_connector_ids", "read_only"}
            self.assertEqual(set(result.keys()), expected_keys)

    def test_summary_json_dump_contains_no_capability_or_surface_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

            records = [
                {
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": "test-1",
                    "provider_id": "provider",
                    "capabilities": ["unique-capability-xyz"],
                    "surfaces": ["unique-surface-abc"],
                    "at": "2026-09-23T12:00:00Z",
                },
            ]

            events_path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                result = _connector_event_summary()
                dumped = json.dumps(result)

            self.assertNotIn("unique-capability-xyz", dumped)
            self.assertNotIn("unique-surface-abc", dumped)

    def test_connector_events_oserror_returns_available_false(self) -> None:
        with patch("agent_os.surfaces.connector_events", side_effect=OSError("secret-path")):
            result = _connector_event_summary()

            self.assertFalse(result["available"])
            self.assertIn("reason", result)
            dumped = json.dumps(result)
            self.assertNotIn("secret-path", dumped)

    def test_health_includes_connector_events_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "connector-events.jsonl"

            records = [
                {
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": "c1",
                    "provider_id": "p1",
                    "capabilities": [],
                    "surfaces": [],
                    "at": "2026-09-23T12:00:00Z",
                },
                {
                    "schema": EVENT_SCHEMA,
                    "event": "connector.added",
                    "connector_id": "c2",
                    "provider_id": "p2",
                    "capabilities": [],
                    "surfaces": [],
                    "at": "2026-09-23T12:01:00Z",
                },
                {
                    "schema": EVENT_SCHEMA,
                    "event": "connector.updated",
                    "connector_id": "c1",
                    "provider_id": "p1",
                    "capabilities": [],
                    "surfaces": [],
                    "at": "2026-09-23T12:02:00Z",
                },
                {
                    "schema": EVENT_SCHEMA,
                    "event": "connector.removed",
                    "connector_id": "c2",
                    "provider_id": "p2",
                    "capabilities": [],
                    "surfaces": [],
                    "at": "2026-09-23T12:03:00Z",
                },
            ]

            events_path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_path):
                result = health()

            self.assertIn("connector_providers", result)
            self.assertIn("events", result["connector_providers"])
            self.assertEqual(result["connector_providers"]["events"]["latest_seq"], 4)


if __name__ == "__main__":
    unittest.main()
