import sys
from datetime import date
from pathlib import Path
import tempfile
from unittest import TestCase, main
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.window import actions_projects, registry
from agent_os.executive.window.confirm import PendingStore


class TestProjectActions(TestCase):
    def setUp(self):
        self.reg = registry.Registry()
        actions_projects.register(self.reg)
        actions_projects.LOAD_STATE = lambda project: {
            "project": "demo", "status": "active", "goal": "G",
            "next_action": "Write the parser tests", "updated": "2026-10-01",
        }
        actions_projects.TODAY = lambda: date(2026, 10, 6)
        actions_projects.WRITE_STATE = None

    def tearDown(self):
        actions_projects.LOAD_STATE = None
        actions_projects.TODAY = None
        actions_projects.WRITE_STATE = None

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
        self.assertEqual(action["applies_to"], ["project_decision", "project_stalled", "project_no_next_action", "project_vague_next_action", "project_repeatedly_deferred"])
        self.assertFalse(action["consequential"])

    def test_repeatedly_deferred_actions(self):
        fresh = registry.Registry()
        actions_projects.register(fresh)
        item = {"id": "p1", "kind": "project_repeatedly_deferred", "context": {"project": "p1"}}
        offered = {
            action["id"] for action in fresh.actions()
            if fresh._applies(fresh._actions[action["id"]], item["kind"])
        }
        self.assertIn("project.resume", offered)
        self.assertIn("project.set_next_action", offered)
        self.assertNotIn("project.resolve_decision", offered)

    def test_unknown_project_raises_value_error(self):
        actions_projects.LOAD_STATE = None
        with patch("agent_os.registry.get_project", side_effect=KeyError("missing")):
            with self.assertRaisesRegex(ValueError, "unknown project: missing"):
                self.reg.invoke("project.resume", {"context": {"project": "missing"}}, params=None, pending=None)

    def test_set_next_action_preview_then_confirm_writes_once(self):
        writes = []
        actions_projects.WRITE_STATE = lambda pid, state: writes.append((pid, state))
        item = {"id": "p", "kind": "project_stalled", "context": {"project": "demo"}}
        params = {"next_action": "Send the draft to Maya"}
        with tempfile.TemporaryDirectory() as directory:
            pending = PendingStore(directory)
            preview = self.reg.invoke("project.set_next_action", item, params, pending)
            self.assertEqual(preview["status"], "needs_confirmation")
            self.assertEqual(preview["preview"]["after"], params["next_action"])
            self.assertEqual(writes, [])
            self.reg.confirm(preview["confirm_token"], pending)
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0][1]["next_action"], params["next_action"])
        self.assertEqual(writes[0][1]["updated_at"], "2026-10-06")

    def test_repeatedly_deferred_set_next_action_preview_then_confirm_writes_once(self):
        writes = []
        actions_projects.WRITE_STATE = lambda pid, state: writes.append((pid, state))
        item = {"id": "p1", "kind": "project_repeatedly_deferred", "context": {"project": "p1"}}
        params = {"next_action": "Send the draft to Maya"}
        with tempfile.TemporaryDirectory() as directory:
            pending = PendingStore(directory)
            preview = self.reg.invoke("project.set_next_action", item, params, pending)
            self.assertEqual(preview["status"], "needs_confirmation")
            self.assertEqual(preview["preview"]["after"], params["next_action"])
            self.assertEqual(writes, [])
            self.reg.confirm(preview["confirm_token"], pending)
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0][0], "p1")
        self.assertEqual(writes[0][1]["next_action"], params["next_action"])
        self.assertEqual(writes[0][1]["updated_at"], "2026-10-06")

    def test_set_next_action_rejects_vague_and_empty_values(self):
        item = {"context": {"project": "demo"}}
        with self.assertRaisesRegex(ValueError, "too vague"):
            actions_projects._set_next_action(item, {"next_action": "work on it"}, confirm=False)
        with self.assertRaisesRegex(ValueError, "non-empty string"):
            actions_projects._set_next_action(item, {"next_action": "  "}, confirm=False)

    def test_set_next_action_action_metadata(self):
        action = self.reg._actions["project.set_next_action"]
        self.assertTrue(action["consequential"])
        self.assertEqual(action["applies_to"], ["project_stalled", "project_no_next_action", "project_vague_next_action", "project_repeatedly_deferred"])

    def test_resolve_decision_preview_then_confirm_writes_resolution(self):
        writes = []
        actions_projects.WRITE_STATE = lambda pid, state: writes.append((pid, state))
        actions_projects.LOAD_STATE = lambda project: {"decisions_needed": ["Choose a date", "Pick an owner"]}
        item = {"id": "d", "kind": "project_decision", "context": {"project": "demo", "decision": "Choose a date"}}
        params = {"resolution": "Use October 20"}
        with tempfile.TemporaryDirectory() as directory:
            pending = PendingStore(directory)
            preview = self.reg.invoke("project.resolve_decision", item, params, pending)
            self.assertEqual(preview["status"], "needs_confirmation")
            self.assertEqual(preview["preview"]["remaining_decisions"], ["Pick an owner"])
            self.assertEqual(writes, [])
            result = self.reg.confirm(preview["confirm_token"], pending)
        state = writes[0][1]
        self.assertEqual(state["decisions_needed"], ["Pick an owner"])
        self.assertEqual(state["decisions_resolved"], [{"decision": "Choose a date", "resolution": "Use October 20", "resolved_on": "2026-10-06"}])
        self.assertEqual(state["updated_at"], "2026-10-06")
        self.assertEqual(result["resolved_on"], "2026-10-06")

    def test_resolve_decision_rejects_unknown_and_empty_resolution(self):
        actions_projects.LOAD_STATE = lambda project: {"decisions_needed": ["Other"]}
        item = {"context": {"project": "demo", "decision": "Choose a date"}}
        with self.assertRaisesRegex(ValueError, "decision no longer open"):
            actions_projects._resolve_decision(item, {"resolution": "Done"}, confirm=False)
        with self.assertRaisesRegex(ValueError, "resolution must be a non-empty string"):
            actions_projects._resolve_decision(item, {"resolution": " "}, confirm=False)

    def test_resolve_decision_action_metadata(self):
        action = self.reg._actions["project.resolve_decision"]
        self.assertTrue(action["consequential"])
        self.assertEqual(action["applies_to"], ["project_decision"])


if __name__ == "__main__":
    main()
