from __future__ import annotations

import json
import sys
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


class ConnectorCredentialStatusMcpTests(unittest.TestCase):
    def test_connector_credential_status_is_discoverable(self) -> None:
        available = methods()
        listing = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, available)
        names = {item["name"] for item in listing["result"]["tools"]}
        self.assertIn("connector.credential_status", names)

    def test_mcp_connector_credential_status_redacts_keyring_references(self) -> None:
        available = methods()
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry_with_keyring()):
            response = _handle_mcp(
                {
                    "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "connector.credential_status", "arguments": {}},
                },
                available,
            )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["schema"], "personal-agent/connector-credential-status/v1")
        self.assertFalse(payload["values_returned"])
        # Check that status is present in items and has expected structure
        self.assertGreater(len(payload["items"]), 0)
        self.assertEqual(payload["items"][0]["status"], "unchecked")
        # Ensure keyring references are not exposed
        self.assertNotIn("keyring:agent-os/keyring-test", json.dumps(payload))
        self.assertNotIn("agent-os/keyring-test", json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
