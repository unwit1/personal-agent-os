"""Planned task goals are never truncated; over-long ones fail planning."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator.model import MAX_GOAL_CHARS, PlanError, new_node  # noqa: E402
from agent_os.orchestrator.planner import node_from_task  # noqa: E402


class PlannerGoalLengthTests(unittest.TestCase):
    def test_long_planned_goal_is_kept_whole(self) -> None:
        goal = "Implement the spec. " + "x" * 5000 + " END-OF-SPEC"
        node = node_from_task({"id": "t1", "goal": goal, "scope": ["src/a.py"]})
        self.assertEqual(node["goal"], goal.strip())
        self.assertTrue(node["goal"].endswith("END-OF-SPEC"))

    def test_over_long_planned_goal_fails_planning(self) -> None:
        with self.assertRaises(PlanError) as caught:
            node_from_task({"id": "t2", "goal": "y" * (MAX_GOAL_CHARS + 1), "scope": ["src/a.py"]})
        self.assertIn("split", str(caught.exception))

    def test_engine_built_goals_are_not_truncated(self) -> None:
        goal = "Repair review findings on t1: " + "z" * MAX_GOAL_CHARS
        self.assertEqual(new_node("t1.repair1", goal, "repairer")["goal"], goal)


if __name__ == "__main__":
    unittest.main()
