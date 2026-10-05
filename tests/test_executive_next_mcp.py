from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import mcp_server
from agent_os.executive.window import registry as window_registry


class NextActionMcpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict(os.environ, {"AGENT_OS_EXECUTIVE_WINDOW_HOME": self.tmp.name})
        env.start()
        self.addCleanup(env.stop)
        self.reg = window_registry.Registry()
        self.reg.register_provider("test_low", lambda: [
            {
                "id": "item-low",
                "tab": "work",
                "kind": "test",
                "title": "Low Priority Item",
                "why": "low priority reason",
                "source": "test",
                "score": 10,
                "age_days": 1,
            }
        ])
        self.reg.register_provider("test_high", lambda: [
            {
                "id": "item-high",
                "tab": "work",
                "kind": "test",
                "title": "High Priority Item",
                "why": "high priority reason",
                "source": "test",
                "score": 100,
                "age_days": 5,
            }
        ])
        patcher = patch.object(mcp_server, "_window_registry", lambda: self.reg)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.available = mcp_server.methods()

    def rpc(self, method, params=None):
        response = mcp_server._handle_mcp({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}, self.available)
        return response["result"]

    def call(self, name, arguments):
        result = self.rpc("tools/call", {"name": name, "arguments": arguments})
        self.assertFalse(result["isError"], result)
        return json.loads(result["content"][0]["text"])

    def test_tools_list_includes_both_tools(self):
        tools = {t["name"]: t for t in self.rpc("tools/list")["tools"]}
        self.assertIn("executive_window.next", tools)
        self.assertIn("executive_window.explain", tools)
        self.assertIn("description", tools["executive_window.next"])
        self.assertIn("description", tools["executive_window.explain"])

    def test_next_returns_higher_score_with_rank(self):
        out = self.call("executive_window.next", {"tab": "work"})
        self.assertIsNotNone(out["next"])
        # The top item should be the high-priority one
        self.assertEqual(out["next"]["window_item"]["id"], "item-high")
        self.assertIsNotNone(out["why"])
        self.assertEqual(out["why"]["rank"], 1)
        self.assertEqual(out["why"]["of"], 2)
        self.assertEqual(out["why"]["priority"], 100)

    def test_explain_returns_ranking_info(self):
        # Get the queue item id first from next
        next_result = self.call("executive_window.next", {"tab": "work"})
        item_id = next_result["next"]["id"]

        # Explain using the queue item id
        out = self.call("executive_window.explain", {"item_id": item_id, "tab": "work"})
        self.assertEqual(out["item_id"], item_id)
        self.assertIsNotNone(out["explanation"])
        self.assertEqual(out["explanation"]["rank"], 1)
        self.assertEqual(out["explanation"]["of"], 2)

    def test_explain_by_window_item_id(self):
        # Explain using the window item id
        out = self.call("executive_window.explain", {"item_id": "item-high", "tab": "work"})
        self.assertEqual(out["item_id"], "item-high")
        self.assertIsNotNone(out["explanation"])
        self.assertEqual(out["explanation"]["rank"], 1)
        self.assertEqual(out["explanation"]["of"], 2)

    def test_explain_unknown_id_returns_null_explanation(self):
        out = self.call("executive_window.explain", {"item_id": "unknown-id", "tab": "work"})
        self.assertEqual(out["item_id"], "unknown-id")
        self.assertIsNone(out["explanation"])
        self.assertFalse(out.get("isError", False))

    def test_next_without_tab_parameter(self):
        out = self.call("executive_window.next", {})
        self.assertIsNotNone(out["next"])
        self.assertEqual(out["why"]["rank"], 1)
        self.assertEqual(out["why"]["of"], 2)

    def test_explain_without_tab_parameter(self):
        # Explain without tab parameter should still work
        out = self.call("executive_window.explain", {"item_id": "item-high"})
        self.assertIsNotNone(out["explanation"])
        self.assertEqual(out["explanation"]["rank"], 1)


if __name__ == "__main__":
    unittest.main()
