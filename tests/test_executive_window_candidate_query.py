import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import http.client
import json
import tempfile
import threading
import unittest
from unittest import mock

from agent_os.executive.window.actions_candidates_query import parse_candidate_query
from agent_os.executive.window.registry import Registry
from agent_os.executive.window.server import build_server


class ParserTest(unittest.TestCase):
    def test_positive(self):
        cases = {
            "give me some good applicants for the open Bus Driver opening": {"opening": "Bus Driver"},
            "good candidates for dispatcher": {"opening": "dispatcher"},
            "who should I interview for the dispatcher job?": {"opening": "dispatcher"},
            "best applicants for Laurel County": {"opening": "Laurel County"},
            "top 3 applicants for CSR": {"opening": "CSR", "limit": 3},
        }
        for text, expected in cases.items():
            self.assertEqual(parse_candidate_query(text), expected, text)

    def test_negative(self):
        for text in ["", "hello", "I applied for a job", "applicants for dispatcher",
                     "the county has 2 openings", "good morning"]:
            self.assertIsNone(parse_candidate_query(text), text)


class FakeBridge:
    def __init__(self):
        self.calls = []

    def send(self, conversation_id, text):
        self.calls.append((conversation_id, text))
        return {"reply": "model", "error": None}


class ChatCandidatesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.bridge = FakeBridge()
        self.server, self.token = build_server("127.0.0.1", 0, registry=Registry(), bridge=self.bridge,
                                               home=Path(self.tmp.name))
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.tmp.cleanup()

    def chat(self, text):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request("POST", "/api/chat", json.dumps({"text": text}), {
            "Host": f"127.0.0.1:{self.port}", "Content-Type": "application/json",
            "X-Agent-OS-Token": self.token})
        resp = conn.getresponse()
        data = json.loads(resp.read())
        conn.close()
        return resp.status, data

    def test_ranked_reply(self):
        rows = [{"applicant_ref": "a1", "name": "Pat Example", "score": 91,
                 "review_reasons": {"summary": "strong route experience"}, "match_reasons": []},
                {"applicant_ref": "a2", "name": "Sam Sample", "score": 80,
                 "review_reasons": None, "match_reasons": ["position match"]}]
        with mock.patch("agent_os.executive.applicants.suggestions",
                        return_value={"opening": "dispatcher", "suggestions": rows}) as fake:
            status, data = self.chat("good candidates for dispatcher")
        self.assertEqual(status, 200)
        fake.assert_called_once_with("dispatcher")
        self.assertIn("Top applicants for dispatcher: 1. Pat Example (score 91) - strong route experience", data["message"])
        self.assertEqual([c["name"] for c in data["candidates"]], ["Pat Example", "Sam Sample"])
        self.assertEqual(self.bridge.calls, [])

    def test_limit(self):
        rows = [{"applicant_ref": f"a{i}", "name": f"N{i}", "score": 90 - i} for i in range(5)]
        with mock.patch("agent_os.executive.applicants.suggestions", return_value={"suggestions": rows}):
            _, data = self.chat("top 2 applicants for CSR")
        self.assertEqual(len(data["candidates"]), 2)

    def test_empty(self):
        with mock.patch("agent_os.executive.applicants.suggestions", return_value={"suggestions": []}):
            _, data = self.chat("best applicants for Dispatcher")
        self.assertEqual(data["message"], "No reviewed applicants match Dispatcher yet.")
        self.assertEqual(data["candidates"], [])

    def test_error_is_friendly(self):
        with mock.patch("agent_os.executive.applicants.suggestions", side_effect=RuntimeError("boom")):
            status, data = self.chat("best applicants for Dispatcher")
        self.assertEqual(status, 200)
        self.assertIn("Could not look up applicants", data["message"])
        self.assertNotIn("Traceback", data["message"])

    def test_unrelated_goes_to_model(self):
        _, data = self.chat("hello")
        self.assertEqual(data["reply"], "model")


if __name__ == "__main__":
    unittest.main()
