from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.mcp_server import _handle_mcp, methods


class ConnectorSetRegistrationStateMcpTests(unittest.TestCase):
    def test_connector_set_registration_state_is_discoverable(self) -> None:
        available = methods()
        listing = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, available)
        names = {item["name"] for item in listing["result"]["tools"]}
        self.assertIn("connector.set_registration_state", names)

    def test_mcp_connector_set_registration_state_preview_with_desired_registration(self) -> None:
        available = methods()
        connector_data = {
            "schema": "personal-agent/connector-registry/v1",
            "version": 1,
            "connectors": [
                {
                    "id": "test-connector",
                    "provider": {"id": "test-provider", "name": "Test Provider"},
                    "capabilities": ["test"],
                    "scopes": ["read"],
                    "health": {"status": "unknown", "checked_at": None},
                    "privacy_domain": "personal",
                    "registrations": [
                        {"surface_id": "agent-os-mcp", "state": "desired"}
                    ],
                    "secret_ref": None,
                }
            ],
        }
        with patch("agent_os.connectors.load_connector_registry", return_value=connector_data):
            response = _handle_mcp(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "connector.set_registration_state",
                        "arguments": {
                            "connector_id": "test-connector",
                            "surface_id": "agent-os-mcp",
                            "state": "disabled",
                        },
                    },
                },
                available,
            )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertFalse(payload["written"])
        self.assertTrue(payload["would_change"])

    def test_mcp_connector_set_registration_state_invalid_state_error(self) -> None:
        available = methods()
        connector_data = {
            "schema": "personal-agent/connector-registry/v1",
            "version": 1,
            "connectors": [
                {
                    "id": "test-connector",
                    "provider": {"id": "test-provider", "name": "Test Provider"},
                    "capabilities": ["test"],
                    "scopes": ["read"],
                    "health": {"status": "unknown", "checked_at": None},
                    "privacy_domain": "personal",
                    "registrations": [
                        {"surface_id": "agent-os-mcp", "state": "desired"}
                    ],
                    "secret_ref": None,
                }
            ],
        }
        with patch("agent_os.connectors.load_connector_registry", return_value=connector_data):
            response = _handle_mcp(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "connector.set_registration_state",
                        "arguments": {
                            "connector_id": "test-connector",
                            "surface_id": "agent-os-mcp",
                            "state": "registered",
                        },
                    },
                },
                available,
            )
        self.assertTrue(response["result"]["isError"])


if __name__ == "__main__":
    unittest.main()
