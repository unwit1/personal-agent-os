from __future__ import annotations

import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

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
from agent_os.skills import Skill, discover, match
from agent_os.validation import validate


class AgentOSTests(unittest.TestCase):
    def test_registered_project_resolves(self) -> None:
        project = get_project("hr-gui")
        self.assertEqual(project["name"], "HR GUI")
        self.assertEqual(load_state(project)["project"], "hr-gui")
        self.assertEqual(identify_project(Path(project["path"]))["id"], "hr-gui")
        self.assertEqual(identify_project(Path(__file__).resolve())["id"], "personal-agent-os")
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

    def test_skill_matching_fails_closed_on_one_generic_overlap(self) -> None:
        weak = Skill("synthetic-skill", "context", Path("synthetic/SKILL.md"), "synthetic")
        self.assertEqual(match("context", [weak]), [])
        self.assertEqual(match("context", [weak], minimum_score=1), [weak])

    def test_context_compiler_records_and_applies_skill_threshold(self) -> None:
        packet = compile_context("personal-agent-os", "context", token_budget=1200)
        self.assertEqual(packet["matched_skills"], [])
        self.assertEqual(packet["context_policy"]["minimum_skill_score"], 2)

    def test_unrelated_skill_growth_keeps_context_packet_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target_path = root / "compile-project-context" / "SKILL.md"
            target_path.parent.mkdir()
            target_path.write_text("synthetic target skill", encoding="utf-8")

            def synthetic_skills(count: int) -> list[Skill]:
                target = Skill(
                    "compile-project-context",
                    "compile project context",
                    target_path,
                    "synthetic",
                )
                unrelated: list[Skill] = []
                for index in range(count):
                    path = root / f"unrelated-{index}" / "SKILL.md"
                    path.parent.mkdir(exist_ok=True)
                    path.write_text(f"synthetic unrelated marker {index}", encoding="utf-8")
                    unrelated.append(
                        Skill(f"unrelated-{index}", f"synthetic unrelated marker {index}", path, "synthetic")
                    )
                return [target, *unrelated]

            with patch("agent_os.compiler.discover", return_value=synthetic_skills(0)):
                baseline = compile_context("personal-agent-os", "compile project context", token_budget=1200)
            with patch("agent_os.compiler.discover", return_value=synthetic_skills(250)):
                expanded = compile_context("personal-agent-os", "compile project context", token_budget=1200)

            self.assertEqual([item["name"] for item in baseline["matched_skills"]], ["compile-project-context"])
            self.assertEqual([item["name"] for item in expanded["matched_skills"]], ["compile-project-context"])
            self.assertLessEqual(
                expanded["context_measurement"]["estimated_packet_tokens"],
                baseline["context_measurement"]["estimated_packet_tokens"] + 4,
            )
            self.assertGreater(
                expanded["context_measurement"]["naive_all_registered_context_tokens"],
                baseline["context_measurement"]["naive_all_registered_context_tokens"],
            )
            self.assertFalse(expanded["context_policy"]["full_skill_bodies_loaded"])
            self.assertTrue(all("content" not in item for item in expanded["matched_skills"]))

    def test_synthetic_skill_selection_corpus_matches_and_omits_expected_skills(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            definitions = {
                "compile-project-context": "compile project context",
                "scanner-regression": "debug scanner regression",
                "context-budgeter": "budget context tokens",
            }
            synthetic: list[Skill] = []
            for name, description in definitions.items():
                path = root / name / "SKILL.md"
                path.parent.mkdir()
                path.write_text(f"synthetic {description}", encoding="utf-8")
                synthetic.append(Skill(name, description, path, "synthetic"))

            corpus = (
                ("compile project context", ["compile-project-context"]),
                ("scanner regression", ["scanner-regression"]),
                ("context", []),
                ("weather dinner", []),
            )
            for task, expected in corpus:
                with self.subTest(task=task):
                    self.assertEqual([skill.name for skill in match(task, synthetic)], expected)
                    with patch("agent_os.compiler.discover", return_value=synthetic):
                        packet = compile_context("personal-agent-os", task, token_budget=1200)
                    self.assertEqual([item["name"] for item in packet["matched_skills"]], expected)
                    self.assertFalse(packet["context_policy"]["full_skill_bodies_loaded"])
                    self.assertTrue(all("content" not in item for item in packet["matched_skills"]))

    def test_canonical_skills_have_no_deterministic_invocation_entrypoint(self) -> None:
        skills = discover()
        self.assertTrue(skills)
        for skill in skills:
            with self.subTest(skill=skill.name):
                self.assertEqual(skill.path.name, "SKILL.md")
                files = [path.name for path in skill.path.parent.iterdir() if path.is_file()]
                self.assertEqual(files, ["SKILL.md"])

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
