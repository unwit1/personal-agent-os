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
from agent_os.executive.window import actions_documents, doc_store, providers_documents
from agent_os.executive.window import registry as window_registry
from agent_os.executive.window.server import build_server, parse_document_request


class FakeBridge:
    def __init__(self):
        self.calls = []

    def send(self, conversation_id, text):
        self.calls.append((conversation_id, text))
        return {"reply": f"model: {text}", "session_id": "s", "error": None}


class DocumentsEntryBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "home"
        self.out = Path(self.tmp.name) / "out"
        self.store = doc_store.DocumentTaskStore(self.home)
        for name, value in (("STORE_FACTORY", lambda: self.store), ("OUTPUT_BASE", self.out)):
            patcher = patch.object(actions_documents, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.reg = window_registry.Registry()
        self.reg.register_provider("documents", lambda: providers_documents.document_items(self.store))
        actions_documents.register(self.reg)


class ChatIntentTest(unittest.TestCase):
    def test_parse(self):
        cases = {
            "new job description for an Executive Assistant": (["job_description"], "Executive Assistant"),
            "Write an internal posting for Executive Assistant": (["internal_posting"], "Executive Assistant"),
            "job description and internal posting for Executive Assistant": (
                ["job_description", "internal_posting"], "Executive Assistant"),
        }
        for text, (types, role) in cases.items():
            self.assertEqual(parse_document_request(text), {"doc_types": types, "role": role}, text)
        for text in ("what is a job description?", "who should we hire for the internal posting team", "hello"):
            self.assertIsNone(parse_document_request(text), text)


class ServerEntryTest(DocumentsEntryBase):
    def setUp(self):
        super().setUp()
        self.bridge = FakeBridge()
        self.server, self.token = build_server("127.0.0.1", 0, registry=self.reg, bridge=self.bridge, home=self.home)
        self.port = self.server.server_address[1]
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 5)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def post(self, path, body):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        headers = {"Host": f"127.0.0.1:{self.port}", "Content-Type": "application/json", "X-Agent-OS-Token": self.token}
        conn.request("POST", path, body=json.dumps(body).encode(), headers=headers)
        response = conn.getresponse()
        payload = json.loads(response.read())
        conn.close()
        return response.status, payload

    def test_start_endpoint_returns_task_and_questions(self):
        status, out = self.post("/api/documents/start", {"doc_type": "job_description", "role": "Executive Assistant"})
        self.assertEqual(status, 200, out)
        self.assertEqual(out["task"]["role"], "Executive Assistant")
        self.assertTrue(out["questions"])
        self.assertEqual(len(self.store.tasks()), 1)

    def test_start_endpoint_rejects_bad_type(self):
        status, _ = self.post("/api/documents/start", {"doc_type": "poem", "role": "X"})
        self.assertGreaterEqual(status, 400)
        self.assertEqual(self.store.tasks(), [])

    def test_chat_starts_two_tasks_without_model_or_save(self):
        status, out = self.post("/api/chat", {"text": "job description and internal posting for Executive Assistant"})
        self.assertEqual(status, 200, out)
        self.assertEqual({t["doc_type"] for t in self.store.tasks()}, {"job_description", "internal_posting"})
        self.assertEqual(self.bridge.calls, [])
        self.assertIn("message", out)
        self.assertIn("previews", out)
        self.assertIn("Nothing is saved", out["message"])
        self.assertIn("reports to", out["message"])
        self.assertFalse(self.out.exists())

    def test_chat_other_text_still_goes_to_model(self):
        status, out = self.post("/api/chat", {"text": "hello there"})
        self.assertEqual(status, 200)
        self.assertEqual(out["message"], "model: hello there")

    def test_answer_then_save_needs_confirmation(self):
        self.post("/api/documents/start", {"doc_type": "internal_posting", "role": "Executive Assistant"})
        items = {i["id"]: i for i in self.reg.outstanding()["items"]}
        question = next(i for i in items.values() if i["kind"] == "document_question")
        status, out = self.post("/api/act", {"item_id": question["id"], "action_id": "document.answer",
                                             "params": {"answer": "The Director"}})
        self.assertEqual(status, 200, out)
        task = next(i for i in items.values() if i["kind"] == "document_task")
        status, out = self.post("/api/act", {"item_id": task["id"], "action_id": "document.save", "params": {}})
        self.assertEqual(out["status"], "needs_confirmation")
        self.assertFalse(self.out.exists())


class McpEntryTest(DocumentsEntryBase):
    def setUp(self):
        super().setUp()
        patcher = patch.dict(os.environ, {"AGENT_OS_EXECUTIVE_WINDOW_HOME": str(self.home)})
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(mcp_server, "_window_registry", lambda: self.reg)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.available = mcp_server.methods()

    def rpc(self, method, params=None):
        return mcp_server._handle_mcp({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}},
                                      self.available)["result"]

    def call(self, name, arguments):
        result = self.rpc("tools/call", {"name": name, "arguments": arguments})
        self.assertFalse(result["isError"], result)
        return json.loads(result["content"][0]["text"])

    def test_tools_listed_and_none_confirms_or_saves(self):
        names = [t["name"] for t in self.rpc("tools/list")["tools"]]
        for tool in ("executive_documents.start", "executive_documents.answer", "executive_documents.list"):
            self.assertIn(tool, names)
        documents_tools = [n for n in names if n.startswith("executive_documents.")]
        self.assertFalse([n for n in documents_tools if "confirm" in n or "save" in n])

    def test_start_answer_list(self):
        started = self.call("executive_documents.start", {"doc_type": "job_description", "role": "Executive Assistant"})
        self.assertTrue(started["questions"])
        doc_id = started["doc_id"]
        answered = self.call("executive_documents.answer", {"doc_id": doc_id, "answers": {"reports_to": "The Director"}})
        self.assertIn("The Director", answered["draft"])
        listed = self.call("executive_documents.list", {})
        self.assertEqual([t["doc_id"] for t in listed["tasks"]], [doc_id])
        self.assertNotIn("reports_to", [q["id"] for q in listed["tasks"][0]["questions"]])
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
