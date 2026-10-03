from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.mcp_server import _handle_mcp, methods


class ConnectorPruneStaleMcpTests(unittest.TestCase):
    def test_connector_prune_stale_is_discoverable(self) -> None:
        available = methods()
        listing = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, available)
        names = {item["name"] for item in listing["result"]["tools"]}
        self.assertIn("connector.prune_stale", names)

    def test_mcp_connector_prune_stale_empty_registry_preview(self) -> None:
        available = methods()
        with patch("agent_os.connectors.load_connector_registry", return_value={"schema": "personal-agent/connector-registry/v1", "version": 1, "connectors": []}):
            with patch("agent_os.surfaces.surfaces", return_value=[]):
                response = _handle_mcp(
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {"name": "connector.prune_stale", "arguments": {}},
                    },
                    available,
                )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertFalse(payload["written"])
        self.assertEqual(payload["count"], 0)

    def test_mcp_connector_prune_stale_empty_registry_confirm(self) -> None:
        available = methods()
        with patch("agent_os.connectors.load_connector_registry", return_value={"schema": "personal-agent/connector-registry/v1", "version": 1, "connectors": []}):
            with patch("agent_os.surfaces.surfaces", return_value=[]):
                response = _handle_mcp(
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {"name": "connector.prune_stale", "arguments": {"confirm_write": True}},
                    },
                    available,
                )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertFalse(payload["written"])
        self.assertTrue(payload["idempotent"])


if __name__ == "__main__":
    unittest.main()
