from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.connectors import REGISTRY_SCHEMA
from agent_os.mcp_server import _handle_mcp, methods


def simple_connector(connector_id: str, provider_id: str) -> dict:
    return {
        "id": connector_id,
        "provider": {"id": provider_id, "name": f"Provider {provider_id}"},
        "capabilities": ["test.read"],
        "scopes": ["test.readonly"],
        "health": {"status": "unknown", "checked_at": None},
        "privacy_domain": "work",
        "registrations": [{"surface_id": "agent-os-mcp", "state": "desired"}],
        "secret_ref": None,
    }


def valid_registry() -> dict:
    return {
        "schema": REGISTRY_SCHEMA,
        "version": 1,
        "connectors": [simple_connector("connector-1", "provider-a")]
    }


class ConnectorVerifyNativeMcpTests(unittest.TestCase):
    def test_connector_verify_native_is_discoverable(self) -> None:
        available = methods()
        listing = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, available)
        names = {item["name"] for item in listing["result"]["tools"]}
        self.assertIn("connector.verify_native", names)

    def test_mcp_connector_verify_native_returns_correct_schema(self) -> None:
        available = methods()
        with patch("agent_os.connectors.load_connector_registry", return_value=valid_registry()):
            with patch("agent_os.surfaces.surfaces", return_value=[{"id": "agent-os-mcp", "kind": "mcp", "executable_name": "test"}]):
                response = _handle_mcp(
                    {
                        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                        "params": {"name": "connector.verify_native", "arguments": {}},
                    },
                    available,
                )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["schema"], "personal-agent/connector-verify-native/v1")
        self.assertFalse(payload["written"])


if __name__ == "__main__":
    unittest.main()
