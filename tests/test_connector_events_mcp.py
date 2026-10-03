from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.mcp_server import _handle_mcp, methods


class ConnectorEventsMcpTests(unittest.TestCase):
    def test_connector_events_is_discoverable(self) -> None:
        available = methods()
        listing = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, available)
        names = {item["name"] for item in listing["result"]["tools"]}
        self.assertIn("connector.events", names)

    def test_connector_events_input_schema_has_after_seq(self) -> None:
        available = methods()
        listing = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, available)
        tools = {item["name"]: item for item in listing["result"]["tools"]}
        schema = tools["connector.events"]["inputSchema"]
        self.assertIn("after_seq", schema["properties"])
        after_seq_schema = schema["properties"]["after_seq"]
        self.assertEqual(after_seq_schema["type"], ["integer", "null"])
        self.assertEqual(after_seq_schema["minimum"], 0)

    def test_connector_unregister_is_discoverable(self) -> None:
        available = methods()
        listing = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, available)
        names = {item["name"] for item in listing["result"]["tools"]}
        self.assertIn("connector.unregister", names)

    def test_mcp_connector_events_with_missing_file(self) -> None:
        available = methods()
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_file = Path(tmpdir) / "events.jsonl"
            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", missing_file):
                response = _handle_mcp(
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {"name": "connector.events", "arguments": {}},
                    },
                    available,
                )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["schema"], "personal-agent/connector-events/v1")
        self.assertEqual(payload["count"], 0)
        self.assertEqual(payload["items"], [])

    def test_mcp_connector_events_with_real_events(self) -> None:
        available = methods()
        with tempfile.TemporaryDirectory() as tmpdir:
            events_file = Path(tmpdir) / "events.jsonl"
            events = [
                {"schema": "personal-agent/connector-event/v1", "event": "connector.added", "connector_id": "test-1", "provider_id": "p1", "capabilities": ["cap1"], "surfaces": ["s1"], "at": "2026-10-03T00:00:00Z"},
                {"schema": "personal-agent/connector-event/v1", "event": "connector.updated", "connector_id": "test-2", "provider_id": "p2", "capabilities": ["cap2"], "surfaces": ["s2"], "at": "2026-10-03T00:01:00Z"},
                {"schema": "personal-agent/connector-event/v1", "event": "connector.removed", "connector_id": "test-3", "provider_id": "p3", "capabilities": ["cap3"], "surfaces": ["s3"], "at": "2026-10-03T00:02:00Z"},
            ]
            events_file.write_text("\n".join(json.dumps(e) for e in events) + "\n")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_file):
                response = _handle_mcp(
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {"name": "connector.events", "arguments": {}},
                    },
                    available,
                )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["schema"], "personal-agent/connector-events/v1")
        self.assertEqual(payload["count"], 3)
        self.assertEqual(len(payload["items"]), 3)

    def test_mcp_connector_events_with_limit(self) -> None:
        available = methods()
        with tempfile.TemporaryDirectory() as tmpdir:
            events_file = Path(tmpdir) / "events.jsonl"
            events = [
                {"schema": "personal-agent/connector-event/v1", "event": "connector.added", "connector_id": "test-1", "provider_id": "p1", "capabilities": ["cap1"], "surfaces": ["s1"], "at": "2026-10-03T00:00:00Z"},
                {"schema": "personal-agent/connector-event/v1", "event": "connector.added", "connector_id": "test-2", "provider_id": "p2", "capabilities": ["cap2"], "surfaces": ["s2"], "at": "2026-10-03T00:01:00Z"},
                {"schema": "personal-agent/connector-event/v1", "event": "connector.added", "connector_id": "test-3", "provider_id": "p3", "capabilities": ["cap3"], "surfaces": ["s3"], "at": "2026-10-03T00:02:00Z"},
            ]
            events_file.write_text("\n".join(json.dumps(e) for e in events) + "\n")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_file):
                response = _handle_mcp(
                    {
                        "jsonrpc": "2.0",
                        "id": 4,
                        "method": "tools/call",
                        "params": {"name": "connector.events", "arguments": {"limit": 2}},
                    },
                    available,
                )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["schema"], "personal-agent/connector-events/v1")
        self.assertEqual(payload["limit"], 2)
        self.assertEqual(len(payload["items"]), 2)

    def test_mcp_connector_events_with_connector_id_filter(self) -> None:
        available = methods()
        with tempfile.TemporaryDirectory() as tmpdir:
            events_file = Path(tmpdir) / "events.jsonl"
            events = [
                {"schema": "personal-agent/connector-event/v1", "event": "connector.added", "connector_id": "test-1", "provider_id": "p1", "capabilities": ["cap1"], "surfaces": ["s1"], "at": "2026-10-03T00:00:00Z"},
                {"schema": "personal-agent/connector-event/v1", "event": "connector.updated", "connector_id": "test-2", "provider_id": "p2", "capabilities": ["cap2"], "surfaces": ["s2"], "at": "2026-10-03T00:01:00Z"},
                {"schema": "personal-agent/connector-event/v1", "event": "connector.added", "connector_id": "test-1", "provider_id": "p1", "capabilities": ["cap1"], "surfaces": ["s1"], "at": "2026-10-03T00:02:00Z"},
            ]
            events_file.write_text("\n".join(json.dumps(e) for e in events) + "\n")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_file):
                response = _handle_mcp(
                    {
                        "jsonrpc": "2.0",
                        "id": 5,
                        "method": "tools/call",
                        "params": {"name": "connector.events", "arguments": {"connector_id": "test-1"}},
                    },
                    available,
                )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["schema"], "personal-agent/connector-events/v1")
        self.assertEqual(payload["connector_filter"], "test-1")
        self.assertEqual(len(payload["items"]), 2)

    def test_mcp_connector_events_with_after_seq_pagination(self) -> None:
        available = methods()
        with tempfile.TemporaryDirectory() as tmpdir:
            events_file = Path(tmpdir) / "events.jsonl"
            events = [
                {"schema": "personal-agent/connector-event/v1", "event": "connector.added", "connector_id": "test-1", "provider_id": "p1", "capabilities": ["cap1"], "surfaces": ["s1"], "at": "2026-10-03T00:00:00Z"},
                {"schema": "personal-agent/connector-event/v1", "event": "connector.added", "connector_id": "test-2", "provider_id": "p2", "capabilities": ["cap2"], "surfaces": ["s2"], "at": "2026-10-03T00:01:00Z"},
                {"schema": "personal-agent/connector-event/v1", "event": "connector.added", "connector_id": "test-3", "provider_id": "p3", "capabilities": ["cap3"], "surfaces": ["s3"], "at": "2026-10-03T00:02:00Z"},
            ]
            events_file.write_text("\n".join(json.dumps(e) for e in events) + "\n")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_file):
                response = _handle_mcp(
                    {
                        "jsonrpc": "2.0",
                        "id": 8,
                        "method": "tools/call",
                        "params": {"name": "connector.events", "arguments": {"after_seq": 1}},
                    },
                    available,
                )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["schema"], "personal-agent/connector-events/v1")
        self.assertEqual(len(payload["items"]), 2)
        self.assertEqual(payload["items"][0]["seq"], 2)
        self.assertEqual(payload["items"][1]["seq"], 3)
        self.assertEqual(payload["next_after_seq"], 3)
        self.assertFalse(payload["has_more"])

    def test_mcp_connector_unregister_preview_absent(self) -> None:
        available = methods()
        with patch("agent_os.connectors.load_connector_registry", return_value={"schema": "personal-agent/connector-registry/v1", "version": 1, "connectors": []}):
            response = _handle_mcp(
                {
                    "jsonrpc": "2.0",
                    "id": 6,
                    "method": "tools/call",
                    "params": {"name": "connector.unregister", "arguments": {"connector_id": "absent-one"}},
                },
                available,
            )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertFalse(payload["written"])
        self.assertTrue(payload["confirmation_required"])
        self.assertEqual(payload["connector_id"], "absent-one")
        self.assertFalse(payload["found"])

    def test_mcp_connector_unregister_confirm_absent(self) -> None:
        available = methods()
        with patch("agent_os.connectors.load_connector_registry", return_value={"schema": "personal-agent/connector-registry/v1", "version": 1, "connectors": []}):
            response = _handle_mcp(
                {
                    "jsonrpc": "2.0",
                    "id": 7,
                    "method": "tools/call",
                    "params": {"name": "connector.unregister", "arguments": {"connector_id": "absent-one", "confirm_write": True}},
                },
                available,
            )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertFalse(payload["written"])
        self.assertTrue(payload["not_found"])
        self.assertEqual(payload["connector_id"], "absent-one")


if __name__ == "__main__":
    unittest.main()
