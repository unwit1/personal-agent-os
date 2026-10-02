"""Test that shared_prefix optimization preserves all required prompt sections."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import unittest
from unittest.mock import patch
from collections import Counter

from agent_os.orchestrator import prompts, context_anatomy


class PromptSectionsParityTests(unittest.TestCase):
    """Verify workers receive every rule they get today with shared_prefix enabled."""

    def _make_run(self, goal: str, shared_prefix: bool = False, operator_messages=None):
        """Create a minimal run record."""
        return {
            "run_id": "test-run",
            "goal": goal,
            "project": None,
            "policy": {"shared_prefix": shared_prefix},
            "nodes": {},
            "operator_messages": operator_messages or []
        }

    def _make_node(self, role: str, node_id: str, goal: str, scope=None):
        """Create a minimal node for the given role."""
        return {
            "id": node_id,
            "role": role,
            "goal": goal,
            "scope": scope or ["src/", "tests/"],
            "context_budget": 1200,
            "validators": []
        }

    def _assert_prompt_parity(self, role: str, prompt_off: str, prompt_on: str):
        """Assert that off and on prompts have the same content."""
        # Count non-empty lines
        off_lines = [line for line in prompt_off.splitlines() if line.strip()]
        on_lines = [line for line in prompt_on.splitlines() if line.strip()]

        off_counter = Counter(off_lines)
        on_counter = Counter(on_lines)

        self.assertEqual(off_counter, on_counter,
                        f"{role}: non-empty line counters differ.\n"
                        f"Off only: {off_counter - on_counter}\n"
                        f"On only: {on_counter - off_counter}")

        # Check sections
        sections_off = set(context_anatomy.sections(prompt_off).keys())
        sections_on = set(context_anatomy.sections(prompt_on).keys())

        # Every section in off should be in on
        missing_sections = sections_off - sections_on
        self.assertFalse(missing_sections,
                        f"{role}: sections in off but not in on: {missing_sections}")

        # Check output contract ends
        contract = prompts._contract(role)
        self.assertTrue(prompt_off.endswith(contract),
                       f"{role}: off prompt does not end with correct contract")
        self.assertTrue(prompt_on.endswith(contract),
                       f"{role}: on prompt does not end with correct contract")

    def _test_role_parity(self, role: str, repo_map: str = None, diff: str = None, findings: list = None):
        """Test shared_prefix=True/False parity for a role."""
        goal = f"Test task for {role}"

        # Initialize all variables
        repo_map_arg = None
        diff_arg = None
        findings_arg = None

        # Create node for this role
        if role == "planner":
            node = self._make_node(role, "plan", goal)
            repo_map_arg = repo_map or "Files most relevant:\n- a.py"
        elif role == "reviewer":
            node = self._make_node(role, "task.review", goal)
            diff_arg = diff or "--- a/test.py\n+++ b/test.py\n@@ -1 @@\n+test"
            findings_arg = findings or [{"id": "F1", "severity": "medium", "summary": "test finding"}]
        elif role == "repairer":
            node = self._make_node(role, "task.repair", goal)
            findings_arg = findings or [{"id": "R1", "severity": "medium", "summary": "test finding"}]
        else:
            # implementer or test_author
            node = self._make_node(role, f"task-{role}", goal)

        # Build with shared_prefix=False
        run_off = self._make_run(goal, shared_prefix=False, operator_messages=[{"text": "Test message"}])
        run_off["nodes"] = {node["id"]: node}

        kwargs_off = {}
        if repo_map_arg is not None:
            kwargs_off["repo_map"] = repo_map_arg
        if diff_arg is not None:
            kwargs_off["diff"] = diff_arg
        if findings_arg is not None:
            kwargs_off["findings"] = findings_arg

        prompt_off, _ = prompts.build_measured(run_off, node, cwd="C:\\test", **kwargs_off)

        # Build with shared_prefix=True
        run_on = self._make_run(goal, shared_prefix=True, operator_messages=[{"text": "Test message"}])
        run_on["nodes"] = {node["id"]: node}

        kwargs_on = kwargs_off.copy()
        prompt_on, _ = prompts.build_measured(run_on, node, cwd="C:\\test", **kwargs_on)

        # Assert parity
        self._assert_prompt_parity(role, prompt_off, prompt_on)

    @patch("agent_os.orchestrator.prompts._context_packet", return_value=("Project summary: X\nConstraints:\n- c1", {}))
    def test_planner_parity(self, mock_context):
        """Planner prompts should have same sections with shared_prefix=True/False."""
        self._test_role_parity("planner", repo_map="Files most relevant:\n- a.py")

    @patch("agent_os.orchestrator.prompts._context_packet", return_value=("Project summary: X\nConstraints:\n- c1", {}))
    def test_implementer_parity(self, mock_context):
        """Implementer prompts should have same sections with shared_prefix=True/False."""
        self._test_role_parity("implementer")

    @patch("agent_os.orchestrator.prompts._context_packet", return_value=("Project summary: X\nConstraints:\n- c1", {}))
    def test_test_author_parity(self, mock_context):
        """Test author prompts should have same sections with shared_prefix=True/False."""
        self._test_role_parity("test_author")

    @patch("agent_os.orchestrator.prompts._context_packet", return_value=("Project summary: X\nConstraints:\n- c1", {}))
    def test_reviewer_parity(self, mock_context):
        """Reviewer prompts should have same sections with shared_prefix=True/False."""
        self._test_role_parity("reviewer", diff="--- a/test.py\n+++ b/test.py\n@@ -1 @@\n+test",
                              findings=[{"id": "F1", "severity": "medium", "summary": "test"}])

    @patch("agent_os.orchestrator.prompts._context_packet", return_value=("Project summary: X\nConstraints:\n- c1", {}))
    def test_repairer_parity(self, mock_context):
        """Repairer prompts should have same sections with shared_prefix=True/False."""
        self._test_role_parity("repairer", findings=[{"id": "R1", "severity": "medium", "summary": "test"}])


if __name__ == "__main__":
    unittest.main()
