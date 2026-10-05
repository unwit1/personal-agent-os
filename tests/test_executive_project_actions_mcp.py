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

    def test_projects_scan_stalled_and_flags_with_stale_days(self):
        # Test with an old updated_at and custom stale_days to verify stalled flag
        # and that stale_days is passed through correctly
        proj_stale = {
            "project": "stale-proj",
            "status": "active",
            "goal": "Old goal",
            "updated_at": "2026-09-01T00:00:00Z"  # 34 days old (relative to 2026-10-05)
        }
        proj_with_decisions = {
            "project": "decision-proj",
            "status": "active",
            "goal": "Goal needing decisions",
            "next_action": "Need to decide on approach",
            "decisions_needed": ["Decide on approach", "Choose implementation path"],
            "updated_at": "2026-10-01T00:00:00Z"
        }
        proj_no_next_action = {
            "project": "no-action-proj",
            "status": "active",
            "goal": "Goal without next action",
            "updated_at": "2026-10-03T00:00:00Z"
        }

        def mock_canonical_projects():
            return [
                {"id": "stale-proj", "name": "Stale Project", "state_file": "stale_proj.json"},
                {"id": "decision-proj", "name": "Decision Project", "state_file": "decision_proj.json"},
                {"id": "no-action-proj", "name": "No Action Project", "state_file": "no_action_proj.json"}
            ]

        def mock_load_state(project):
            if project.get("id") == "stale-proj":
                return proj_stale
            elif project.get("id") == "decision-proj":
                return proj_with_decisions
            elif project.get("id") == "no-action-proj":
                return proj_no_next_action
            raise ValueError(f"Unknown project: {project}")

        with patch.object(mcp_server, "canonical_projects", side_effect=mock_canonical_projects):
            with patch.object(mcp_server, "load_state", side_effect=mock_load_state):
                result = self.call("executive_projects.scan", {"stale_days": 20})
                # Verify stale_days is passed through
                self.assertEqual(result["stale_days"], 20)
                # Verify stalled list contains the old project
                self.assertIn("stale-proj", result["stalled"])
                # Verify needs_decision list contains the project with decisions
                self.assertIn("decision-proj", result["needs_decision"])
                # Verify no_next_action list contains the project without next action
                self.assertIn("no-action-proj", result["no_next_action"])
                # Verify we have 3 projects in results
                self.assertEqual(len(result["projects"]), 3)

    def test_projects_next_with_vague_action(self):
        synthetic_state = {
            "project": "test-proj",
            "status": "active",
            "goal": "Test goal",
            "next_action": "TBD",
            "current_priorities": ["Write unit tests", "Review docs"],
            "updated_at": "2026-10-01T00:00:00Z"
        }

        def mock_get_project(project_id):
            return {"id": "test-proj", "name": "Test Project", "state_file": "test_state.json"}

        def mock_load_state(project):
            return synthetic_state

        with patch.object(mcp_server, "get_project", side_effect=mock_get_project):
            with patch.object(mcp_server, "load_state", side_effect=mock_load_state):
                result = self.call("executive_projects.next", {"project": "test-proj"})
                self.assertEqual(result["project"], "test-proj")
                self.assertEqual(result["next_action"], "TBD")
                self.assertIn("vague_next_action", result["flags"])
                self.assertEqual(result["suggested_next_action"], "Write unit tests")

    def test_projects_scan_with_vague_next_action(self):
        proj_vague = {
            "project": "vague-proj",
            "status": "active",
            "next_action": "Work on project X",
            "current_priorities": [],
            "delegable_work": ["Write tests", "Review code"],
            "updated_at": "2026-10-05T00:00:00Z"
        }
        proj_specific = {
            "project": "specific-proj",
            "status": "active",
            "next_action": "Write tests",
            "updated_at": "2026-10-05T00:00:00Z"
        }

        def mock_canonical_projects():
            return [
                {"id": "vague-proj", "name": "Vague Project", "state_file": "vague_proj.json"},
                {"id": "specific-proj", "name": "Specific Project", "state_file": "specific_proj.json"}
            ]

        def mock_load_state(project):
            if project.get("id") == "vague-proj":
                return proj_vague
            elif project.get("id") == "specific-proj":
                return proj_specific
            raise ValueError(f"Unknown project: {project}")

        with patch.object(mcp_server, "canonical_projects", side_effect=mock_canonical_projects):
            with patch.object(mcp_server, "load_state", side_effect=mock_load_state):
                result = self.call("executive_projects.scan", {})
                self.assertIn("vague_next_action", result)
                self.assertEqual(result["vague_next_action"], ["vague-proj"])
                self.assertEqual(len(result["projects"]), 2)


if __name__ == "__main__":
    unittest.main()
