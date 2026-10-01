from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import applicants as ex

NOW = datetime(2026, 10, 1, 12, 0)
ROWS = [
    {"agent_ref": ref, "name": name, "position": "Tech", "submitted": "2026-09-20",
     "status": "New", "county": "Kent", "city": "Dover"}
    for ref, name in (("ref-a", "Ann"), ("ref-b", "Bo"), ("ref-c", "Cy"))
]
EMAILS = {"ref-a": "ann@example.test", "ref-b": "bo@example.test", "ref-c": "cy@example.test"}
SLOTS = [(datetime(2026, 10, 5, 9), "free"), (datetime(2026, 10, 5, 13), "free")]
TECH = {"match": "Tech", "pending": False, "alternates": [], "reasons": []}


def list_applicants(status=None, limit=50, offset=0):
    rows = [r for r in ROWS if not status or r["status"] == status][offset:offset + limit]
    return {"count": len(rows), "results": [dict(r) for r in rows]}


def get_summary(ref):
    return {"applicant_ref": ref, "email": EMAILS.get(ref, "")}


class FakeGateway:
    def __init__(self):
        self.calls = []
        self.fail_send = set()
        self.fail_draft = set()
        self.send_returns_none = set()

    def match_for(self, ref):
        return TECH

    def manager_for(self, ref):
        return "Mgr"

    def suggest_slots(self, manager, duration_minutes, count):
        return list(SLOTS)

    def render_outreach(self, name, position, slots, interview_type, location, duration_minutes, message, county):
        return f"Interview: {position}", f"Hello {name}"

    def record_outreach_drafted(self, ref, slots, interview_type, location, duration_minutes, draft_path, area_manager):
        self.calls.append(("record_outreach_drafted", ref))
        if ref in self.fail_draft:
            raise RuntimeError("dashboard locked")
        return f"draft-{ref}"

    def send_now(self, ref, kind, to_addr, subject, body):
        self.calls.append(("send_now", ref, kind, to_addr))
        if ref in self.fail_send:
            raise RuntimeError(f"Outlook refused {to_addr}")
        if ref in self.send_returns_none:
            return None
        return f"email-{ref}"

    def sends(self):
        return [c[1] for c in self.calls if c[0] == "send_now"]

    def drafts(self):
        return [c[1] for c in self.calls if c[0] == "record_outreach_drafted"]


class MemStore:
    def __init__(self):
        self.data = {}
        self.saves = []

    def save(self, batch):
        self.data[batch["batch_id"]] = json.loads(json.dumps(batch))
        self.saves.append(json.loads(json.dumps(batch)))

    def load(self, batch_id):
        return json.loads(json.dumps(self.data[batch_id]))


