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


class BrainDumpServerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.server, self.token = build_server("127.0.0.1", 0, registry=Registry(), bridge=FakeBridge(), home=self.home)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.tmp.cleanup()

    def request(self, body, token=True):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        headers = {"Host": f"127.0.0.1:{self.port}", "Content-Type": "application/json"}
        if token:
            headers["X-Agent-OS-Token"] = self.token
        conn.request("POST", "/api/brain-dump", body=json.dumps(body).encode("utf-8"), headers=headers)
        response = conn.getresponse()
        payload = json.loads(response.read())
        conn.close()
        return response.status, payload

    def test_captures_records_and_marks_already_captured_duplicates(self):
        with patch("agent_os.executive.window.server._known_projects", return_value=[{"id": "alpha", "aliases": []}]):
            status, result = self.request({"text": "Finish alpha docs\nidea: what if #zeta"})
            self.assertEqual(status, 200)
            self.assertEqual(len(result["added"]), 2)
            self.assertEqual(len(result["clarifications"]), 1)
            self.assertTrue(result["refresh"])

            stored = json.loads((self.home / "brain-dump.json").read_text(encoding="utf-8"))["records"]
            self.assertEqual(set(stored), set(result["added"]))
            self.assertEqual({record["tab"] for record in stored.values()}, {"work"})

            status, repeated = self.request({"text": "Finish alpha docs\nidea: what if #zeta"})
            self.assertEqual(status, 200)
            self.assertEqual(repeated["added"], [])
            self.assertEqual(len(repeated["duplicates"]), 2)
            self.assertTrue(all(item["reason"] == "already_captured" for item in repeated["duplicates"]))

    def test_empty_text_returns_error(self):
        status, payload = self.request({"text": "  "})
        self.assertEqual(status, 400)
        self.assertIn("text is required", payload["error"])

    def test_missing_session_token_is_rejected(self):
        status, payload = self.request({"text": "Finish alpha docs"}, token=False)
        self.assertEqual(status, 403)
        self.assertIn("session token", payload["error"])


if __name__ == "__main__":
    unittest.main()
