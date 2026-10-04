from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.mcp_server import _handle_mcp, methods


class ConnectorSubscribersMcpTests(unittest.TestCase):
    def test_connector_subscriber_poll_is_discoverable(self) -> None:
        available = methods()
        listing = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, available)
        names = {item["name"] for item in listing["result"]["tools"]}
        self.assertIn("connector.subscriber_poll", names)

    def test_connector_subscriber_ack_is_discoverable(self) -> None:
        available = methods()
        listing = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, available)
        names = {item["name"] for item in listing["result"]["tools"]}
        self.assertIn("connector.subscriber_ack", names)

    def test_connector_subscriber_poll_input_schema(self) -> None:
        available = methods()
        listing = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, available)
        tools = {item["name"]: item for item in listing["result"]["tools"]}
        schema = tools["connector.subscriber_poll"]["inputSchema"]
        self.assertIn("subscriber_id", schema["properties"])
        self.assertIn("limit", schema["properties"])
        self.assertEqual(schema["required"], ["subscriber_id"])
        self.assertTrue(schema["additionalProperties"] is False)
        self.assertEqual(schema["properties"]["limit"]["minimum"], 1)
        self.assertEqual(schema["properties"]["limit"]["maximum"], 500)

    def test_connector_subscriber_ack_input_schema(self) -> None:
        available = methods()
        listing = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, available)
        tools = {item["name"]: item for item in listing["result"]["tools"]}
        schema = tools["connector.subscriber_ack"]["inputSchema"]
        self.assertIn("subscriber_id", schema["properties"])
        self.assertIn("seq", schema["properties"])
        self.assertIn("confirm_write", schema["properties"])
        self.assertEqual(set(schema["required"]), {"subscriber_id", "seq"})
        self.assertTrue(schema["additionalProperties"] is False)
        self.assertEqual(schema["properties"]["seq"]["minimum"], 0)

    def test_mcp_connector_subscriber_poll_returns_correct_schema(self) -> None:
        available = methods()
        with tempfile.TemporaryDirectory() as tmpdir:
            events_file = Path(tmpdir) / "events.jsonl"
            cursors_file = Path(tmpdir) / "cursors.json"
            lock_file = Path(tmpdir) / "lock"

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_file):
                with patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_file):
                    with patch("agent_os.connectors._REGISTRY_LOCK_PATH", lock_file):
                        response = _handle_mcp(
                            {
                                "jsonrpc": "2.0",
                                "id": 2,
                                "method": "tools/call",
                                "params": {"name": "connector.subscriber_poll", "arguments": {"subscriber_id": "test-subscriber"}},
                            },
                            available,
                        )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["schema"], "personal-agent/connector-subscriber-poll/v1")
        self.assertEqual(payload["subscriber_id"], "test-subscriber")

    def test_mcp_connector_subscriber_poll_with_events(self) -> None:
        available = methods()
        with tempfile.TemporaryDirectory() as tmpdir:
            events_file = Path(tmpdir) / "events.jsonl"
            cursors_file = Path(tmpdir) / "cursors.json"
            lock_file = Path(tmpdir) / "lock"

            events = [
                {"schema": "personal-agent/connector-event/v1", "event": "connector.added", "connector_id": "test-1", "provider_id": "p1", "capabilities": ["cap1"], "surfaces": ["s1"], "at": "2026-10-03T00:00:00Z"},
                {"schema": "personal-agent/connector-event/v1", "event": "connector.updated", "connector_id": "test-2", "provider_id": "p2", "capabilities": ["cap2"], "surfaces": ["s2"], "at": "2026-10-03T00:01:00Z"},
            ]
            events_file.write_text("\n".join(json.dumps(e) for e in events) + "\n")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_file):
                with patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_file):
                    with patch("agent_os.connectors._REGISTRY_LOCK_PATH", lock_file):
                        response = _handle_mcp(
                            {
                                "jsonrpc": "2.0",
                                "id": 3,
                                "method": "tools/call",
                                "params": {"name": "connector.subscriber_poll", "arguments": {"subscriber_id": "test-subscriber"}},
                            },
                            available,
                        )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["schema"], "personal-agent/connector-subscriber-poll/v1")
        self.assertEqual(payload["count"], 2)
        self.assertEqual(len(payload["items"]), 2)

    def test_mcp_connector_subscriber_ack_preview(self) -> None:
        available = methods()
        with tempfile.TemporaryDirectory() as tmpdir:
            events_file = Path(tmpdir) / "events.jsonl"
            cursors_file = Path(tmpdir) / "cursors.json"
            lock_file = Path(tmpdir) / "lock"

            events = [
                {"schema": "personal-agent/connector-event/v1", "event": "connector.added", "connector_id": "test-1", "provider_id": "p1", "capabilities": ["cap1"], "surfaces": ["s1"], "at": "2026-10-03T00:00:00Z"},
            ]
            events_file.write_text("\n".join(json.dumps(e) for e in events) + "\n")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_file):
                with patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_file):
                    with patch("agent_os.connectors._REGISTRY_LOCK_PATH", lock_file):
                        response = _handle_mcp(
                            {
                                "jsonrpc": "2.0",
                                "id": 4,
                                "method": "tools/call",
                                "params": {"name": "connector.subscriber_ack", "arguments": {"subscriber_id": "test-subscriber", "seq": 1}},
                            },
                            available,
                        )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["schema"], "personal-agent/connector-subscriber-ack/v1")
        self.assertEqual(payload["subscriber_id"], "test-subscriber")
        self.assertEqual(payload["after_seq"], 1)
        self.assertTrue(payload["preview"])
        self.assertFalse(payload["written"])

    def test_mcp_connector_subscriber_ack_confirm_and_poll(self) -> None:
        available = methods()
        with tempfile.TemporaryDirectory() as tmpdir:
            events_file = Path(tmpdir) / "events.jsonl"
            cursors_file = Path(tmpdir) / "cursors.json"
            lock_file = Path(tmpdir) / "lock"

            events = [
                {"schema": "personal-agent/connector-event/v1", "event": "connector.added", "connector_id": "test-1", "provider_id": "p1", "capabilities": ["cap1"], "surfaces": ["s1"], "at": "2026-10-03T00:00:00Z"},
                {"schema": "personal-agent/connector-event/v1", "event": "connector.updated", "connector_id": "test-2", "provider_id": "p2", "capabilities": ["cap2"], "surfaces": ["s2"], "at": "2026-10-03T00:01:00Z"},
                {"schema": "personal-agent/connector-event/v1", "event": "connector.removed", "connector_id": "test-3", "provider_id": "p3", "capabilities": ["cap3"], "surfaces": ["s3"], "at": "2026-10-03T00:02:00Z"},
            ]
            events_file.write_text("\n".join(json.dumps(e) for e in events) + "\n")

            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", events_file):
                with patch("agent_os.connectors._CONNECTOR_CURSORS_PATH", cursors_file):
                    with patch("agent_os.connectors._REGISTRY_LOCK_PATH", lock_file):
                        # First, acknowledge up to seq 1
                        ack_response = _handle_mcp(
                            {
                                "jsonrpc": "2.0",
                                "id": 5,
                                "method": "tools/call",
                                "params": {"name": "connector.subscriber_ack", "arguments": {"subscriber_id": "test-subscriber", "seq": 1, "confirm_write": True}},
                            },
                            available,
                        )
                        ack_payload = json.loads(ack_response["result"]["content"][0]["text"])
                        self.assertTrue(ack_payload["written"])

                        # Now poll; should only see events after seq 1
                        poll_response = _handle_mcp(
                            {
                                "jsonrpc": "2.0",
                                "id": 6,
                                "method": "tools/call",
                                "params": {"name": "connector.subscriber_poll", "arguments": {"subscriber_id": "test-subscriber"}},
                            },
                            available,
                        )
            poll_payload = json.loads(poll_response["result"]["content"][0]["text"])
            self.assertEqual(poll_payload["count"], 2)
            self.assertEqual(len(poll_payload["items"]), 2)
            self.assertEqual(poll_payload["items"][0]["seq"], 2)
            self.assertEqual(poll_payload["items"][1]["seq"], 3)


if __name__ == "__main__":
    unittest.main()
