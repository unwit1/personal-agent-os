from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.project_gaps import FACTORS, project_gaps
from agent_os.executive.knowledge_gaps import select_questions


class ProjectGapsTests(unittest.TestCase):
    def test_complete_active_state_has_no_gaps(self):
        state = {
            "project": "alpha", "status": "active", "goal": "Ship", "next_action": "Build",
            "blockers": [],
        }
        self.assertEqual(project_gaps([state]), [])

    def test_missing_fields_emit_expected_gaps(self):
        gaps = project_gaps([{"project": "alpha", "status": "active"}])
        self.assertEqual([gap["id"] for gap in gaps], [
            "project-gap:alpha:goal", "project-gap:alpha:next_action", "project-gap:alpha:blockers",
        ])
        self.assertEqual([gap["question"] for gap in gaps], [
            "What is the goal of project alpha?",
            "What is the next concrete action for project alpha?",
            "Is anything blocking project alpha? (list blockers, or none)",
        ])
        for gap, field in zip(gaps, ("goal", "next_action", "blockers")):
            self.assertEqual(gap["field"], field)
            self.assertEqual(gap["topic"], f"project:{field}")
            self.assertEqual(gap["source"], "project_state")
            self.assertEqual({key: gap[key] for key in FACTORS[field]}, FACTORS[field])

    def test_summary_and_priority_satisfy_goal_and_next_action(self):
        state = {"project": "alpha", "status": "active", "summary": "Ship", "current_priorities": ["Build"], "blockers": []}
        self.assertEqual(project_gaps([state]), [])

    def test_empty_blockers_are_known_none(self):
        state = {"project": "alpha", "status": "active", "blockers": []}
        self.assertNotIn("blockers", [gap["field"] for gap in project_gaps([state])])

    def test_inactive_is_optional(self):
        state = {"project": "alpha", "status": "paused"}
        self.assertEqual(project_gaps([state]), [])
        self.assertEqual(len(project_gaps([state], include_inactive=True)), 3)

    def test_invalid_states_are_skipped(self):
        self.assertEqual(project_gaps([None, {}, {"project": ""}, {"project": "  "}]), [])

    def test_output_is_deterministic_and_sorted(self):
        states = [{"project": "zeta", "status": "active"}, {"project": "alpha", "status": "active"}]
        first = project_gaps(states)
        self.assertEqual(first, project_gaps(states))
        self.assertEqual([gap["project"] for gap in first], ["alpha"] * 3 + ["zeta"] * 3)

    def test_each_gap_is_selected_with_default_threshold(self):
        gaps = project_gaps([{"project": "alpha", "status": "active"}])
        result = select_questions(gaps, budget=10)
        self.assertEqual({item["id"] for item in result["ask"]}, {gap["id"] for gap in gaps})
        self.assertTrue(all(item["score"] >= 0.2 for item in result["ask"]))


if __name__ == "__main__":
    unittest.main()
