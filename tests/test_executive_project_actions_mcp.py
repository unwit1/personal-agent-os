from __future__ import annotations

import json
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import mcp_server


class ProjectActionsMcpTests(unittest.TestCase):
    def setUp(self):
        self.available = mcp_server.methods()

    def rpc(self, method, params=None):
        response = mcp_server._handle_mcp({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}, self.available)
        return response["result"]

    def call(self, name, arguments):
        result = self.rpc("tools/call", {"name": name, "arguments": arguments})
        self.assertFalse(result["isError"], result)
        return json.loads(result["content"][0]["text"])

    def test_tools_in_list(self):
        tools = {t["name"]: t for t in self.rpc("tools/list")["tools"]}
        self.assertIn("executive_projects.next", tools)
        self.assertIn("executive_projects.scan", tools)
        self.assertEqual(tools["executive_projects.next"]["inputSchema"]["required"], ["project"])
        self.assertIn("stale_days", tools["executive_projects.next"]["inputSchema"]["properties"])
        self.assertIn("stale_days", tools["executive_projects.scan"]["inputSchema"]["properties"])
        self.assertIn("include_inactive", tools["executive_projects.scan"]["inputSchema"]["properties"])

    def test_projects_next_with_unknown_project(self):
        result = self.rpc("tools/call", {"name": "executive_projects.next", "arguments": {"project": "nonexistent-project-xyz"}})
        self.assertTrue(result["isError"])

    def test_projects_next_with_patched_registry(self):
        synthetic_state = {
            "project": "test-proj",
            "status": "active",
            "goal": "Test goal",
            "summary": "Test summary",
            "current_state": "In progress",
            "next_action": "Complete implementation",
            "current_priorities": ["Priority 1"],
            "blockers": ["Blocker 1"],
            "waiting_on": ["Waiting 1"],
            "decisions_needed": ["Decision 1"],
            "delegable_work": ["Work 1"],
            "updated_at": "2026-10-01T00:00:00Z"
        }

        def mock_get_project(project_id):
            if project_id == "test-proj":
                return {"id": "test-proj", "name": "Test Project", "state_file": "test_state.json"}
            raise KeyError(f"Unknown project: {project_id}")

        def mock_load_state(project):
            return synthetic_state

        with patch.object(mcp_server, "get_project", side_effect=mock_get_project):
            with patch.object(mcp_server, "load_state", side_effect=mock_load_state):
                result = self.call("executive_projects.next", {"project": "test-proj"})
                self.assertEqual(result["project"], "test-proj")
                self.assertEqual(result["status"], "active")
                self.assertEqual(result["goal"], "Test goal")
                self.assertEqual(result["next_action"], "Complete implementation")
                self.assertIn("blocked", result["flags"])

    def test_projects_next_with_custom_stale_days(self):
        synthetic_state = {
            "project": "test-proj",
            "status": "active",
            "updated_at": "2026-09-01T00:00:00Z"
        }

        def mock_get_project(project_id):
            return {"id": "test-proj", "name": "Test Project", "state_file": "test_state.json"}

        def mock_load_state(project):
            return synthetic_state

        with patch.object(mcp_server, "get_project", side_effect=mock_get_project):
            with patch.object(mcp_server, "load_state", side_effect=mock_load_state):
                result = self.call("executive_projects.next", {"project": "test-proj", "stale_days": 20})
                self.assertEqual(result["project"], "test-proj")
                self.assertIn("stalled", result["flags"])

    def test_projects_scan_with_patched_registry(self):
        proj1_state = {
            "project": "proj1",
            "status": "active",
            "goal": "Goal 1",
            "next_action": "Action 1",
            "updated_at": "2026-10-01T00:00:00Z"
        }
        proj2_state = {
            "project": "proj2",
            "status": "inactive",
            "goal": "Goal 2",
            "next_action": "Action 2",
            "updated_at": "2026-10-01T00:00:00Z"
        }

        def mock_canonical_projects():
            return [
                {"id": "proj1", "name": "Project 1", "state_file": "proj1_state.json"},
                {"id": "proj2", "name": "Project 2", "state_file": "proj2_state.json"}
            ]

        def mock_load_state(project):
            if project.get("id") == "proj1":
                return proj1_state
            elif project.get("id") == "proj2":
                return proj2_state
            raise ValueError(f"Unknown project: {project}")

        with patch.object(mcp_server, "canonical_projects", side_effect=mock_canonical_projects):
            with patch.object(mcp_server, "load_state", side_effect=mock_load_state):
                result = self.call("executive_projects.scan", {})
                self.assertEqual(len(result["projects"]), 1)
                self.assertEqual(result["projects"][0]["project"], "proj1")
                self.assertIn("errors", result)

    def test_projects_scan_include_inactive(self):
        proj1_state = {
            "project": "proj1",
            "status": "active",
            "goal": "Goal 1",
            "updated_at": "2026-10-01T00:00:00Z"
        }
        proj2_state = {
            "project": "proj2",
            "status": "inactive",
            "goal": "Goal 2",
            "updated_at": "2026-10-01T00:00:00Z"
        }

        def mock_canonical_projects():
            return [
                {"id": "proj1", "name": "Project 1", "state_file": "proj1_state.json"},
                {"id": "proj2", "name": "Project 2", "state_file": "proj2_state.json"}
            ]

        def mock_load_state(project):
            if project.get("id") == "proj1":
                return proj1_state
            elif project.get("id") == "proj2":
                return proj2_state
            raise ValueError(f"Unknown project: {project}")

        with patch.object(mcp_server, "canonical_projects", side_effect=mock_canonical_projects):
            with patch.object(mcp_server, "load_state", side_effect=mock_load_state):
                result = self.call("executive_projects.scan", {"include_inactive": True})
                self.assertEqual(len(result["projects"]), 2)

    def test_projects_scan_with_load_error(self):
        proj1_state = {
            "project": "proj1",
            "status": "active",
            "goal": "Goal 1",
            "updated_at": "2026-10-01T00:00:00Z"
        }

        def mock_canonical_projects():
            return [
                {"id": "proj1", "name": "Project 1", "state_file": "proj1_state.json"},
                {"id": "proj2", "name": "Project 2", "state_file": "proj2_state.json"}
            ]

        def mock_load_state(project):
            if project.get("id") == "proj1":
                return proj1_state
            elif project.get("id") == "proj2":
                raise ValueError("File not found")
            raise ValueError(f"Unknown project: {project}")

        with patch.object(mcp_server, "canonical_projects", side_effect=mock_canonical_projects):
            with patch.object(mcp_server, "load_state", side_effect=mock_load_state):
                result = self.call("executive_projects.scan", {})
                self.assertEqual(len(result["projects"]), 1)
                self.assertEqual(len(result["errors"]), 1)
                self.assertEqual(result["errors"][0]["project"], "proj2")


if __name__ == "__main__":
    unittest.main()
