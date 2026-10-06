from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import mcp_server


class CaptureMCPTests(unittest.TestCase):
    def test_tools_are_listed_registered_and_resume_schema_requires_project(self):
        available = mcp_server.methods()
        response = mcp_server._handle_mcp({"id": 1, "method": "tools/list"}, available)
        listed = {tool["name"]: tool for tool in response["result"]["tools"]}
        names = {
            "executive_capture.rescue", "executive_capture.resume",
            "executive_capture.brain_dump", "executive_capture.gaps",
        }
        self.assertTrue(names.issubset(listed))
        self.assertTrue(names.issubset(available))
        self.assertEqual(listed["executive_capture.resume"]["inputSchema"]["required"], ["project"])

    def test_rescue_returns_expected_fields(self):
        with patch.object(mcp_server, "_window_queue", return_value={"queue_items": [], "errors": []}), patch(
            "agent_os.executive.window.rescue_view.project_results", return_value=([], [])
        ):
            result = mcp_server._capture_rescue(today="2026-10-06")
        self.assertTrue({"basis", "action", "why", "then", "suppressed", "errors"}.issubset(result))
        self.assertEqual(result["errors"], [])

    def test_resume_rejects_unknown_project(self):
        with self.assertRaisesRegex(ValueError, "unknown project"):
            mcp_server._capture_resume("definitely-not-a-project-xyz")

    def test_brain_dump_returns_typed_results_and_rejects_empty_text(self):
        result = mcp_server._capture_brain_dump("Call the plumber tomorrow. I decided to use Postgres.")
        self.assertIsInstance(result, dict)
        for key in ("records", "duplicates", "clarifications"):
            self.assertIsInstance(result[key], list)
        self.assertTrue(result["records"])
        with self.assertRaisesRegex(ValueError, "text must be a non-empty string"):
            mcp_server._capture_brain_dump("")

    def test_gaps_selects_with_budget_and_rejects_non_list(self):
        gaps = [
            {"id": "g1", "question": "Q1?", "topic": "t", "utility": 1, "urgency": 1},
            {"id": "g2", "question": "Q2?", "topic": "t", "utility": 1, "urgency": 1},
        ]
        result = mcp_server._capture_gaps(gaps, budget=1)
        self.assertEqual(len(result["ask"]), 1)
        self.assertEqual(result["deferred"][0]["id"], "g2")
        self.assertEqual(result["deferred"][0]["reason"], "over_budget")
        with self.assertRaisesRegex(ValueError, "gaps must be a JSON list"):
            mcp_server._capture_gaps({"x": 1})


if __name__ == "__main__":
    unittest.main()
