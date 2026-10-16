import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import contextlib
import tempfile
import threading
import unittest
from unittest import mock

from agent_os.executive.window import actions_coding, providers_orchestrator
from agent_os.executive.window.registry import Registry
from agent_os.executive.window.server import Api


class FakeWake:
    enabled = False

    @contextlib.contextmanager
    def request(self):
        yield


class FakeBridge:
    def __init__(self):
        self.sent = []

    def send(self, conversation_id, text):
        self.sent.append(text)
        return {"reply": "model"}


class CodingTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name) / "home"
        self.home.mkdir()
        self.repo = Path(tmp.name) / "repo"
        self.repo.mkdir()
        self.registry = Registry()
        actions_coding.register(self.registry)
        self.bridge = FakeBridge()
        self.api = Api(self.registry, self.bridge, self.home, transport=object(), gateway_factory=lambda: None,
                       wake=FakeWake(), usage_home=Path(tmp.name) / "usage")
        self.started = threading.Event()
        self.start = mock.Mock(return_value={"run_id": "run-abcdef12"})
        self.engine = mock.Mock()
        self.engine.run_loop.side_effect = lambda *a, **k: self.started.set()
        self.patches = [
            mock.patch("agent_os.orchestrator.service.start_recommended", self.start),
            mock.patch("agent_os.orchestrator.service.engine", return_value=self.engine),
            mock.patch("agent_os.orchestrator.service.providers", return_value={"providers": [{"id": "claude"}]}),
        ]
        for patch in self.patches:
            patch.start()
            self.addCleanup(patch.stop)

    def test_preview_has_no_side_effects(self):
        out = self.api.post("/api/coding/start", {"goal": "add a test", "repo": str(self.repo)})
        self.assertEqual(out["status"], "needs_confirmation")
        self.assertEqual(out["preview"]["goal"], "add a test")
        self.assertEqual(out["preview"]["repo"], str(self.repo.resolve()))
        self.assertEqual(out["preview"]["routing"]["providers"], ["claude"])
        self.assertIn("nothing is merged without you", out["preview"]["note"])
        self.start.assert_not_called()
        self.engine.run_loop.assert_not_called()

    def test_confirm_starts_exactly_once(self):
        out = self.api.post("/api/coding/start", {"goal": "add a test", "repo": str(self.repo)})
        result = self.api.post("/api/confirm", {"confirm_token": out["confirm_token"]})
        self.assertEqual(result["result"]["run_id"], "run-abcdef12")
        self.assertTrue(self.started.wait(5))
        self.start.assert_called_once()
        args, kwargs = self.start.call_args
        self.assertEqual(args[0], "add a test")
        self.assertEqual(kwargs.get("policy"), {})
        self.engine.run_loop.assert_called_once()
        with self.assertRaises(Exception):
            self.api.post("/api/confirm", {"confirm_token": out["confirm_token"]})
        self.start.assert_called_once()

    def test_chat_intents_return_confirmation_not_a_start(self):
        for text in (f"code: fix the bug in {self.repo}", f"Code: fix the bug in {self.repo}"):
            out = self.api.post("/api/chat", {"text": text})
            self.assertTrue(out["confirm_token"])
            self.assertEqual(out["preview"]["goal"], "fix the bug")
        self.start.assert_not_called()
        self.assertEqual(self.bridge.sent, [])

    def test_chat_without_repo_asks_which_project(self):
        out = self.api.post("/api/chat", {"text": "Start a coding task: fix the bug"})
        self.assertNotIn("confirm_token", out)
        self.assertIn("Which project", out["message"])
        out = self.api.post("/api/chat", {"text": "have the orchestrator tidy the docs"})
        self.assertIn("Which project", out["message"])
        self.start.assert_not_called()

    def test_parse_intents(self):
        self.assertEqual(actions_coding.parse_coding_request("start a coding task: do x")["goal"], "do x")
        self.assertEqual(actions_coding.parse_coding_request("code: do x in proj"), {"goal": "do x", "repo": "proj"})
        self.assertEqual(actions_coding.parse_coding_request("have the orchestrator do x")["goal"], "do x")
        self.assertIsNone(actions_coding.parse_coding_request("what needs me today?"))

    def test_unknown_repo_is_rejected(self):
        with self.assertRaises(ValueError):
            self.api.post("/api/coding/start", {"goal": "x", "repo": str(self.repo / "missing")})

    def test_run_items_render(self):
        runs = [{"run_id": "r1", "state": "RUNNING"}, {"run_id": "r2", "state": "COMPLETE"}, {"run_id": "r3", "state": "FAILED"}]
        statuses = {
            "r1": {"goal": "Add retries to the uploader " * 6, "state": "RUNNING", "paused": False,
                   "progress": {"passed": 3, "total": 5}, "gates": [], "nodes": []},
            "r2": {"goal": "Done thing", "state": "COMPLETE", "integration": {"branch": "orch/r2"}},
        }
        items = providers_orchestrator.orchestrator_items(lambda: runs, statuses.__getitem__)
        by_id = {i["id"]: i for i in items}
        self.assertEqual(set(by_id), {"coding:r1", "coding_done:r2"})
        running = by_id["coding:r1"]
        self.assertEqual(running["kind"], "coding_run")
        self.assertEqual(running["tab"], "work")
        self.assertLessEqual(len(running["title"]), 80)
        self.assertIn("3 of 5 tasks done", running["why"])
        self.assertIn("orch/r2", by_id["coding_done:r2"]["why"])

    def test_control_actions(self):
        item = {"id": "coding:r1", "kind": "coding_run", "context": {"run_id": "r1"}}
        with mock.patch("agent_os.orchestrator.service.control", return_value={"state": "PAUSED", "paused": True}) as control:
            self.registry.invoke("coding.pause", item, {}, mock.Mock())
            control.assert_called_once_with("r1", "pause")
            pending = mock.Mock()
            out = self.registry.invoke("coding.stop", item, {}, pending)
            self.assertEqual(out["status"], "needs_confirmation")
            control.assert_called_once()


if __name__ == "__main__":
    unittest.main()
