import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.window.registry import Registry
from agent_os.executive.window.rescue_view import project_results, rescue_view


TODAY = date(2026, 10, 5)


class RescueViewTests(unittest.TestCase):
    def setUp(self):
        self.registry = Registry()
        self.registry.register_provider("p", lambda: [
            {"id": "a1", "title": "Pay invoice", "kind": "task", "tab": "work", "due": "2026-10-05"},
            {"id": "b1", "title": "Other", "kind": "task", "tab": "personal"},
        ])

    def test_deadline_item_maps_to_window_id(self):
        got = rescue_view(self.registry, projects=[], today=TODAY)
        self.assertEqual(got["basis"], "deadline")
        self.assertEqual(got["item_id"], "a1")

    def test_tab_filter_selects_personal_item(self):
        got = rescue_view(self.registry, tab="personal", projects=[], today=TODAY)
        self.assertEqual(got["item_id"], "b1")
        self.assertEqual(got["basis"], "queue")

    def test_empty_registry(self):
        got = rescue_view(Registry(), projects=[], today=TODAY)
        self.assertIsNone(got["action"])
        self.assertIsNone(got["item_id"])

    def test_project_action_has_no_window_item_id(self):
        projects = [{"project": "alpha", "status": "active", "next_action": "Write plan", "flags": [], "age_days": 1}]
        got = rescue_view(Registry(), projects=projects, today=TODAY)
        self.assertEqual(got["basis"], "project")
        self.assertIsNone(got["item_id"])

    def test_project_results_collects_per_project_failure(self):
        projects = [{"id": "ok", "state_file": "ok"}, {"id": "bad", "state_file": "bad"}]
        def load(proj):
            if proj["id"] == "bad":
                raise RuntimeError("unavailable")
            return {"project": "ok", "status": "active", "next_action": "Write plan"}
        with patch("agent_os.registry.canonical_projects", return_value=projects), patch("agent_os.registry.load_state", side_effect=load):
            results, errors = project_results(TODAY)
        self.assertEqual(len(results), 1)
        self.assertEqual(errors, [{"project": "bad", "error": "unavailable"}])


if __name__ == "__main__":
    unittest.main()
