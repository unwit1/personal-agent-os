from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import mcp_server


class ProjectActionsMcpTests(unittest.TestCase):
    def setUp(self):
        self.available = mcp_server.methods()
        # Keep deferral counts off the real local Event Bus unless a test patches it.
        bus = patch.object(mcp_server, "_routing_event_bus", side_effect=RuntimeError("no bus in tests"))
        bus.start()
        self.addCleanup(bus.stop)

    def with_projects(self, states, name, arguments):
        """Call a tool with the registry patched to the given {project_id: state} map."""
        entries = [{"id": pid, "state_file": f"{pid}.json"} for pid in states]

        def load_state(entry):
            state = states[entry["id"]]
            if isinstance(state, Exception):
                raise state
            return state

        def get_project(project_id):
            if project_id not in states:
                raise KeyError(project_id)
            return {"id": project_id, "state_file": f"{project_id}.json"}

        with patch.object(mcp_server, "canonical_projects", return_value=entries),                 patch.object(mcp_server, "get_project", side_effect=get_project),                 patch.object(mcp_server, "load_state", side_effect=load_state):
            return self.call(name, arguments)

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
        self.assertIn("Unknown project", result["content"][0]["text"])

    def test_projects_without_state_file(self):
        entry = {"id": "no-state", "name": "No State"}
        with patch.object(mcp_server, "get_project", return_value=entry):
            result = self.rpc("tools/call", {"name": "executive_projects.next", "arguments": {"project": "no-state"}})
        self.assertTrue(result["isError"])
        self.assertIn("has no state file", result["content"][0]["text"])
        with patch.object(mcp_server, "canonical_projects", return_value=[entry]),                 patch.object(mcp_server, "load_state", side_effect=AssertionError("must not load")):
            result = self.call("executive_projects.scan", {})
        self.assertEqual(result["projects"], [])
        self.assertEqual(result["errors"], [])

    def test_projects_next_with_patched_registry(self):
        state = {
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
            "updated_at": "2026-10-01T00:00:00Z",
        }
        result = self.with_projects({"test-proj": state}, "executive_projects.next", {"project": "test-proj"})
        self.assertEqual(result["project"], "test-proj")
        self.assertEqual(result["status"], "active")
        self.assertEqual(result["goal"], "Test goal")
        self.assertEqual(result["next_action"], "Complete implementation")
        self.assertIn("blocked", result["flags"])

    def test_projects_next_with_custom_stale_days(self):
        state = {"project": "test-proj", "status": "active", "updated_at": "2026-09-01T00:00:00Z"}
        result = self.with_projects(
            {"test-proj": state}, "executive_projects.next", {"project": "test-proj", "stale_days": 20}
        )
        self.assertEqual(result["project"], "test-proj")
        self.assertIn("stalled", result["flags"])

    def test_projects_scan_include_inactive(self):
        states = {
            "proj1": {"project": "proj1", "status": "active", "goal": "Goal 1", "next_action": "Action 1"},
            "proj2": {"project": "proj2", "status": "inactive", "goal": "Goal 2", "next_action": "Action 2"},
        }
        for arguments, expected in (({}, ["proj1"]), ({"include_inactive": True}, ["proj1", "proj2"])):
            with self.subTest(arguments=arguments):
                result = self.with_projects(states, "executive_projects.scan", arguments)
                self.assertEqual([p["project"] for p in result["projects"]], expected)
                self.assertEqual(result["errors"], [])

    def test_projects_scan_with_load_error(self):
        states = {
            "proj1": {"project": "proj1", "status": "active", "goal": "Goal 1"},
            "proj2": ValueError("File not found"),
        }
        result = self.with_projects(states, "executive_projects.scan", {})
        self.assertEqual(len(result["projects"]), 1)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["project"], "proj2")

    def test_projects_scan_stalled_and_flags_with_stale_days(self):
        states = {
            "stale-proj": {"project": "stale-proj", "status": "active", "goal": "Old goal",
                           "updated_at": "2026-09-01T00:00:00Z"},
            "decision-proj": {"project": "decision-proj", "status": "active", "goal": "Goal needing decisions",
                              "next_action": "Need to decide on approach",
                              "decisions_needed": ["Decide on approach", "Choose implementation path"],
                              "updated_at": "2026-10-01T00:00:00Z"},
            "no-action-proj": {"project": "no-action-proj", "status": "active",
                               "goal": "Goal without next action", "updated_at": "2026-10-03T00:00:00Z"},
        }
        result = self.with_projects(states, "executive_projects.scan", {"stale_days": 20})
        self.assertEqual(result["stale_days"], 20)
        self.assertIn("stale-proj", result["stalled"])
        self.assertIn("decision-proj", result["needs_decision"])
        self.assertIn("no-action-proj", result["no_next_action"])
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

    def test_projects_scan_reports_repeated_deferrals(self):
        state = {"project": "deferred-proj", "status": "active", "next_action": "Write tests"}
        with (
            patch.object(mcp_server, "canonical_projects", return_value=[{"id": "deferred-proj", "state_file": "state.json"}]),
            patch.object(mcp_server, "load_state", return_value=state),
            patch.object(mcp_server, "_routing_event_bus", return_value=object()),
            patch("agent_os.executive.window_queue.project_deferral_counts", return_value={"deferred-proj": 3}),
        ):
            result = self.call("executive_projects.scan", {})
        self.assertEqual(result["repeatedly_deferred"], ["deferred-proj"])

    def test_projects_next_reports_repeated_deferrals(self):
        state = {"project": "deferred-proj", "status": "active", "next_action": "Write tests"}
        with (
            patch.object(mcp_server, "get_project", return_value={"id": "deferred-proj", "state_file": "state.json"}),
            patch.object(mcp_server, "load_state", return_value=state),
            patch.object(mcp_server, "_routing_event_bus", return_value=object()),
            patch("agent_os.executive.window_queue.project_deferral_counts", return_value={"deferred-proj": 3}),
        ):
            result = self.call("executive_projects.next", {"project": "deferred-proj"})
        self.assertEqual(result["deferrals"], 3)
        self.assertIn("repeatedly_deferred", result["flags"])

    def test_project_deferral_count_failure_defaults_to_empty(self):
        with (
            patch.object(mcp_server, "canonical_projects", return_value=[{"id": "deferred-proj", "state_file": "state.json"}]),
            patch.object(mcp_server, "load_state", return_value={"project": "deferred-proj", "status": "active"}),
            patch.object(mcp_server, "_routing_event_bus", side_effect=RuntimeError("unavailable")),
        ):
            result = self.call("executive_projects.scan", {})
        self.assertEqual(result["repeatedly_deferred"], [])


if __name__ == "__main__":
    unittest.main()
