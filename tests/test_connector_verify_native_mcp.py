from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.mcp_server import _handle_mcp, methods


class ConnectorVerifyNativeMcpTests(unittest.TestCase):
    def test_connector_verify_native_is_discoverable(self) -> None:
        available = methods()
        listing = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, available)
        names = {item["name"] for item in listing["result"]["tools"]}
        self.assertIn("connector.verify_native", names)

    def test_mcp_connector_verify_native_returns_correct_schema(self) -> None:
        available = methods()
        with patch("agent_os.connectors.verify_native_registrations", return_value={
            "schema": "personal-agent/connector-verify-native/v1",
            "written": False,
            "confirmation_required": True,
            "connector_id": None,
            "changes": [],
            "count": 0,
            "unchanged_counts": {},
            "verification": "client_config_entry_observed",
        }):
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
