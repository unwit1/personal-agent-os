from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import mcp_server
from agent_os.executive import applicants as ex

FUTURE = datetime.now().replace(microsecond=0) + timedelta(days=3)
ROWS = [{"agent_ref": "ref-a", "name": "Ann", "position": "Tech", "submitted": "2026-09-20",
         "status": "New", "county": "Kent", "city": "Dover"},
        {"agent_ref": "ref-b", "name": "Bob", "position": "Tech", "submitted": "2026-09-21",
         "status": "Interested", "county": "Kent", "city": "Dover"}]
TOOLS = ("executive.needs_action", "executive.suggestions", "executive.plan",
         "executive.batch", "executive.approve", "executive.send")


class MemStore:
    def __init__(self):
        self.data = {}

    def save(self, batch):
        self.data[batch["batch_id"]] = json.loads(json.dumps(batch))

    def load(self, batch_id):
        return json.loads(json.dumps(self.data[batch_id]))


class FakeGateway:
    def __init__(self):
        self.calls = []

    def match_for(self, ref):
        return {"match": "Tech", "pending": False, "alternates": [], "reasons": []}

    def manager_for(self, ref):
        return "Mgr"

    def suggest_slots(self, manager, duration_minutes, count):
        return [(FUTURE, "free")]

    def render_outreach(self, name, position, slots, interview_type, location, duration_minutes, message, county):
        return f"Interview: {position}", f"Hello {name}"

    def record_outreach_drafted(self, ref, slots, interview_type, location, duration_minutes, draft_path, area_manager):
        self.calls.append(("draft", ref))
        return "draft-1"

    def send_now(self, ref, kind, to_addr, subject, body):
        self.calls.append(("send_now", ref))
        return "email-1"

    def ranked(self, min_score=0):
        applicant = {"applicant_ref": "ref-a", "name": "Ann", "position": "Tech",
                     "submitted": "2026-09-20", "status": "New", "county": "Kent", "city": "Dover"}
        review = {"score": 88, "recommendation": "interview",
                  "result_json": {"summary": "Strong fit", "strengths": ["EE degree"], "concerns": [], "criteria": []}}
        return [(applicant, review)]


def call(name, **arguments):
    request = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments}}
    result = mcp_server._handle_mcp(request, mcp_server.methods())["result"]
    return bool(result.get("isError")), json.loads(result["content"][0]["text"])


class ExecutiveMcpTests(unittest.TestCase):
    def setUp(self):
        self.gw, self.store = FakeGateway(), MemStore()
        patches = (
            patch.object(mcp_server, "_executive_gateway", lambda: self.gw),
            patch.object(mcp_server, "_executive_store", lambda: self.store),
            patch.object(ex.rtec_applicants, "list_applicants",
                         side_effect=lambda status=None, limit=50, offset=0: {"count": 1, "results": [dict(r) for r in ROWS if not status or r["status"] == status][offset:offset + limit]}),
            patch.object(ex.rtec_applicants, "get_summary", side_effect=lambda ref: {"applicant_ref": ref, "email": "ann@example.test"}),
            patch.object(ex.rtec_applicants, "pending_actions", side_effect=lambda limit=100: {"results": [
                {"applicant_ref": "ref-a", "name": "Ann", "position": "Tech", "status": "New",
                 "submitted": "2026-09-20", "administrative_action": "human_review_pending"}]}),
            patch.object(ex.rtec_applicants, "_audit_access", lambda *a, **k: None),
        )
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def plan(self):
        err, out = call("executive.plan", applicant_refs=["ref-a"], opening="Tech",
                        interview_type="phone", location="HQ", duration_minutes=30)
        self.assertFalse(err, out)
        return out["batch_id"]

    def test_discovery(self):
        listed = mcp_server._handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, mcp_server.methods())
        tools = {t["name"]: t for t in listed["result"]["tools"]}
        for name in TOOLS:
            self.assertIn(name, tools)
            self.assertIn(name, mcp_server.methods())
        self.assertIn("confirm_send", tools["executive.send"]["inputSchema"]["properties"])
        self.assertNotIn("confirm_send", tools["executive.approve"]["inputSchema"]["properties"])

    def test_needs_action_and_suggestions(self):
        err, out = call("executive.needs_action")
        self.assertFalse(err)
        self.assertEqual(out["count"], 1)
        err, out = call("executive.suggestions", opening="Tech")
        self.assertFalse(err, out)
        self.assertEqual(out["label"], ex.ADVISORY_LABEL)
        self.assertEqual(out["count"], 2)  # reviewed fits first, then unreviewed fits with no score
        self.assertIsNone(out["suggestions"][1]["score"])
        self.assertEqual(out["suggestions"][0]["applicant_ref"], "ref-a")
        self.assertEqual(out["suggestions"][0]["score"], 88)
        self.assertEqual(out["suggestions"][0]["label"], ex.ADVISORY_LABEL)
        self.assertEqual(out["unreviewed_matching_count"], 1)

    def test_plan_inspect_approve_and_send_gate(self):
        batch_id = self.plan()
        err, out = call("executive.batch", batch_id=batch_id)
        self.assertFalse(err)
        self.assertEqual(out["state"], ex.PENDING_APPROVAL)
        self.assertNotIn("@", json.dumps(out))

        err, out = call("executive.send", batch_id=batch_id, confirm_send=True)
        self.assertTrue(err)  # not approved yet
        err, out = call("executive.approve", batch_id=batch_id, choices={"ref-a": "confirm"})
        self.assertFalse(err, out)
        self.assertEqual(self.store.load(batch_id)["state"], ex.APPROVED)

        err, out = call("executive.send", batch_id=batch_id)
        self.assertFalse(err, out)
        self.assertTrue(out["dry_run"])
        err, out = call("executive.send", batch_id=batch_id, confirm_send="yes")
        self.assertTrue(out["dry_run"])
        self.assertFalse([c for c in self.gw.calls if c[0] == "send_now"])

        err, out = call("executive.send", batch_id=batch_id, confirm_send=True)
        self.assertFalse(err, out)
        self.assertFalse(out["dry_run"])
        self.assertEqual(out["sent"], ["ref-a"])
        self.assertEqual([c for c in self.gw.calls if c[0] == "send_now"], [("send_now", "ref-a")])

    def test_unknown_batch_is_error(self):
        err, _ = call("executive.batch", batch_id="nope")
        self.assertTrue(err)


if __name__ == "__main__":
    unittest.main()
