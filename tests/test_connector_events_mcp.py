from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.connectors import REGISTRY_SCHEMA
from agent_os.mcp_server import _handle_mcp, methods


def valid_connector_with_keyring() -> dict:
    return {
        "id": "keyring-test",
        "provider": {"id": "test-provider", "name": "Test Provider"},
        "capabilities": ["test.read"],
        "scopes": ["test.readonly"],
        "health": {"status": "unknown", "checked_at": None},
        "privacy_domain": "work",
        "registrations": [{"surface_id": "agent-os-mcp", "state": "desired"}],
        "secret_ref": "keyring:agent-os/keyring-test",
    }


def valid_registry_with_keyring() -> dict:
    return {"schema": REGISTRY_SCHEMA, "version": 1, "connectors": [valid_connector_with_keyring()]}


class ConnectorEventsMcpTests(unittest.TestCase):
    def test_connector_events_is_discoverable(self) -> None:
        available = methods()
        listing = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, available)
        names = {item["name"] for item in listing["result"]["tools"]}
        self.assertIn("connector.events", names)

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

    def test_mcp_connector_events_with_limit_parameter(self) -> None:
        available = methods()
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_file = Path(tmpdir) / "events.jsonl"
            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", missing_file):
                response = _handle_mcp(
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {"name": "connector.events", "arguments": {"limit": 1}},
                    },
                    available,
                )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["schema"], "personal-agent/connector-events/v1")
        self.assertEqual(payload["limit"], 1)
        self.assertEqual(payload["count"], 0)

    def test_mcp_connector_events_with_connector_id_filter(self) -> None:
        available = methods()
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_file = Path(tmpdir) / "events.jsonl"
            with patch("agent_os.connectors._CONNECTOR_EVENTS_PATH", missing_file):
                response = _handle_mcp(
                    {
                        "jsonrpc": "2.0",
                        "id": 4,
                        "method": "tools/call",
                        "params": {"name": "connector.events", "arguments": {"connector_id": "test-connector"}},
                    },
                    available,
                )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["schema"], "personal-agent/connector-events/v1")
        self.assertEqual(payload["connector_filter"], "test-connector")
        self.assertEqual(payload["count"], 0)

    def test_mcp_connector_unregister_preview_absent_connector(self) -> None:
        available = methods()
        with patch("agent_os.connectors.load_connector_registry", return_value={"schema": REGISTRY_SCHEMA, "version": 1, "connectors": []}):
            response = _handle_mcp(
                {
                    "jsonrpc": "2.0",
                    "id": 5,
                    "method": "tools/call",
                    "params": {"name": "connector.unregister", "arguments": {"connector_id": "absent-one"}},
                },
                available,
            )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["written"], False)
        self.assertEqual(payload["confirmation_required"], True)
        self.assertEqual(payload["connector_id"], "absent-one")

    def test_mcp_connector_unregister_remove_existing_connector(self) -> None:
        available = methods()
        test_registry = valid_registry_with_keyring()
        with patch("agent_os.connectors.load_connector_registry", return_value=test_registry):
            with patch("agent_os.connectors.write_json"):
                with patch("agent_os.connectors._append_connector_event", return_value=True):
                    response = _handle_mcp(
                        {
                            "jsonrpc": "2.0",
                            "id": 6,
                            "method": "tools/call",
                            "params": {"name": "connector.unregister", "arguments": {"connector_id": "keyring-test", "confirm_write": True}},
                        },
                        available,
                    )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["written"], True)
        self.assertEqual(payload["connector_id"], "keyring-test")
        self.assertEqual(payload["event_recorded"], True)


if __name__ == "__main__":
    unittest.main()
