from __future__ import annotations

import sys
import unittest
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.compiler import compile_context
from agent_os import candidates as candidate_module
from agent_os.candidates import curate_candidates, stage_candidates
from agent_os.chat import context as chat_context
from agent_os.chat import resolve_project
from agent_os.cli import parser
from agent_os.index import rebuild, search
from agent_os.mcp_server import _handle_mcp, methods
from agent_os.inventory import scan
from agent_os.registry import get_project, identify_project, load_state, projects
from agent_os.review import assess
from agent_os.routing import targets
from agent_os.skills import discover, match
from agent_os.validation import validate


class AgentOSTests(unittest.TestCase):
    def test_registered_project_resolves(self) -> None:
        project = get_project("hr-gui")
        self.assertEqual(project["name"], "HR GUI")
        self.assertEqual(load_state(project)["project"], "hr-gui")
        self.assertEqual(identify_project(Path(project["path"]))["id"], "hr-gui")
        self.assertEqual(identify_project(Path(__file__).resolve())["id"], "personal-agent-os")
        self.assertEqual(Path(get_project("personal-agent-os")["path"]).resolve(), Path(__file__).resolve().parents[1])
        self.assertEqual(len({item["id"] for item in projects()}), 7)

    def test_project_inventory_is_fully_registered(self) -> None:
        inventory = scan()
        self.assertEqual(inventory["unregistered"], [])
        dashboard = next(item for item in inventory["projects"] if item["registered_as"] == "job-applicant-dashboard")
        self.assertIn("dashboard.db", dashboard["sensitive_markers"])

    def test_scan_projects_command_parses(self) -> None:
        args = parser().parse_args(["scan-projects"])
        self.assertEqual(args.command, "scan-projects")

    def test_routing_targets_cover_global_and_project_adapters(self) -> None:
        destinations = [str(destination) for _, destination in targets()]
        self.assertEqual(len(destinations), 7)
        self.assertTrue(any(destination.endswith(".codex\\AGENTS.md") for destination in destinations))
        skill = (Path(__file__).resolve().parents[1] / ".agents/skills/personal-agent-os/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("begin-task", skill)
        self.assertIn("finish-task", skill)

    def test_skill_discovery_and_selective_match(self) -> None:
        skills = discover()
        self.assertTrue(any(skill.name == "compile-project-context" for skill in skills))
        matched = match("compile project context", skills)
        self.assertEqual(matched[0].name, "compile-project-context")

        project = get_project("hr-gui")
        state = load_state(project)
        project_skills = discover(Path(project["path"]), state["skill_roots"])
        matched = match("fix scanner two digit year regression", project_skills)
        self.assertTrue(any(skill.name == "scanner-regression" for skill in matched))

    def test_rebuild_and_search(self) -> None:
        result = rebuild()
        self.assertGreater(result["documents"], 3)
        matches = search("scanner", scope="hr-gui")
        self.assertTrue(matches)

    def test_context_compiler_is_focused(self) -> None:
        packet = compile_context("hr-gui", "fix scanner two digit year regression", token_budget=1200)
        self.assertEqual(packet["project"], "hr-gui")
        self.assertFalse(packet["context_policy"]["raw_history_loaded"])
        self.assertFalse(packet["context_policy"]["full_skill_bodies_loaded"])
        self.assertLessEqual(len(packet["matched_skills"]), 3)
        self.assertTrue(packet["context_measurement"]["within_budget"])

    def test_regular_chat_router_avoids_unrelated_context(self) -> None:
        casual = chat_context("What is a good dinner idea?")
        self.assertEqual(casual["activation"], "not_project_related")
        self.assertIsNone(casual["context"])

        resolved = resolve_project("Please review Personal Agent OS context routing")
        self.assertEqual(resolved["project"]["id"], "personal-agent-os")
        packet = chat_context("Why is the JSON RPC stdio server returning an error?", token_budget=550)
        self.assertEqual(packet["project"], "personal-agent-os")
        self.assertLessEqual(packet["context"]["context_measurement"]["estimated_packet_tokens"], 550)

    def test_candidate_writeback_stages_deduplicates_and_requires_curation(self) -> None:
        original_root = candidate_module.ROOT
        scratch_root = Path(__file__).resolve().parents[1] / ".tmp"
        scratch_root.mkdir(exist_ok=True)
        temporary = scratch_root / "candidate-test-root"
        temporary.mkdir(exist_ok=True)
        candidate_module.ROOT = temporary
        try:
            candidate = {
                "kind": "documentation_candidate",
                "statement": f"Document the compact regular-chat context contract {uuid.uuid4()}.",
                "evidence": ["acceptance test"],
                "confidence": 0.9,
            }
            staged = stage_candidates("personal-agent-os", "Reviewed regular chat", [candidate])
            self.assertEqual(len(staged["staged"]), 1)
            duplicate = stage_candidates("personal-agent-os", "Reviewed regular chat", [candidate])
            self.assertEqual(len(duplicate["duplicates"]), 1)
            promoted = curate_candidates("personal-agent-os", [staged["staged"][0]["id"]], action="promote")
            self.assertEqual(promoted["results"][0]["outcome"], "promoted")
            self.assertTrue((temporary / "memory" / "promoted-candidates.json").exists())
        finally:
            candidate_module.ROOT = original_root

    def test_chat_facing_mcp_surface_is_available(self) -> None:
        available = methods()
        for name in ("agent.context", "agent.capture_candidates", "agent.search", "agent.project_status", "agent.skills_match", "agent.latest_handoff"):
            self.assertIn(name, available)

    def test_mcp_initialization_and_tool_discovery(self) -> None:
        available = methods()
        initialized = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}}, available)
        self.assertEqual(initialized["result"]["serverInfo"]["name"], "personal-agent-os")
        tools = _handle_mcp({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, available)
        names = {tool["name"] for tool in tools["result"]["tools"]}
        self.assertIn("agent.context", names)
        self.assertIsNone(_handle_mcp({"jsonrpc": "2.0", "method": "notifications/initialized"}, available))

    def test_review_escalates(self) -> None:
        result = assess(["schemas/memory.schema.json"], architecture_change=True)
        self.assertGreaterEqual(result["review_level"], 2)

    def test_validation(self) -> None:
        result = validate()
        self.assertTrue(result["ok"], result["errors"])


if __name__ == "__main__":
    unittest.main()
