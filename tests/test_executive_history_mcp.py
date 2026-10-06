from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import mcp_server
from agent_os.executive.event_bus import EventBus


class ExecutiveHistoryMcpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.bus = EventBus(Path(self.tmp.name) / "events")
        entity_id = "ex-task-0123456789abcdef"
        self.bus.publish("task.created", "test", "created-1", {"entity_id": entity_id}, subject=entity_id)
        self.bus.publish("task.cancelled", "test", "cancelled-1", {"entity_id": entity_id}, subject=entity_id)
        self.queue_items = [{
            "id": "qi-0123456789abcdef",
            "entity_id": entity_id,
            "provider": "test",
            "source": "test",
            "status": "cancelled",
            "window_item": {"id": "window-item-1", "title": "Private window title"},
        }]
        self.queue_patch = patch.object(mcp_server, "_window_queue", return_value={"queue_items": self.queue_items, "errors": []})
        self.bus_patch = patch.object(mcp_server, "_routing_event_bus", return_value=self.bus)
        self.queue_patch.start()
        self.bus_patch.start()
        self.addCleanup(self.queue_patch.stop)
        self.addCleanup(self.bus_patch.stop)

    def rpc(self, method, params=None):
        return mcp_server._handle_mcp({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}, mcp_server.methods())["result"]

    def call(self, arguments):
        result = self.rpc("tools/call", {"name": "executive_window.history", "arguments": arguments})
        self.assertFalse(result["isError"], result)
        return result["content"][0]["text"]

    def test_tool_is_listed_with_explain_schema(self):
        tools = {tool["name"]: tool for tool in self.rpc("tools/list")["tools"]}
        self.assertIn("executive_window.history", tools)
        self.assertEqual(tools["executive_window.history"]["inputSchema"], tools["executive_window.explain"]["inputSchema"])
        self.assertEqual(tools["executive_window.history"]["description"], "Executive window: provenance history of an outstanding item — identifiers-only Event Bus lifecycle events (created, deferred, completed, cancelled) with persisted route decisions, current status and deferral count. Read-only; local data only.")

    def test_history_returns_identifiers_only_lifecycle_and_unknown_is_null(self):
        encoded = self.call({"item_id": "window-item-1", "tab": "work"})
        out = json.loads(encoded)
        self.assertEqual([event["type"] for event in out["provenance"]["history"]], ["task.created", "task.cancelled"])
        self.assertNotIn("Private window title", encoded)

        unknown = json.loads(self.call({"item_id": "unknown-item"}))
        self.assertIsNone(unknown["provenance"])


if __name__ == "__main__":
    unittest.main()
