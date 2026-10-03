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


def valid_registry_with_conflicts() -> dict:
    return {
        "schema": REGISTRY_SCHEMA,
        "version": 1,
        "connectors": [
            connector_with_env_ref("connector-1", "provider-a", "env:SHARED_TOKEN"),
            connector_with_env_ref("connector-2", "provider-b", "env:SHARED_TOKEN"),
        ]
    }


class ConnectorConflictsMcpTests(unittest.TestCase):
    def test_connector_conflicts_is_discoverable(self) -> None:
        available = methods()
        listing = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, available)
        names = {item["name"] for item in listing["result"]["tools"]}
        self.assertIn("connector.conflicts", names)

    def test_mcp_connector_conflicts_redacts_secret_references(self) -> None:
        available = methods()
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry_with_conflicts()):
            response = _handle_mcp(
                {
                    "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "connector.conflicts", "arguments": {}},
                },
                available,
            )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["schema"], "personal-agent/connector-conflicts/v1")
        self.assertGreater(len(payload["conflicts"]), 0)

        # Check that the conflict is a shared_credential_reference
        shared_ref_conflicts = [c for c in payload["conflicts"] if c["kind"] == "shared_credential_reference"]
        self.assertGreater(len(shared_ref_conflicts), 0)

        # Ensure secret references are not exposed in payload
        payload_json = json.dumps(payload)
        self.assertNotIn("SHARED_TOKEN", payload_json)
        self.assertNotIn("env:SHARED_TOKEN", payload_json)


if __name__ == "__main__":
    unittest.main()
