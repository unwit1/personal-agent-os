from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import applicants as ex
from agent_os.executive.window import actions_executive, registry
from agent_os.executive.window.confirm import PendingStore

NOW = datetime(2026, 10, 1, 12, 0)
ROWS = [
    {"agent_ref": ref, "name": name, "position": "Tech", "submitted": "2026-09-20",
     "status": "New", "county": "Kent", "city": "Dover"}
    for ref, name in (("ref-a", "Ann"), ("ref-b", "Bo"), ("ref-c", "Cy"))
]
EMAILS = {"ref-a": "ann@example.test", "ref-b": "bo@example.test", "ref-c": "cy@example.test"}
# Offered slots must stay in the future: the send path rejects past slots against the real clock.
_SLOT_DAY = (datetime.now() + timedelta(days=4)).replace(hour=0, minute=0, second=0, microsecond=0)
SLOTS = [(_SLOT_DAY.replace(hour=9), "free"), (_SLOT_DAY.replace(hour=13), "free")]
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


class ActionExecutiveTests(unittest.TestCase):
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

        # Set up injectable factories with proper cleanup
        gw_patch = patch.object(actions_executive, "GATEWAY_FACTORY", lambda: self.gw)
        store_patch = patch.object(actions_executive, "STORE_FACTORY", lambda: self.store)
        gw_patch.start()
        store_patch.start()
        self.addCleanup(gw_patch.stop)
        self.addCleanup(store_patch.stop)

    def test_plan_interviews_creates_batch(self):
        """Test that plan_interviews action creates a PENDING_APPROVAL batch."""
        item = {"id": "group-1", "kind": "applicant_group"}
        params = {
            "applicant_refs": ["ref-a", "ref-b", "ref-c"],
            "opening": "Tech",
            "interview_type": "phone",
            "location": "Office",
            "duration_minutes": 30,
        }

        result = actions_executive._plan_interviews(item, params, confirm=False)

        self.assertIn("batch_id", result)
        self.assertEqual(result["state"], ex.PENDING_APPROVAL)
        self.assertEqual(len(result["items"]), 3)

        # Verify each item includes slots
        for item_result in result["items"]:
            self.assertIn("applicant_ref", item_result)
            self.assertIn("name", item_result)
            self.assertIn("subject", item_result)
            self.assertIn("slots", item_result)
            self.assertIn("state", item_result)
            self.assertGreater(len(item_result["slots"]), 0)

        # Verify batch was created in store
        batch = self.store.load(result["batch_id"])
        self.assertEqual(batch["state"], ex.PENDING_APPROVAL)
        self.assertEqual(batch["opening"], "Tech")
        self.assertEqual(len(batch["items"]), 3)

    def test_reach_out_preview_does_not_send(self):
        """Test that reach_out preview (confirm=False) does not call gateway.send_now."""
        # First create and approve a batch
        item = {"id": "group-1", "kind": "applicant_group"}
        plan_params = {
            "applicant_refs": ["ref-a", "ref-b", "ref-c"],
            "opening": "Tech",
            "interview_type": "phone",
            "location": "Office",
            "duration_minutes": 30,
        }
        plan_result = actions_executive._plan_interviews(item, plan_params, confirm=False)
        batch_id = plan_result["batch_id"]

        # Approve the batch
        approve_params = {
            "batch_id": batch_id,
            "choices": {
                "ref-a": "confirm",
                "ref-b": "confirm",
                "ref-c": "drop",
            },
        }
        actions_executive._approve_batch(item, approve_params, confirm=True)

        # Preview reach_out
        self.gw.calls.clear()
        reach_params = {"batch_id": batch_id}
        result = actions_executive._reach_out(item, reach_params, confirm=False)

        # Verify preview does not call send_now
        self.assertTrue(result["dry_run"])
        self.assertEqual(self.gw.sends(), [])
        self.assertEqual(len(result["would_send"]), 2)

    def test_reach_out_confirm_sends_through_gateway(self):
        """Test that reach_out with confirm=True sends through the fake gateway."""
        # First create and approve a batch
        item = {"id": "group-1", "kind": "applicant_group"}
        plan_params = {
            "applicant_refs": ["ref-a", "ref-b", "ref-c"],
            "opening": "Tech",
            "interview_type": "phone",
            "location": "Office",
            "duration_minutes": 30,
        }
        plan_result = actions_executive._plan_interviews(item, plan_params, confirm=False)
        batch_id = plan_result["batch_id"]

        # Approve the batch
        approve_params = {
            "batch_id": batch_id,
            "choices": {
                "ref-a": "confirm",
                "ref-b": "confirm",
                "ref-c": "drop",
            },
        }
        actions_executive._approve_batch(item, approve_params, confirm=True)

        # Send with confirmation
        self.gw.calls.clear()
        reach_params = {"batch_id": batch_id}
        result = actions_executive._reach_out(item, reach_params, confirm=True)

        # Verify confirmed send called gateway
        self.assertFalse(result["dry_run"])
        self.assertEqual(sorted(result["sent"]), ["ref-a", "ref-b"])
        self.assertEqual(self.gw.sends(), ["ref-a", "ref-b"])
        self.assertIn(("send_now", "ref-a", ex.OUTREACH_KIND, EMAILS["ref-a"]), self.gw.calls)

    def test_register_adds_actions(self):
        """register() adds plan and approve for applicant groups, plus the confirm-only
        send and browser actions for model requests; reach_out goes through compose."""
        reg = registry.Registry()
        actions_executive.register(reg)

        actions = {a["id"]: a for a in reg.actions()}

        self.assertEqual(set(actions), {"executive.plan_interviews", "executive.approve_batch",
                                        "executive.send_batch", "browser.execute_consequential"})
        self.assertNotIn("executive.reach_out", actions)

        # Approval is the operator's decision, so it needs a window Confirm.
        self.assertFalse(actions["executive.plan_interviews"]["consequential"])
        self.assertTrue(actions["executive.approve_batch"]["consequential"])
        self.assertTrue(actions["executive.send_batch"]["consequential"])
        self.assertTrue(actions["browser.execute_consequential"]["consequential"])

        # Verify applies_to
        for action_id in ["executive.plan_interviews", "executive.approve_batch"]:
            self.assertEqual(actions[action_id]["applies_to"], ["applicant_group"])

    def test_approve_batch_preview_changes_nothing_until_confirm(self):
        with tempfile.TemporaryDirectory() as tmp:
            pending = PendingStore(tmp)
            reg = registry.Registry()
            actions_executive.register(reg)
            item = {"id": "group-1", "kind": "applicant_group", "tab": "work"}
            plan = reg.invoke("executive.plan_interviews", item, {
                "applicant_refs": ["ref-a"], "opening": "Tech", "interview_type": "phone",
                "location": "Office", "duration_minutes": 30}, pending)
            batch_id = plan["result"]["batch_id"]

            out = reg.invoke("executive.approve_batch", item,
                             {"batch_id": batch_id, "choices": {"ref-a": "confirm"}}, pending)
            self.assertEqual(out["status"], "needs_confirmation")
            self.assertEqual(self.store.load(batch_id)["state"], ex.PENDING_APPROVAL)

            done = reg.confirm(out["confirm_token"], pending)
            self.assertEqual(done["state"], ex.APPROVED)
            self.assertEqual(self.store.load(batch_id)["state"], ex.APPROVED)

    def test_actions_through_registry(self):
        """Test that actions work when invoked through the registry."""
        with tempfile.TemporaryDirectory() as tmp:
            pending = PendingStore(tmp)
            reg = registry.Registry()
            actions_executive.register(reg)

            item = {"id": "group-1", "kind": "applicant_group", "tab": "work"}
            plan_params = {
                "applicant_refs": ["ref-a", "ref-b"],
                "opening": "Tech",
                "interview_type": "phone",
                "location": "Office",
                "duration_minutes": 30,
            }

            # Invoke through registry
            result = reg.invoke("executive.plan_interviews", item, plan_params, pending)

            self.assertEqual(result["status"], "done")
            self.assertIn("batch_id", result["result"])

    def test_reach_out_consequential_flow(self):
        """reach_out is not a window action: the registry refuses it and nothing sends."""
        with tempfile.TemporaryDirectory() as tmp:
            pending = PendingStore(tmp)
            reg = registry.Registry()
            actions_executive.register(reg)

            # Create and approve batch first
            item = {"id": "group-1", "kind": "applicant_group", "tab": "work"}
            plan_params = {
                "applicant_refs": ["ref-a", "ref-b"],
                "opening": "Tech",
                "interview_type": "phone",
                "location": "Office",
                "duration_minutes": 30,
            }
            plan_result = reg.invoke("executive.plan_interviews", item, plan_params, pending)
            batch_id = plan_result["result"]["batch_id"]

            approve_params = {
                "batch_id": batch_id,
                "choices": {"ref-a": "confirm", "ref-b": "confirm"},
            }
            approval = reg.invoke("executive.approve_batch", item, approve_params, pending)
            reg.confirm(approval["confirm_token"], pending)

            # Preview reach_out (should not actually send)
            self.gw.calls.clear()
            reach_params = {"batch_id": batch_id}
            with self.assertRaises(KeyError):
                reg.invoke("executive.reach_out", item, reach_params, pending)
            self.assertEqual(self.gw.sends(), [])

    def test_privacy_preserved_in_output(self):
        """Test that action output preserves privacy rules (no secrets in JSON)."""
        item = {"id": "group-1", "kind": "applicant_group"}
        params = {
            "applicant_refs": ["ref-a", "ref-b", "ref-c"],
            "opening": "Tech",
            "interview_type": "phone",
            "location": "Office",
            "duration_minutes": 30,
        }

        result = actions_executive._plan_interviews(item, params, confirm=False)
        batch_id = result["batch_id"]
        batch = self.store.load(batch_id)

        # Verify no email addresses in batch
        text = json.dumps(batch)
        for email in EMAILS.values():
            self.assertNotIn(email, text)


if __name__ == "__main__":
    unittest.main()
