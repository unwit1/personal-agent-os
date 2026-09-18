from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.compiler import compile_context
from agent_os.index import rebuild, search
from agent_os.registry import get_project, identify_project, load_state
from agent_os.review import assess
from agent_os.skills import discover, match
from agent_os.validation import validate


class AgentOSTests(unittest.TestCase):
    def test_registered_project_resolves(self) -> None:
        project = get_project("hr-gui")
        self.assertEqual(project["name"], "HR GUI")
        self.assertEqual(load_state(project)["project"], "hr-gui")
        self.assertEqual(identify_project(Path(project["path"]))["id"], "hr-gui")
        self.assertEqual(identify_project(Path(__file__).resolve())["id"], "personal-agent-os")

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
        self.assertLessEqual(len(packet["matched_skills"]), 3)

    def test_review_escalates(self) -> None:
        result = assess(["schemas/memory.schema.json"], architecture_change=True)
        self.assertGreaterEqual(result["review_level"], 2)

    def test_validation(self) -> None:
        result = validate()
        self.assertTrue(result["ok"], result["errors"])


if __name__ == "__main__":
    unittest.main()
