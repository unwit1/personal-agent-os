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
ROWS = {
    "New": [
        {"agent_ref": "ref-a", "name": "Ann", "position": "Tech", "submitted": "2026-09-20", "status": "New", "county": "Kent", "city": "Dover"},
        {"agent_ref": "ref-b", "name": "Bo", "position": "Tech", "submitted": "2026-09-25", "status": "New", "county": "Kent", "city": "Dover"},
    ],
}
SLOTS = [(datetime(2026, 10, 5, 9), "free"), (datetime(2026, 10, 5, 13), "free"), (datetime(2026, 10, 6, 10), "free")]
TECH = {"match": "Tech", "pending": False, "alternates": [], "reasons": []}


def list_applicants(status=None, limit=50, offset=0):
    rows = [r for group in ROWS.values() for r in group]
    if status:
        rows = [r for r in rows if r["status"] == status]
    rows = rows[offset:offset + limit]
    return {"count": len(rows), "results": [dict(r) for r in rows]}


class FakeGateway:
    def __init__(self):
        self.calls = []
        self.slots = list(SLOTS)
        self.matches = {"ref-a": TECH, "ref-b": TECH}

    def match_for(self, ref):
        self.calls.append(("match_for", ref))
        return self.matches[ref]

    def manager_for(self, ref):
        self.calls.append(("manager_for", ref))
        return "Mgr"

    def suggest_slots(self, manager, duration_minutes, count):
        self.calls.append(("suggest_slots", manager))
        return list(self.slots)

    def render_outreach(self, name, position, slots, interview_type, location, duration_minutes, message, county):
        self.calls.append(("render_outreach", name))
        return f"Interview: {position}", f"{name}: " + ", ".join(w.isoformat() for w, _ in slots)

    def record_outreach_drafted(self, *a, **k):
        self.calls.append(("record_outreach_drafted",))

    def send_now(self, *a, **k):
        self.calls.append(("send_now",))

    def names(self):
        return [c[0] for c in self.calls]


class MemStore:
    def __init__(self):
        self.data = {}

    def save(self, batch):
        self.data[batch["batch_id"]] = json.loads(json.dumps(batch))

    def load(self, batch_id):
        return json.loads(json.dumps(self.data[batch_id]))


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.gw = FakeGateway()
        self.store = MemStore()
        with patch.object(ex.rtec_applicants, "list_applicants", side_effect=list_applicants):
            self.batch = ex.plan_outreach(
                ["ref-a", "ref-b"], "Tech", "phone", "Office", 30,
                gateway=self.gw, store=self.store, now=NOW,
            )
        self.id = self.batch["batch_id"]

    def approve(self, choices, now=NOW, bid=None):
        return ex.approve_batch(bid or self.id, choices, gateway=self.gw, store=self.store, now=now)

    def pending(self):
        return self.store.load(self.id)["state"] == "PENDING_APPROVAL"

    def test_confirm_and_change(self):
        renders = self.gw.names().count("render_outreach")
        out = self.approve({"ref-a": "confirm", "ref-b": [SLOTS[2][0].isoformat()]})
        self.assertEqual(out["state"], "APPROVED")
        a, b = out["items"]
        self.assertEqual((a["state"], a["decision"]), ("APPROVED", "confirmed"))
        self.assertEqual((b["decision"], len(b["slots"])), ("changed", 1))
        self.assertEqual(self.gw.names().count("render_outreach"), renders + 1)
        self.assertIn("2026-10-06T10:00:00", b["body"])
        self.assertEqual(self.store.load(self.id)["state"], "APPROVED")
        self.assertNotIn("send_now", self.gw.names())
        self.assertNotIn("record_outreach_drafted", self.gw.names())

    def test_reordered_slots_count_as_changed_and_rerender(self):
        original = [s["start"] for s in self.batch["items"][0]["slots"]]
        self.assertGreater(len(original), 1)
        renders = self.gw.names().count("render_outreach")
        out = self.approve({"ref-a": list(reversed(original)), "ref-b": "confirm"})
        a = out["items"][0]
        self.assertEqual(a["decision"], "changed")
        self.assertEqual([s["start"] for s in a["slots"]], list(reversed(original)))
        self.assertEqual(self.gw.names().count("render_outreach"), renders + 1)

    def test_drop(self):
        out = self.approve({"ref-a": "drop", "ref-b": "confirm"})
        self.assertEqual(out["items"][0]["state"], "DROPPED")

    def test_all_dropped_rejected(self):
        with self.assertRaises(ex.ApprovalError):
            self.approve({"ref-a": "drop", "ref-b": "drop"})
        self.assertTrue(self.pending())

    def test_missing_extra_invalid_choices(self):
        bad = (
            {"ref-a": "confirm"},
            {"ref-a": "confirm", "ref-b": "confirm", "zzz": "drop"},
            {"ref-a": "confirm", "ref-b": "maybe"},
            {"ref-a": "confirm", "ref-b": []},
        )
        for choices in bad:
            with self.assertRaises(ex.ApprovalError):
                self.approve(choices)
        self.assertTrue(self.pending())

    def test_arbitrary_time_rejected(self):
        with self.assertRaises(ex.ApprovalError):
            self.approve({"ref-a": "confirm", "ref-b": ["2026-10-09T09:00:00"]})
        self.assertTrue(self.pending())

    def test_slot_no_longer_available(self):
        self.gw.slots = SLOTS[1:]
        with self.assertRaises(ex.ApprovalError):
            self.approve({"ref-a": "confirm", "ref-b": "confirm"})
        self.assertTrue(self.pending())

    def test_unknown_stale_repeated(self):
        for bid in ("batch-000000000000", "../etc"):
            with self.assertRaises(ex.ApprovalError):
                self.approve({}, bid=bid)
        with self.assertRaises(ex.ApprovalError):
            self.approve({"ref-a": "confirm", "ref-b": "confirm"}, now=NOW + timedelta(days=2))
        self.approve({"ref-a": "confirm", "ref-b": "confirm"})
        with self.assertRaises(ex.ApprovalError):
            self.approve({"ref-a": "confirm", "ref-b": "confirm"})

    def test_item_held_when_fit_lost(self):
        self.gw.matches["ref-b"] = {"match": "Clerk", "pending": False, "alternates": [], "reasons": []}
        out = self.approve({"ref-a": "confirm", "ref-b": "confirm"})
        self.assertEqual(out["items"][1]["state"], "HELD")

    def test_missing_manager_holds_item(self):
        self.gw.manager_for = lambda ref: None if ref == "ref-b" else "Mgr"
        out = self.approve({"ref-a": "confirm", "ref-b": "confirm"})
        self.assertEqual(out["items"][1]["state"], "HELD")
        self.assertEqual(out["items"][1]["hold_reason"], "no_manager")
        self.assertNotIn(("suggest_slots", None), self.gw.calls)

    def test_timezone_aware_choice_matches_local_slot(self):
        aware = SLOTS[2][0].astimezone().isoformat()
        out = self.approve({"ref-a": "confirm", "ref-b": [aware]})
        self.assertEqual(out["items"][1]["decision"], "changed")


if __name__ == "__main__":
    unittest.main()
