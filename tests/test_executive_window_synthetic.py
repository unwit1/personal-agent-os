import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import http.client
import json
import os
import tempfile
import threading
import unittest
from unittest.mock import patch

from agent_os import mcp_server
from agent_os.executive.window.registry import Registry
from agent_os.executive.window.server import build_server


class FakeRunner:
    def __init__(self):
        self.calls = []

    def send(self, conversation_id, text):
        self.calls.append((conversation_id, text))
        return {"reply": "done", "session_id": "sess-e2e", "error": None}


class ExecutiveWindowSyntheticE2ETest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        env = patch.dict(os.environ, {"AGENT_OS_EXECUTIVE_WINDOW_HOME": str(self.home)})
        env.start()
        self.addCleanup(env.stop)

        self.executed = []
        self.registry = Registry()
        self.registry.register_provider("syn-work", lambda: [
            {"id": "w1", "tab": "work", "kind": "synthetic", "title": "Work item", "why": "fixture", "source": "syn-work"}])
        self.registry.register_provider("syn-personal", lambda: [
            {"id": "p1", "tab": "personal", "kind": "synthetic", "title": "Personal item", "why": "fixture", "source": "syn-personal"}])

        def send_handler(item, params, confirm=False):
            if confirm:
                self.executed.append(item["id"])
                return {"sent": True}
            return {"preview": f"would send for {item['id']}"}

        self.registry.register_action("synthetic.send", "Send", ["synthetic"], send_handler, consequential=True)
        self.registry.register_action(
            "synthetic.note", "Note", ["synthetic"], lambda item, params, confirm=False: {"noted": item["id"]}, consequential=False)

        patcher = patch.object(mcp_server, "_window_registry", lambda: self.registry)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.available = mcp_server.methods()

        self.runner = FakeRunner()
        self.server, self.token = build_server("127.0.0.1", 0, registry=self.registry, bridge=self.runner, home=self.home)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self._stop)

    def _stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def request(self, method, path, body=None, token=True):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        headers = {"Host": f"127.0.0.1:{self.port}", "Content-Type": "application/json"}
        if token:
            headers["X-Agent-OS-Token"] = self.token
        data = json.dumps(body).encode("utf-8") if body is not None else None
        conn.request(method, path, body=data, headers=headers)
        response = conn.getresponse()
        raw = response.read()
        conn.close()
        try:
            return response.status, json.loads(raw)
        except ValueError:
            return response.status, raw

    def mcp_call(self, name, arguments):
        response = mcp_server._handle_mcp(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments}},
            self.available)
        result = response["result"]
        self.assertFalse(result["isError"], result)
        return json.loads(result["content"][0]["text"])

    def run_enum(self):
        response = mcp_server._handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}, self.available)
        tools = {t["name"]: t for t in response["result"]["tools"]}
        return tools["executive_window.run"]["inputSchema"]["properties"]["action_id"]["enum"]

    def test_end_to_end(self):
        # (a) tabs and registry-derived options
        for tab, item_id in (("work", "w1"), ("personal", "p1")):
            status, payload = self.request("GET", f"/api/items?tab={tab}")
            self.assertEqual(status, 200)
            self.assertEqual([i["id"] for i in payload["items"]], [item_id])
            self.assertEqual({o["action_id"] for o in payload["items"][0]["options"]}, {"synthetic.send", "synthetic.note"})

        # (b) a later-registered action appears as option and in the schema enum
        self.assertNotIn("synthetic.extra", self.run_enum())
        self.registry.register_action(
            "synthetic.extra", "Extra", ["synthetic"], lambda item, params, confirm=False: {"extra": item["id"]}, consequential=False)
        self.assertIn("synthetic.extra", self.run_enum())
        for tab in ("work", "personal"):
            _, payload = self.request("GET", f"/api/items?tab={tab}")
            self.assertIn("synthetic.extra", {o["action_id"] for o in payload["items"][0]["options"]})

        # (c) consequential action via MCP yields a pending preview visible to the server
        out = self.mcp_call("executive_window.run", {"action_id": "synthetic.send", "item_id": "w1"})
        self.assertEqual(out["status"], "needs_confirmation")
        self.assertNotIn("confirm_token", out)
        self.assertIs(out["confirm_token_issued"], True)
        self.assertEqual(self.executed, [])
        status, pending = self.request("GET", "/api/pending")
        self.assertEqual(status, 200)
        [record] = [r for r in pending["pending"] if r["action_id"] == "synthetic.send"]
        confirm_token = record["token"]
        self.assertNotIn(confirm_token, json.dumps(out))

        # (d) only the explicit confirm with session header executes, once
        status, _ = self.request("POST", "/api/confirm", {"confirm_token": confirm_token}, token=False)
        self.assertEqual(status, 403)
        self.assertEqual(self.executed, [])
        status, payload = self.request("POST", "/api/confirm", {"confirm_token": confirm_token})
        self.assertEqual(status, 200)
        self.assertEqual(payload["result"], {"sent": True})
        self.assertEqual(self.executed, ["w1"])
        status, _ = self.request("POST", "/api/confirm", {"confirm_token": confirm_token})
        self.assertNotEqual(status, 200)
        self.assertEqual(self.executed, ["w1"])
        lines = (self.home / "audit.jsonl").read_text(encoding="utf-8").splitlines()
        events = [json.loads(line) for line in lines]
        self.assertEqual([e["action_id"] for e in events], ["synthetic.send"])

        # (e) /api/option hands the item and action to the model runner
        status, _ = self.request("POST", "/api/option", {"conversation_id": "c1", "item_id": "p1", "action_id": "synthetic.note"})
        self.assertEqual(status, 200)
        self.assertEqual(len(self.runner.calls), 1)
        conversation_id, prompt = self.runner.calls[0]
        self.assertEqual(conversation_id, "c1")
        self.assertIn("p1", prompt)
        self.assertIn("synthetic.note", prompt)


if __name__ == "__main__":
    unittest.main()
