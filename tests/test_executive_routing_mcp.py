from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import mcp_server


class RoutingMCPTests(unittest.TestCase):
    def test_tools_are_listed_and_registered(self):
        available = mcp_server.methods()
        response = mcp_server._handle_mcp({"id": 1, "method": "tools/list"}, available)
        listed = {tool["name"]: tool for tool in response["result"]["tools"]}
        self.assertIn("executive_routing.reason", listed)
        self.assertIn("executive_routing.dispatch", listed)
        self.assertEqual(listed["executive_routing.reason"]["inputSchema"]["required"], ["event_id"])
        self.assertIn("executive_routing.dispatch", available)

    def test_reason_uses_local_bus(self):
        bus = object()
        with patch.object(mcp_server, "_routing_event_bus", return_value=bus), patch(
            "agent_os.executive.routing.route_reason", return_value={"disposition": "process"}
        ) as reason:
            self.assertEqual(mcp_server._routing_reason("evt-1"), {"event_id": "evt-1", "route": {"disposition": "process"}})
            reason.assert_called_once_with("evt-1", bus=bus)

    def test_dispatch_previews_by_default_and_dispatches_on_confirmation(self):
        bus = object()
        with patch.object(mcp_server, "_routing_event_bus", return_value=bus), patch(
            "agent_os.executive.routing.preview_pending", return_value=[{"id": "evt-1"}]
        ) as preview, patch("agent_os.executive.routing.dispatch_pending", return_value=[{"id": "evt-2"}]) as dispatch:
            self.assertEqual(mcp_server._routing_dispatch(), {"consumer": "router", "confirm_write": False, "preview": [{"id": "evt-1"}]})
            preview.assert_called_once_with(bus, consumer="router", rules=None)
            self.assertEqual(mcp_server._routing_dispatch("worker", {"x": "process"}, True), {"consumer": "worker", "confirm_write": True, "dispatched": [{"id": "evt-2"}]})
            dispatch.assert_called_once_with(bus, consumer="worker", rules={"x": "process"})

    def test_rejects_non_object_rules(self):
        with self.assertRaisesRegex(ValueError, "rules must be a JSON object"):
            mcp_server._routing_dispatch(rules=["bad"])


if __name__ == "__main__":
    unittest.main()
