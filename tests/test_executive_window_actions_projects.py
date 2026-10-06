import sys
from datetime import date
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.window import actions_projects, registry


class TestProjectActions(TestCase):
    def setUp(self):
        self.reg = registry.Registry()
        actions_projects.register(self.reg)
        actions_projects.LOAD_STATE = lambda project: {
            "project": "demo", "status": "active", "goal": "G",
            "next_action": "Write the parser tests", "updated": "2026-10-01",
        }
        actions_projects.TODAY = lambda: date(2026, 10, 6)

    def tearDown(self):
        actions_projects.LOAD_STATE = None
        actions_projects.TODAY = None

    def test_resume_returns_packet(self):
        result = self.reg.invoke(
            "project.resume",
            {"id": "project:demo:stalled", "kind": "project_stalled", "context": {"project": "demo"}},
            pending=None,
            params=None,
        )
        self.assertEqual(result["status"], "done")
        self.assertEqual(result["result"]["packet"]["schema"], "agent-os/resumption-packet@1")
        self.assertEqual(result["result"]["project"], "demo")

    def test_missing_project_context_raises(self):
        with self.assertRaisesRegex(ValueError, "missing project id"):
            self.reg.invoke("project.resume", {"id": "x", "context": {}}, params=None, pending=None)

    def test_action_kinds_and_consequential_flag(self):
        action = self.reg._actions["project.resume"]
        self.assertEqual(action["applies_to"], ["project_decision", "project_stalled", "project_no_next_action", "project_vague_next_action"])
        self.assertFalse(action["consequential"])

    def test_unknown_project_raises_value_error(self):
        actions_projects.LOAD_STATE = None
        with patch("agent_os.registry.get_project", side_effect=KeyError("missing")):
            with self.assertRaisesRegex(ValueError, "unknown project: missing"):
                self.reg.invoke("project.resume", {"context": {"project": "missing"}}, params=None, pending=None)


if __name__ == "__main__":
    main()
