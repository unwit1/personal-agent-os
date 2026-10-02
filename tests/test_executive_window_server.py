import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import http.client
import json
import tempfile
import threading
import unittest

from agent_os.executive.window.registry import Registry
from agent_os.executive.window.server import build_server


class FakeBridge:
    def __init__(self):
        self.calls = []

    def send(self, conversation_id, text):
        self.calls.append((conversation_id, text))
        return {"reply": f"ok: {text}", "session_id": "sess-1", "error": None}


class ExecutiveWindowServerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.executed = []
        registry = Registry()
        registry.register_provider("synthetic", lambda: [
            {"id": "w1", "tab": "work", "kind": "synthetic", "title": "Work item", "why": "test", "source": "fixture"},
            {"id": "p1", "tab": "personal", "kind": "synthetic", "title": "Personal item", "why": "test", "source": "fixture"},
        ])

        def send_handler(item, params, confirm):
            if confirm:
                self.executed.append(item["id"])
                return {"sent": True}
            return {"preview": f"would send for {item['id']}"}

        registry.register_action("synthetic.send", "Send", ["synthetic"], send_handler, consequential=True)
        registry.register_action("synthetic.note", "Note", ["synthetic"], lambda item, params, confirm: {"noted": item["id"]}, consequential=False)
        self.bridge = FakeBridge()
        self.server, self.token = build_server("127.0.0.1", 0, registry=registry, bridge=self.bridge, home=self.home)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.tmp.cleanup()

    def request(self, method, path, body=None, token=True, host=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        headers = {"Host": host or f"127.0.0.1:{self.port}", "Content-Type": "application/json"}
        if token:
            headers["X-Agent-OS-Token"] = self.token
        data = json.dumps(body).encode("utf-8") if body is not None else None
        conn.request(method, path, body=data, headers=headers)
        response = conn.getresponse()
        raw = response.read()
        conn.close()
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = raw
        return response.status, payload

    def test_rejects_non_loopback_host(self):
        with self.assertRaises(ValueError):
            build_server("0.0.0.0")

    def test_binds_to_localhost(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")

    def test_post_without_token_is_forbidden(self):
        status, _ = self.request("POST", "/api/act", {"action_id": "synthetic.note", "item_id": "w1"}, token=False)
        self.assertEqual(status, 403)

    def test_bad_host_header_rejected(self):
        status, _ = self.request("GET", "/api/items", host="evil.example:80")
        self.assertEqual(status, 403)
        status, _ = self.request("POST", "/api/chat", {"text": "hi"}, host="evil.example:80")
        self.assertEqual(status, 403)

    def test_index_injects_token(self):
        status, body = self.request("GET", "/", token=False)
        self.assertEqual(status, 200)
        self.assertIn(self.token.encode("ascii"), body)

    def test_items_and_options_from_registry(self):
        status, payload = self.request("GET", "/api/items?tab=work")
        self.assertEqual(status, 200)
        self.assertEqual([item["id"] for item in payload["items"]], ["w1"])
        self.assertEqual({o["action_id"] for o in payload["items"][0]["options"]}, {"synthetic.send", "synthetic.note"})
        status, payload = self.request("GET", "/api/actions")
        self.assertEqual({a["id"] for a in payload["actions"]}, {"synthetic.send", "synthetic.note"})

    def test_consequential_action_needs_confirm(self):
        status, payload = self.request("POST", "/api/act", {"action_id": "synthetic.send", "item_id": "w1", "params": {}})
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "needs_confirmation")
        self.assertEqual(self.executed, [])
        self.assertFalse((self.home / "audit.jsonl").exists())
        confirm_token = payload["confirm_token"]

        status, pending = self.request("GET", "/api/pending")
        self.assertEqual([r["token"] for r in pending["pending"]], [confirm_token])

        status, payload = self.request("POST", "/api/confirm", {"confirm_token": confirm_token})
        self.assertEqual(status, 200)
        self.assertEqual(payload["result"], {"sent": True})
        self.assertEqual(self.executed, ["w1"])
        lines = (self.home / "audit.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["action_id"], "synthetic.send")

        status, _ = self.request("POST", "/api/confirm", {"confirm_token": confirm_token})
        self.assertNotEqual(status, 200)
        self.assertEqual(self.executed, ["w1"])

    def test_dismiss_declines_without_executing(self):
        _, payload = self.request("POST", "/api/act", {"action_id": "synthetic.send", "item_id": "p1"})
        status, result = self.request("POST", "/api/dismiss", {"item_id": "p1"})
        self.assertEqual(status, 200)
        self.assertEqual(result["declined"], [payload["confirm_token"]])
        self.assertEqual(self.executed, [])
        event = json.loads((self.home / "audit.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertTrue(event["declined"])
        status, _ = self.request("POST", "/api/confirm", {"confirm_token": payload["confirm_token"]})
        self.assertNotEqual(status, 200)
        self.assertEqual(self.executed, [])

    def test_chat_goes_through_bridge(self):
        status, payload = self.request("POST", "/api/chat", {"conversation_id": "c1", "text": "hello"})
        self.assertEqual(status, 200)
        self.assertEqual(payload["reply"], "ok: hello")
        self.assertEqual(self.bridge.calls, [("c1", "hello")])

    def test_option_sends_prompt_to_bridge(self):
        status, _ = self.request("POST", "/api/option", {"conversation_id": "c1", "item_id": "w1", "action_id": "synthetic.send"})
        self.assertEqual(status, 200)
        self.assertEqual(len(self.bridge.calls), 1)
        conversation_id, prompt = self.bridge.calls[0]
        self.assertEqual(conversation_id, "c1")
        self.assertIn("w1", prompt)
        self.assertIn("synthetic.send", prompt)
        self.assertEqual(self.executed, [])


if __name__ == "__main__":
    unittest.main()
