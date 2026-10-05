"""Tests for EXEC-1 per-project Next Action Engine documentation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXEC_PROJECT_ACTIONS_DOC = PROJECT_ROOT / "docs" / "orchestrator-os" / "executive-project-actions.md"
EXEC_WINDOW_DOC = PROJECT_ROOT / "docs" / "orchestrator-os" / "executive-window.md"


class TestExecutiveProjectActionsDocumentation(unittest.TestCase):
    """Validate that executive-project-actions.md exists and contains required content."""

    def test_doc_exists(self):
        """The documentation file should exist."""
        self.assertTrue(
            EXEC_PROJECT_ACTIONS_DOC.exists(),
            f"Documentation file not found: {EXEC_PROJECT_ACTIONS_DOC}"
        )

    def test_doc_contains_project_next_action(self):
        """The documentation should mention project_next_action function."""
        content = EXEC_PROJECT_ACTIONS_DOC.read_text(encoding="utf-8")
        self.assertIn("project_next_action", content)

    def test_doc_contains_scan(self):
        """The documentation should mention scan function."""
        content = EXEC_PROJECT_ACTIONS_DOC.read_text(encoding="utf-8")
        self.assertIn("scan", content)

    def test_doc_contains_project_next_cli_command(self):
        """The documentation should mention project-next CLI command."""
        content = EXEC_PROJECT_ACTIONS_DOC.read_text(encoding="utf-8")
        self.assertIn("project-next", content)

    def test_doc_contains_project_scan_cli_command(self):
        """The documentation should mention project-scan CLI command."""
        content = EXEC_PROJECT_ACTIONS_DOC.read_text(encoding="utf-8")
        self.assertIn("project-scan", content)

    def test_doc_contains_executive_projects_next_mcp_tool(self):
        """The documentation should mention executive_projects.next MCP tool."""
        content = EXEC_PROJECT_ACTIONS_DOC.read_text(encoding="utf-8")
        self.assertIn("executive_projects.next", content)

    def test_doc_contains_executive_projects_scan_mcp_tool(self):
        """The documentation should mention executive_projects.scan MCP tool."""
        content = EXEC_PROJECT_ACTIONS_DOC.read_text(encoding="utf-8")
        self.assertIn("executive_projects.scan", content)

    def test_doc_contains_decisions_needed(self):
        """The documentation should mention decisions_needed field."""
        content = EXEC_PROJECT_ACTIONS_DOC.read_text(encoding="utf-8")
        self.assertIn("decisions_needed", content)

    def test_doc_contains_delegable_work(self):
        """The documentation should mention delegable_work field."""
        content = EXEC_PROJECT_ACTIONS_DOC.read_text(encoding="utf-8")
        self.assertIn("delegable_work", content)

    def test_doc_describes_vague_next_action(self):
        """The documentation should describe vague action detection and suggestions."""
        content = EXEC_PROJECT_ACTIONS_DOC.read_text(encoding="utf-8")
        self.assertIn("vague_next_action", content)
        self.assertIn("suggested_next_action", content)
        self.assertIn("is_vague_action", content)

    def test_open_section_keeps_repeated_deferral(self):
        """Repeated deferral remains open and identifies its undecided data source."""
        content = EXEC_PROJECT_ACTIONS_DOC.read_text(encoding="utf-8")
        open_section = content.split("## Open", 1)[1]
        self.assertIn("Repeated-deferral", open_section)
        self.assertIn("deferral-history source", open_section)

    def test_executive_window_links_to_project_actions_doc(self):
        """executive-window.md should link to executive-project-actions.md."""
        content = EXEC_WINDOW_DOC.read_text(encoding="utf-8")
        self.assertIn("executive-project-actions.md", content)


if __name__ == "__main__":
    unittest.main()
