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


class WindowMcpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict(os.environ, {"AGENT_OS_EXECUTIVE_WINDOW_HOME": self.tmp.name})
        env.start()
        self.addCleanup(env.stop)
        self.reg = window_registry.Registry()
        self.calls = []
        self.reg.register_provider("synthetic", lambda: [
            {"id": "syn-1", "tab": "work", "kind": "synthetic", "title": "T", "why": "w", "source": "test"}])

        def handler(item, params, confirm=False):
            self.calls.append(confirm)
            return {"preview": item["id"]}

        self.reg.register_action("synthetic.send", "Synthetic send", ["synthetic"], handler, True)
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

    def test_run_schema_enum_and_no_confirm_tool(self):
        tools = {t["name"]: t for t in self.rpc("tools/list")["tools"]}
        run = tools["executive_window.run"]
        self.assertIn("synthetic.send", run["inputSchema"]["properties"]["action_id"]["enum"])
        self.assertIn("synthetic.send", run["description"])
        self.assertFalse([n for n in tools if "confirm" in n.lower()])

    def test_consequential_run_returns_token_and_never_confirms(self):
        out = self.call("executive_window.run", {"action_id": "synthetic.send", "item_id": "syn-1"})
        self.assertEqual(out["status"], "needs_confirmation")
        self.assertTrue(out["confirm_token"])
        self.assertTrue(self.calls)
        self.assertNotIn(True, self.calls)

    def test_outstanding_actions_and_unknown_item(self):
        out = self.call("executive_window.outstanding", {"tab": "work"})
        self.assertEqual([o["action_id"] for o in out["items"][0]["options"]], ["synthetic.send"])
        self.assertEqual(self.call("executive_window.outstanding", {"tab": "personal"})["items"], [])
        self.assertEqual(self.call("executive_window.actions", {})["actions"][0]["id"], "synthetic.send")
        bad = self.rpc("tools/call", {"name": "executive_window.run", "arguments": {"action_id": "synthetic.send", "item_id": "nope"}})
        self.assertTrue(bad["isError"])


if __name__ == "__main__":
    unittest.main()
