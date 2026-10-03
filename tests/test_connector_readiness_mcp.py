from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.connectors import REGISTRY_SCHEMA
from agent_os.mcp_server import _handle_mcp, methods


def connector_with_env_ref(connector_id: str, provider_id: str, secret_ref: str | None = None) -> dict:
    return {
        "id": connector_id,
        "provider": {"id": provider_id, "name": f"Provider {provider_id}"},
        "capabilities": ["test.read"],
        "scopes": ["test.readonly"],
        "health": {"status": "unknown", "checked_at": None},
        "privacy_domain": "work",
        "registrations": [{"surface_id": "agent-os-mcp", "state": "desired"}],
        "secret_ref": secret_ref,
    }


def valid_registry_with_connectors() -> dict:
    return {
        "schema": REGISTRY_SCHEMA,
        "version": 1,
        "connectors": [
            connector_with_env_ref("connector-1", "provider-a", "env:TEST_TOKEN"),
            connector_with_env_ref("connector-2", "provider-b"),
        ]
    }


class ConnectorProvisioningReadinessMcpTests(unittest.TestCase):
    def test_connector_provisioning_readiness_is_discoverable(self) -> None:
        available = methods()
        listing = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, available)
        names = {item["name"] for item in listing["result"]["tools"]}
        self.assertIn("connector.provisioning_readiness", names)

    def test_mcp_connector_provisioning_readiness_returns_schema(self) -> None:
        available = methods()
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry_with_connectors()):
            response = _handle_mcp(
                {
                    "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "connector.provisioning_readiness", "arguments": {}},
                },
                available,
            )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["schema"], "personal-agent/connector-provisioning-readiness/v1")

        # Ensure secret references are not exposed in payload
        payload_json = json.dumps(payload)
        self.assertNotIn("TEST_TOKEN", payload_json)
        self.assertNotIn("env:TEST_TOKEN", payload_json)


if __name__ == "__main__":
    unittest.main()
