import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.rescue import rescue


TODAY = date(2026, 10, 5)


class RescueTests(unittest.TestCase):
    def test_deadline_basis_uses_rank_order(self):
        items = [
            {"id": "later-ranked", "priority": 1, "window_item": {"due": "2026-10-05", "title": "First"}},
            {"id": "top-ranked", "priority": 5, "window_item": {"due": "2026-10-06T12:00:00", "summary": "Urgent"}},
        ]
        got = rescue(items, [], today=TODAY)
        self.assertEqual(got["basis"], "deadline")
        self.assertEqual(got["action"]["queue_item_id"], "top-ranked")
        self.assertEqual(got["action"]["title"], "Urgent")

    def test_project_basis_and_exactly_one_action(self):
        projects = [{"project": str(i), "status": "active", "flags": [], "next_action": f"Step {i}"} for i in range(8)]
        got = rescue([], projects, today=TODAY)
        self.assertEqual(got["basis"], "project")
        self.assertEqual(got["action"]["project"], "0")
        self.assertEqual(got["suppressed"], 7)
        self.assertEqual(set(got["action"]), {"title", "project", "queue_item_id", "due"})

    def test_vague_suggestion_and_skips_blocked_or_unsuggested(self):
        projects = [
            {"project": "blocked", "status": "active", "flags": ["blocked"], "next_action": "Do it"},
            {"project": "vague", "status": "active", "flags": ["vague_next_action"], "next_action": "Continue", "suggested_next_action": "Write tests"},
            {"project": "unsuggested", "status": "active", "flags": ["vague_next_action"], "next_action": "Continue"},
        ]
        got = rescue([], projects, today=TODAY)
        self.assertEqual(got["action"]["title"], "Write tests")
        self.assertEqual(got["action"]["project"], "vague")

    def test_project_tie_break_is_decision_then_age_then_project(self):
        projects = [
            {"project": "a", "status": "active", "flags": [], "age_days": 1, "next_action": "A"},
            {"project": "z", "status": "active", "flags": ["needs_decision"], "age_days": 0, "next_action": "Z"},
            {"project": "b", "status": "active", "flags": [], "age_days": 3, "next_action": "B"},
        ]
        got = rescue([], projects, today=TODAY)
        self.assertEqual(got["action"]["project"], "a")

    def test_queue_basis_and_single_choice(self):
        items = [{"id": str(i), "priority": i, "window_item": {"title": f"Q{i}"}} for i in range(10)]
        got = rescue(items, [], today=TODAY)
        self.assertEqual(got["basis"], "queue")
        self.assertEqual(got["action"]["queue_item_id"], "9")
        self.assertEqual(got["suppressed"], 9)

    def test_far_or_malformed_due_falls_through_to_queue(self):
        for due in ("2026-12-01", "garbage"):
            with self.subTest(due=due):
                items = [{"id": "q1", "priority": 1, "window_item": {"due": due, "title": "Later"}}]
                got = rescue(items, [], today=TODAY)
                self.assertEqual(got["basis"], "queue")
                self.assertEqual(got["action"]["due"], due)

    def test_empty_inputs(self):
        got = rescue([], [], today=TODAY)
        self.assertIsNone(got["basis"])
        self.assertIsNone(got["action"])
        self.assertEqual(got["suppressed"], 0)

    def test_follow_up_message_is_plain_english(self):
        got = rescue([], [], today=TODAY)
        self.assertEqual(got["then"], "Finish this one step, then press Just one thing again.")
        self.assertNotIn("agent-os", got["then"])


if __name__ == "__main__":
    unittest.main()
