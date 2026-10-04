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
    connector_subscriber_remove,
)


class ConnectorSubscriberRemoveTests(unittest.TestCase):
    def test_connector_subscriber_remove_invalid_subscriber_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            with patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                with self.assertRaises(ValueError):
                    connector_subscriber_remove("INVALID")

    def test_connector_subscriber_remove_preview_mode_nonexistent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            with patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                result = connector_subscriber_remove("my-subscriber", confirm_write=False)

            self.assertEqual(result["schema"], "personal-agent/connector-subscriber-remove/v1")
            self.assertEqual(result["subscriber_id"], "my-subscriber")
            self.assertEqual(result["existed"], False)
            self.assertEqual(result["previous_after_seq"], None)
            self.assertEqual(result["preview"], True)
            self.assertEqual(result["written"], False)

    def test_connector_subscriber_remove_preview_mode_existing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            # Create cursor store with a subscriber
            cursor_store = {
                "schema": "personal-agent/connector-event-cursors/v1",
                "subscribers": {
                    "my-subscriber": {"after_seq": 5}
                }
            }
            cursors_path.write_text(json.dumps(cursor_store), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                result = connector_subscriber_remove("my-subscriber", confirm_write=False)

            self.assertEqual(result["schema"], "personal-agent/connector-subscriber-remove/v1")
            self.assertEqual(result["subscriber_id"], "my-subscriber")
            self.assertEqual(result["existed"], True)
            self.assertEqual(result["previous_after_seq"], 5)
            self.assertEqual(result["preview"], True)
            self.assertEqual(result["written"], False)
            # File should not be modified in preview mode
            self.assertIn("my-subscriber", json.loads(cursors_path.read_text(encoding="utf-8"))["subscribers"])

    def test_connector_subscriber_remove_write_mode_nonexistent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            with patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                result = connector_subscriber_remove("my-subscriber", confirm_write=True)

            self.assertEqual(result["schema"], "personal-agent/connector-subscriber-remove/v1")
            self.assertEqual(result["subscriber_id"], "my-subscriber")
            self.assertEqual(result["existed"], False)
            self.assertEqual(result["previous_after_seq"], None)
            self.assertEqual(result["preview"], False)
            self.assertEqual(result["written"], False)
            self.assertEqual(result.get("not_found"), True)

    def test_connector_subscriber_remove_write_mode_existing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            # Create cursor store with a subscriber
            cursor_store = {
                "schema": "personal-agent/connector-event-cursors/v1",
                "subscribers": {
                    "my-subscriber": {"after_seq": 5}
                }
            }
            cursors_path.write_text(json.dumps(cursor_store), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                result = connector_subscriber_remove("my-subscriber", confirm_write=True)

            self.assertEqual(result["schema"], "personal-agent/connector-subscriber-remove/v1")
            self.assertEqual(result["subscriber_id"], "my-subscriber")
            self.assertEqual(result["existed"], True)
            self.assertEqual(result["previous_after_seq"], 5)
            self.assertEqual(result["preview"], False)
            self.assertEqual(result["written"], True)

            # Verify file was updated
            updated_store = json.loads(cursors_path.read_text(encoding="utf-8"))
            self.assertNotIn("my-subscriber", updated_store["subscribers"])

    def test_connector_subscriber_remove_write_mode_multiple_subscribers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            # Create cursor store with multiple subscribers
            cursor_store = {
                "schema": "personal-agent/connector-event-cursors/v1",
                "subscribers": {
                    "subscriber-1": {"after_seq": 3},
                    "subscriber-2": {"after_seq": 5},
                    "subscriber-3": {"after_seq": 7},
                }
            }
            cursors_path.write_text(json.dumps(cursor_store), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                result = connector_subscriber_remove("subscriber-2", confirm_write=True)

            self.assertEqual(result["written"], True)
            self.assertEqual(result["existed"], True)
            self.assertEqual(result["previous_after_seq"], 5)

            # Verify file was updated correctly
            updated_store = json.loads(cursors_path.read_text(encoding="utf-8"))
            self.assertEqual(len(updated_store["subscribers"]), 2)
            self.assertIn("subscriber-1", updated_store["subscribers"])
            self.assertNotIn("subscriber-2", updated_store["subscribers"])
            self.assertIn("subscriber-3", updated_store["subscribers"])
            self.assertEqual(updated_store["subscribers"]["subscriber-1"]["after_seq"], 3)
            self.assertEqual(updated_store["subscribers"]["subscriber-3"]["after_seq"], 7)

    def test_connector_subscriber_remove_malformed_cursor_store_raises_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            cursors_path.write_text("{invalid json", encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                with self.assertRaises(ValueError) as ctx:
                    connector_subscriber_remove("my-subscriber", confirm_write=True)

                self.assertIn("malformed", str(ctx.exception).lower())

    def test_connector_subscriber_remove_confirm_write_must_be_bool(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            with patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                with self.assertRaises(ValueError):
                    connector_subscriber_remove("my-subscriber", confirm_write="not-a-bool")

    def test_connector_subscriber_remove_write_mode_removes_single_subscriber(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            # Create cursor store with a single subscriber
            cursor_store = {
                "schema": "personal-agent/connector-event-cursors/v1",
                "subscribers": {
                    "only-subscriber": {"after_seq": 10}
                }
            }
            cursors_path.write_text(json.dumps(cursor_store), encoding="utf-8")

            with patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                result = connector_subscriber_remove("only-subscriber", confirm_write=True)

            self.assertEqual(result["written"], True)

            # Verify subscriber was removed and store is empty
            updated_store = json.loads(cursors_path.read_text(encoding="utf-8"))
            self.assertEqual(updated_store["schema"], "personal-agent/connector-event-cursors/v1")
            self.assertEqual(len(updated_store["subscribers"]), 0)

    def test_connector_subscriber_remove_preview_doesnt_modify_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cursors_path = Path(tmpdir) / "connector-event-cursors.json"

            # Create cursor store
            cursor_store = {
                "schema": "personal-agent/connector-event-cursors/v1",
                "subscribers": {
                    "my-subscriber": {"after_seq": 5}
                }
            }
            cursors_path.write_text(json.dumps(cursor_store), encoding="utf-8")
            original_content = cursors_path.read_bytes()

            with patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_path):
                connector_subscriber_remove("my-subscriber", confirm_write=False)

            # File should be unchanged
            self.assertEqual(cursors_path.read_bytes(), original_content)


if __name__ == "__main__":
    unittest.main()
