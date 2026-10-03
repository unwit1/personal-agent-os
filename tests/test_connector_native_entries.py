from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.mcp_server import _handle_mcp, methods


class TestConnectorNativeEntries(unittest.TestCase):
    def test_connector_register_and_import_have_server_name_property(self) -> None:
        available = methods()
        listing = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, available)
        tools = {item["name"]: item for item in listing["result"]["tools"]}

        self.assertIn("connector.register", tools)
        self.assertIn("connector.import", tools)

        for tool_name in ["connector.register", "connector.import"]:
            with self.subTest(tool=tool_name):
                tool = tools[tool_name]
                input_schema = tool["inputSchema"]
                connector_props = input_schema["properties"]["connector"]["properties"]
                registrations_schema = connector_props["registrations"]

                items_schema = registrations_schema["items"]
                self.assertEqual(items_schema["type"], "object")

                item_properties = items_schema["properties"]
                self.assertIn("server_name", item_properties)
                self.assertEqual(item_properties["server_name"], {"type": "string"})

                self.assertIn("surface_id", item_properties)
                self.assertIn("state", item_properties)

                required = items_schema["required"]
                self.assertEqual(set(required), {"surface_id", "state"})

                self.assertFalse(items_schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
