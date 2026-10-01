from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import applicants as ex

NOW = datetime(2026, 10, 1, 12, 0)
ROWS = {
    "New": [
        {"agent_ref": "ref-a", "name": "Ann", "position": "Tech", "submitted": "2026-09-20", "status": "New", "county": "Kent", "city": "Dover", "aa_pdf_path": "SECRET-AA.pdf", "race": "SECRET-RACE", "applicant_key": "SECRET-KEY", "source_key": "SECRET-SRC"},
    ],
    "Interested": [
        {"agent_ref": "ref-c", "name": "Cy", "position": "Clerk", "submitted": "2026-09-30", "status": "Interested", "county": "Sussex", "city": "Lewes"},
    ],
}
MATCHES = {
    "ref-a": {"match": "Tech", "pending": False, "alternates": [], "reasons": ["m-a"]},
    "ref-c": {"match": "Clerk", "pending": False, "alternates": ["Tech"], "reasons": ["m-c"]},
}
SLOTS = [(datetime(2026, 10, 5, 9), "free"), (datetime(2026, 10, 5, 13), "free"), (datetime(2026, 10, 6, 10), "free")]


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

    def match_for(self, ref):
        self.calls.append(("match_for", ref))
        return MATCHES[ref]

    def manager_for(self, ref):
        self.calls.append(("manager_for", ref))
        return "Mgr"

    def suggest_slots(self, manager, duration_minutes, count):
        self.calls.append(("suggest_slots", manager, duration_minutes, count))
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


class PlanTests(unittest.TestCase):
    def plan(self, refs, opening="Tech", gw=None, store=None):
        gw = gw or FakeGateway()
        store = store if store is not None else MemStore()
        with patch.object(ex.rtec_applicants, "list_applicants", side_effect=list_applicants):
            batch = ex.plan_outreach(refs, opening, "phone", "Office", 30, gateway=gw, store=store, now=NOW)
        return batch, gw, store

    def test_creates_pending_batch_without_writes_or_sends(self):
        batch, gw, store = self.plan(["ref-a", "ref-c"])
        self.assertEqual(batch["state"], "PENDING_APPROVAL")
        self.assertEqual(batch["opening"], "Tech")
        self.assertEqual([i["applicant_ref"] for i in batch["items"]], ["ref-a", "ref-c"])
        item = batch["items"][0]
        self.assertEqual(len(item["slots"]), 3)
        self.assertEqual(item["subject"], "Interview: Tech")
        self.assertEqual(store.load(batch["batch_id"]), batch)
        self.assertNotIn("record_outreach_drafted", gw.names())
        self.assertNotIn("send_now", gw.names())
        self.assertIn(("suggest_slots", "Mgr", 30, 3), gw.calls)

    def test_mismatch_excluded_and_all_excluded_creates_nothing(self):
        batch, _, _ = self.plan(["ref-a", "ref-c"], opening="Clerk")
        self.assertEqual([i["applicant_ref"] for i in batch["items"]], ["ref-c"])
        self.assertEqual(batch["excluded"][0]["applicant_ref"], "ref-a")
        self.assertEqual(batch["excluded"][0]["reason"], "opening_mismatch")
        self.assertEqual(batch["excluded"][0]["match_reasons"], ["m-a"])
        store = MemStore()
        with self.assertRaises(ValueError):
            self.plan(["ref-a"], opening="Clerk", store=store)
        self.assertEqual(store.data, {})

    def test_validation(self):
        for refs in ([], ["ref-a", "ref-a"], ["nope"], "ref-a", [""]):
            with self.assertRaises(ValueError):
                self.plan(refs)
        with self.assertRaises(ValueError):
            self.plan(["ref-a"], opening=" ")

    def test_no_slots_creates_nothing(self):
        gw = FakeGateway()
        gw.slots = []
        with self.assertRaises(ValueError):
            self.plan(["ref-a"], gw=gw)

    def test_stored_batch_has_no_eeo_fields(self):
        batch, _, store = self.plan(["ref-a"])
        self.assertEqual(store.load(batch["batch_id"]), batch)
        text = json.dumps(store.data, default=str)
        for secret in ("SECRET-AA", "SECRET-RACE", "SECRET-KEY", "SECRET-SRC"):
            self.assertNotIn(secret, text)

    def test_store_is_required(self):
        with self.assertRaises(TypeError):
            ex.plan_outreach(["ref-a"], "Tech", "phone", "Office", 30, gateway=FakeGateway(), now=NOW)


class RosterPagingTests(unittest.TestCase):
    def test_pages_past_200_rows(self):
        rows = [
            {"agent_ref": f"r{i}", "name": "N", "position": "Tech", "submitted": "2026-09-20",
             "status": "New", "county": "Kent", "city": "Dover"}
            for i in range(450)
        ]

        def paged(status=None, limit=50, offset=0):
            page = rows[offset:offset + limit]
            return {"count": len(page), "results": page}

        with patch.object(ex.rtec_applicants, "list_applicants", side_effect=paged) as lst:
            roster = ex._reviewable_applicants()
        self.assertEqual(len(roster), 450)
        self.assertEqual(lst.call_count, 3)


if __name__ == "__main__":
    unittest.main()
