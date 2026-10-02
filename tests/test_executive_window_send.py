import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import http.client
import json
import tempfile
import threading
import unittest

from agent_os.executive.gateway import SyntheticDashboardGateway
from agent_os.executive.window.registry import Registry
from agent_os.executive.window.server import Api, build_server
from agent_os.executive.window.transport import FakeTransport


class _Bridge:
    def send(self, conversation_id, text):
        return {"reply": "ok"}


def _payload(**over):
    body = dict(to="a@example.invalid", subject="Hello", body="Body text",
                kind="outreach", applicant_ref="app-1", county="Fulton")
    body.update(over)
    return body


class SendApiTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.gateway = SyntheticDashboardGateway(applicants=[dict(applicant_ref="app-1", status="New")])
        self.transport = FakeTransport()
        self.api = Api(Registry(), _Bridge(), self.home, transport=self.transport,
                       gateway_factory=lambda: self.gateway)

    def tearDown(self):
        self.tmp.cleanup()

    def audit_lines(self):
        path = self.api.pending.audit_path
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def test_success_records_status_and_audits_without_body(self):
        result = self.api.post("/api/send", _payload())
        self.assertTrue(result["sent"])
        self.assertTrue(result["status_recorded"])
        self.assertEqual(len(self.transport.calls), 1)
        self.assertEqual([c for c in self.gateway.calls if c[0] == "record_applicant_sent"],
                         [("record_applicant_sent", ("app-1", "outreach", "a@example.invalid", "Hello"))])
        self.assertEqual(self.gateway.applicants["app-1"]["status"], "Interested")
        audit = self.audit_lines()
        self.assertEqual(len(audit), 1)
        self.assertTrue(audit[0]["send"]["sent"])
        self.assertNotIn("Body text", json.dumps(audit))

    def test_transport_failure_is_not_sent_and_not_recorded(self):
        self.transport._fail_with = "smtp refused"
        result = self.api.post("/api/send", _payload())
        self.assertFalse(result["sent"])
        self.assertTrue(result["error"].startswith("NOT SENT"))
        self.assertEqual(self.gateway.calls, [])
        self.assertEqual(self.gateway.applicants["app-1"]["status"], "New")
        self.assertFalse(self.audit_lines()[0]["send"]["sent"])

    def test_missing_to_rejected_without_sending(self):
        with self.assertRaises(ValueError):
            self.api.post("/api/send", _payload(to="  "))
        self.assertEqual(self.transport.calls, [])
        self.assertEqual(self.gateway.calls, [])

    def test_status_record_failure_reported(self):
        result = self.api.post("/api/send", _payload(applicant_ref="missing"))
        self.assertTrue(result["sent"])
        self.assertFalse(result["status_recorded"])
        self.assertIn("error", result)

    def test_no_applicant_ref_skips_gateway(self):
        result = self.api.post("/api/send", _payload(applicant_ref=None, kind="reply"))
        self.assertTrue(result["sent"])
        self.assertEqual(self.gateway.calls, [])


class SendHttpTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.transport = FakeTransport()
        self.gateway = SyntheticDashboardGateway(applicants=[dict(applicant_ref="app-1", status="New")])
        self.server, self.token = build_server("127.0.0.1", 0, registry=Registry(), bridge=_Bridge(),
                                               home=Path(self.tmp.name), transport=self.transport,
                                               gateway_factory=lambda: self.gateway)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.tmp.cleanup()

    def post(self, body, token=True):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        headers = {"Host": f"127.0.0.1:{self.port}", "Content-Type": "application/json"}
        if token:
            headers["X-Agent-OS-Token"] = self.token
        conn.request("POST", "/api/send", body=json.dumps(body).encode(), headers=headers)
        response = conn.getresponse()
        payload = json.loads(response.read())
        conn.close()
        return response.status, payload

    def test_requires_session_token(self):
        status, _ = self.post(_payload(), token=False)
        self.assertEqual(status, 403)
        self.assertEqual(self.transport.calls, [])

    def test_send_with_token(self):
        status, payload = self.post(_payload())
        self.assertEqual(status, 200)
        self.assertTrue(payload["sent"])

    def test_failure_is_http_200(self):
        self.transport._fail_with = "down"
        status, payload = self.post(_payload())
        self.assertEqual(status, 200)
        self.assertFalse(payload["sent"])

    def test_missing_to_is_400(self):
        status, _ = self.post(_payload(to=""))
        self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()
