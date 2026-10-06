"""Tests for EXEC-1 per-project Next Action Engine documentation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from agent_os.executive.window import actions_projects
from agent_os.executive.window.registry import Registry

EXEC_PROJECT_ACTIONS_DOC = PROJECT_ROOT / "docs" / "orchestrator-os" / "executive-project-actions.md"
EXEC_WINDOW_DOC = PROJECT_ROOT / "docs" / "orchestrator-os" / "executive-window.md"


class TestExecutiveProjectActionsDocumentation(unittest.TestCase):
    """Validate that executive-project-actions.md covers the engine, CLI, MCP tools and window actions."""

    @classmethod
    def setUpClass(cls):
        cls.content = EXEC_PROJECT_ACTIONS_DOC.read_text(encoding="utf-8")
        cls.window_content = EXEC_WINDOW_DOC.read_text(encoding="utf-8")

    def assert_terms(self, content, terms):
        for term in terms:
            with self.subTest(term=term):
                self.assertIn(term, content)

    def test_doc_describes_engine_functions_and_fields(self):
        self.assert_terms(self.content, (
            "`project_next_action(", "`scan(", "decisions_needed", "delegable_work",
            "vague_next_action", "suggested_next_action", "is_vague_action", "STALE_DAYS_DEFAULT",
        ))

    def test_doc_describes_cli_commands_and_mcp_tools(self):
        self.assert_terms(self.content, (
            "agent-os executive project-next", "agent-os executive project-scan",
            "--stale-days", "--today YYYY-MM-DD", "--all",
            "executive_projects.next", "executive_projects.scan", "include_inactive",
        ))

    def test_doc_describes_executive_window_actions(self):
        self.assert_terms(self.content, (
            "project.resume", "project.set_next_action", "project.resolve_decision", "decisions_resolved", "Confirm",
        ))

    def test_doc_lists_every_item_kind_each_window_action_applies_to(self):
        reg = Registry()
        actions_projects.register(reg)
        for action in reg.actions():
            line = next(line for line in self.content.splitlines() if f"**`{action['id']}`**" in line)
            for kind in action["applies_to"]:
                with self.subTest(action=action["id"], kind=kind):
                    self.assertIn(f"`{kind}`", line)

    def test_doc_describes_repeated_deferrals(self):
        self.assert_terms(self.content, (
            "repeatedly_deferred", "REPEATED_DEFERRAL_THRESHOLD", "project_deferral_counts", "task.deferred",
        ))

    def test_executive_window_links_to_project_actions_doc(self):
        self.assertIn("executive-project-actions.md", self.window_content)

    def test_both_docs_describe_repeatedly_deferred_window_item(self):
        for content in (self.window_content, self.content):
            self.assertIn("project_repeatedly_deferred", content)


if __name__ == "__main__":
    unittest.main()
