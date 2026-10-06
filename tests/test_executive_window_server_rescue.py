import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import http.client
import json
import tempfile
import threading
import unittest
from unittest.mock import patch

from agent_os.executive.window.registry import Registry
from agent_os.executive.window.server import build_server


class FakeBridge:
    def send(self, conversation_id, text):
        return {"reply": "ok", "error": None}


class RescueServerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        registry = Registry()
        registry.register_provider("fixture", lambda: [
            {"id": "a1", "title": "Pay invoice", "kind": "task", "tab": "work", "due": "2000-01-01"},
        ])
        self.server, self.token = build_server(
            "127.0.0.1", 0, registry=registry, bridge=FakeBridge(), home=self.home,
        )
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.tmp.cleanup()

    def get(self, path):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request("GET", path, headers={"Host": f"127.0.0.1:{self.port}"})
        response = conn.getresponse()
        payload = json.loads(response.read())
        conn.close()
        return response.status, payload

    @patch("agent_os.executive.window.rescue_view.project_results", return_value=([], []))
    def test_rescue_view_returns_ranked_deadline_action(self, _project_results):
        status, payload = self.get("/api/rescue")
        self.assertEqual(status, 200)
        self.assertEqual(payload["mode"], "rescue")
        self.assertEqual(payload["basis"], "deadline")
        self.assertEqual(payload["item_id"], "a1")
        for key in ("why", "then", "suppressed", "errors"):
            self.assertIn(key, payload)

    @patch("agent_os.executive.window.rescue_view.project_results", return_value=([], []))
    def test_rescue_view_can_filter_personal_tab(self, _project_results):
        status, payload = self.get("/api/rescue?tab=personal")
        self.assertEqual(status, 200)
        self.assertIsNone(payload["action"])
        self.assertIsNone(payload["item_id"])

    def test_invalid_tab_is_bad_request(self):
        status, payload = self.get("/api/rescue?tab=bogus")
        self.assertEqual(status, 400)
        self.assertIn("tab must be work or personal", payload["error"])

    def test_invalid_horizon_days_is_bad_request(self):
        status, payload = self.get("/api/rescue?horizon_days=x")
        self.assertEqual(status, 400)
        self.assertIn("horizon_days must be an integer", payload["error"])

    @patch("agent_os.executive.window.rescue_view.project_results", return_value=([], []))
    def test_horizon_days_is_passed_through(self, _project_results):
        with patch("agent_os.executive.window.server.rescue_view", return_value={}) as view:
            status, _ = self.get("/api/rescue?horizon_days=7")
        self.assertEqual(status, 200)
        self.assertEqual(view.call_args.kwargs["horizon_days"], 7)


if __name__ == "__main__":
    unittest.main()