class SendTests(unittest.TestCase):
    def setUp(self):
        self.audits = []
        patches = [
            patch.object(ex.rtec_applicants, "list_applicants", side_effect=list_applicants),
            patch.object(ex.rtec_applicants, "get_summary", side_effect=get_summary),
            patch.object(
                ex.rtec_applicants, "_audit_access",
                side_effect=lambda action, applicant_ref=None, metadata=None: self.audits.append(
                    (action, applicant_ref, dict(metadata or {}))
                ),
            ),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.gw = FakeGateway()
        self.store = MemStore()
        batch = ex.plan_outreach(
            ["ref-a", "ref-b", "ref-c"], "Tech", "phone", "Office", 30,
            gateway=self.gw, store=self.store, now=NOW,
        )
        self.id = batch["batch_id"]

    def approve(self):
        ex.approve_batch(
            self.id, {"ref-a": "confirm", "ref-b": "confirm", "ref-c": "drop"},
            gateway=self.gw, store=self.store, now=NOW,
        )

    def send(self, **kw):
        return ex.send_batch(self.id, gateway=self.gw, store=self.store, now=NOW, **kw)

    def items(self):
        return {i["applicant_ref"]: i for i in self.store.load(self.id)["items"]}

    def test_unapproved_batch_cannot_send(self):
        with self.assertRaises(ex.SendError):
            self.send(confirm=True)
        with self.assertRaises(ex.SendError):
            ex.send_batch("batch-missing", gateway=self.gw, store=self.store, confirm=True)
        self.assertEqual(self.gw.calls, [])

    def test_default_is_dry_run(self):
        self.approve()
        before = self.store.load(self.id)
        saves = len(self.store.saves)
        for out in (self.send(), self.send(confirm="yes"), self.send(confirm=1)):
            self.assertTrue(out["dry_run"])
            self.assertEqual([w["applicant_ref"] for w in out["would_send"]], ["ref-a", "ref-b"])
            self.assertEqual(out["sent"], [])
        self.assertEqual(self.gw.calls, [])
        self.assertEqual(self.store.load(self.id), before)
        self.assertEqual(len(self.store.saves), saves)
        self.assertNotIn("@", json.dumps(out))

    def test_confirmed_send_only_approved_undropped(self):
        self.approve()
        out = self.send(confirm=True)
        self.assertFalse(out["dry_run"])
        self.assertEqual(out["state"], ex.SENT)
        self.assertEqual(out["sent"], ["ref-a", "ref-b"])
        self.assertEqual(self.gw.drafts(), ["ref-a", "ref-b"])
        self.assertEqual(self.gw.sends(), ["ref-a", "ref-b"])
        self.assertIn(("send_now", "ref-a", ex.OUTREACH_KIND, EMAILS["ref-a"]), self.gw.calls)
        # Each draft is recorded before its send.
        names = [c[:2] for c in self.gw.calls]
        self.assertLess(names.index(("record_outreach_drafted", "ref-a")), names.index(("send_now", "ref-a")))
        items = self.items()
        self.assertEqual(items["ref-a"]["email_id"], "email-ref-a")
        self.assertEqual(items["ref-a"]["draft_id"], "draft-ref-a")
        self.assertEqual(items["ref-c"]["state"], "DROPPED")
        self.assertNotIn("email_id", items["ref-c"])
        self.assertEqual(self.store.load(self.id)["state"], ex.SENT)
        self.assertNotIn("@", json.dumps(self.store.saves))
        self.assertNotIn("@", json.dumps(self.audits))
        sends = [a for a in self.audits if a[0] == "executive.outreach_send"]
        self.assertEqual([(a[1], a[2]["status"]) for a in sends], [("ref-a", "sent"), ("ref-b", "sent")])

    def test_partial_failure_then_retry(self):
        self.approve()
        self.gw.fail_send = {"ref-a"}
        out = self.send(confirm=True)
        self.assertEqual(out["state"], ex.PARTIALLY_SENT)
        self.assertEqual((out["sent"], out["failed"]), (["ref-b"], ["ref-a"]))
        items = self.items()
        a, b = items["ref-a"], items["ref-b"]
        self.assertEqual(a["state"], "SEND_FAILED")
        self.assertNotIn("email_id", a)
        self.assertEqual((a["send_error"], a["send_stage"]), ("RuntimeError", "send"))
        self.assertEqual(a["draft_id"], "draft-ref-a")
        self.assertEqual(b["email_id"], "email-ref-b")
        self.assertNotIn("@", json.dumps(self.store.saves))
        # The failure was persisted before ref-b was attempted.
        failed_first = [s for s in self.store.saves
                        if s["items"][0]["state"] == "SEND_FAILED" and s["items"][1]["state"] == "APPROVED"]
        self.assertTrue(failed_first)

        self.gw.fail_send = set()
        self.gw.calls.clear()
        out = self.send(confirm=True)
        self.assertEqual(out["state"], ex.SENT)
        self.assertEqual(self.gw.sends(), ["ref-a"])
        self.assertEqual(self.gw.drafts(), [])
        items = self.items()
        self.assertEqual(items["ref-a"]["email_id"], "email-ref-a")
        self.assertEqual(items["ref-a"]["send_attempts"], 2)
        self.assertNotIn("send_error", items["ref-a"])
        self.assertEqual(items["ref-b"]["email_id"], "email-ref-b")

        self.gw.calls.clear()
        out = self.send(confirm=True)
        self.assertEqual(out["state"], ex.SENT)
        self.assertEqual(self.gw.calls, [])

    def test_all_failed_stays_approved_and_never_successful(self):
        self.approve()
        self.gw.fail_send = {"ref-a", "ref-b"}
        out = self.send(confirm=True)
        self.assertEqual(out["state"], ex.APPROVED)
        self.assertEqual(out["sent"], [])
        self.assertTrue(all("email_id" not in i for i in self.items().values()))

    def test_draft_failure_skips_send_and_retries_draft(self):
        self.approve()
        self.gw.fail_draft = {"ref-a"}
        self.send(confirm=True)
        a = self.items()["ref-a"]
        self.assertEqual((a["state"], a["send_stage"]), ("SEND_FAILED", "draft"))
        self.assertNotIn("draft_id", a)
        self.assertEqual(self.gw.sends(), ["ref-b"])
        self.gw.fail_draft = set()
        self.send(confirm=True)
        self.assertEqual(self.gw.drafts().count("ref-a"), 2)
        self.assertEqual(self.items()["ref-a"]["email_id"], "email-ref-a")

    def test_missing_email_fails_without_dashboard_calls(self):
        self.approve()
        with patch.dict(EMAILS, {"ref-a": ""}):
            self.send(confirm=True)
        a = self.items()["ref-a"]
        self.assertEqual((a["state"], a["send_error"]), ("SEND_FAILED", "no_email"))
        self.assertNotIn("ref-a", self.gw.drafts() + self.gw.sends())

    def test_stale_approval_refuses_confirmed_send(self):
        self.approve()
        before = self.store.load(self.id)
        late = NOW + ex.DEFAULT_MAX_BATCH_AGE + timedelta(minutes=1)
        with self.assertRaises(ex.SendError):
            ex.send_batch(self.id, gateway=self.gw, store=self.store, now=late, confirm=True)
        self.assertEqual(self.gw.calls, [])
        self.assertEqual(self.store.load(self.id), before)
        # Dry-run still previews.
        out = ex.send_batch(self.id, gateway=self.gw, store=self.store, now=late)
        self.assertTrue(out["dry_run"])

    def test_past_slot_refuses_confirmed_send(self):
        self.approve()
        batch = self.store.load(self.id)
        batch["items"][1]["slots"][0]["start"] = (NOW - timedelta(hours=1)).isoformat()
        self.store.save(batch)
        with self.assertRaises(ex.SendError):
            self.send(confirm=True)
        self.assertEqual(self.gw.calls, [])
        # A slot starting exactly now is also past.
        with self.assertRaises(ex.SendError):
            ex.send_batch(self.id, gateway=self.gw, store=self.store, now=SLOTS[0][0], confirm=True)
        self.assertTrue(all("email_id" not in i for i in self.items().values()))

    def test_interrupted_or_unconfirmed_send_is_not_resent(self):
        self.approve()
        batch = self.store.load(self.id)
        batch["items"][0]["state"] = "SENDING"
        self.store.save(batch)
        self.gw.send_returns_none = {"ref-b"}
        out = self.send(confirm=True)
        self.assertEqual(sorted(out["unknown"]), ["ref-a", "ref-b"])
        self.assertEqual(self.gw.sends(), ["ref-b"])
        self.assertNotIn("email_id", self.items()["ref-b"])
        self.gw.calls.clear()
        self.send(confirm=True)
        self.assertEqual(self.gw.sends(), [])


if __name__ == "__main__":
    unittest.main()
