from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.gateway import SyntheticDashboardGateway
from agent_os.executive.window import actions_applicant_decisions as mod
from agent_os.executive.window.confirm import PendingStore
from agent_os.executive.window.registry import Registry

RESTRICTED = {
    "race": "EEO_LEAK_RACE_1",
    "gender": "EEO_LEAK_GENDER_1",
    "veteran_status": "EEO_LEAK_VET_1",
    "disability": "EEO_LEAK_DIS_1",
    "self_id": "EEO_LEAK_SELFID_1",
    "aa_pdf_path": "EEO_LEAK_PDF_1",
    "applicant_key": "EEO_LEAK_KEY_1",
}
ITEM = {"id": "county:kent", "kind": "county_openings"}


def _gateway() -> SyntheticDashboardGateway:
    applicant = {
        "agent_ref": "ref-a", "name": "Ann", "position": "Tech", "submitted": "2026-09-20",
        "status": "New", "county": "Kent", "city": "Dover", "email": "ann@example.test",
        "match": {"match": "Tech", "alternates": [], "reasons": ["County fit"], "group_label": "Kent"},
        **RESTRICTED,
    }
    result = {"summary": "Relevant", "strengths": ["Experience"], "concerns": [],
              "criteria": [{"criterion": "License", "met": True, "evidence": "Held", **RESTRICTED}],
              **RESTRICTED}
    review = {"score": 90, "recommendation": "interview", "result_json": result, **RESTRICTED}
    return SyntheticDashboardGateway(applicants=[applicant], reviews={"ref-a": review})


class ApplicantDecisionTests(unittest.TestCase):
    def setUp(self):
        self.gateway = _gateway()
        mod.GATEWAY_FACTORY = lambda: self.gateway
        self.addCleanup(setattr, mod, "GATEWAY_FACTORY", None)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pending = PendingStore(home=self.tmp.name)
        self.registry = Registry()
        mod.register(self.registry)

    def _writes(self):
        return [c for c in self.gateway.calls if c[0] == "set_applicant_status"]

    def test_registration(self):
        actions = {a["id"]: a for a in self.registry.actions()}
        self.assertEqual(set(actions), {"applicant.review", "applicant.decline", "applicant.hold"})
        self.assertFalse(actions["applicant.review"]["consequential"])
        for key in ("applicant.decline", "applicant.hold"):
            self.assertTrue(actions[key]["consequential"])
        for action in actions.values():
            self.assertEqual(action["applies_to"], ["county_openings"])
            self.assertTrue(action["params_schema"])

    def test_preview_makes_no_write(self):
        for action_id, status in (("applicant.decline", "Denied"), ("applicant.hold", None)):
            result = self.registry.invoke(action_id, ITEM, {"applicant_ref": "ref-a"}, self.pending)
            self.assertEqual(result["status"], "needs_confirmation")
            self.assertEqual(result["preview"], {"applicant_ref": "ref-a", "name": "Ann", "new_status": status})
        self.assertEqual(self._writes(), [])
        self.assertEqual(self.gateway.status_log, [])

    def test_confirm_writes_once(self):
        result = self.registry.invoke("applicant.decline", ITEM, {"applicant_ref": "ref-a"}, self.pending)
        done = self.registry.confirm(result["confirm_token"], self.pending)
        self.assertTrue(done["declined"])
        self.assertEqual(len(self._writes()), 1)
        self.assertEqual(self._writes()[0][1][:2], ("ref-a", "Denied"))
        self.assertEqual(self.gateway.applicants["ref-a"]["status"], "Denied")

    def test_hold_confirm_records_note_only(self):
        result = self.registry.invoke("applicant.hold", ITEM, {"applicant_ref": "ref-a"}, self.pending)
        done = self.registry.confirm(result["confirm_token"], self.pending)
        self.assertTrue(done["held"])
        self.assertEqual(len(self._writes()), 1)
        self.assertIsNone(self._writes()[0][1][1])
        self.assertEqual(self.gateway.applicants["ref-a"]["status"], "New")

    def test_review_omits_eeo(self):
        result = self.registry.invoke("applicant.review", ITEM, {"applicant_ref": "ref-a"}, self.pending)
        self.assertEqual(result["status"], "done")
        panel = result["result"]
        self.assertEqual(panel["name"], "Ann")
        self.assertEqual(panel["email"], "ann@example.test")
        self.assertEqual(panel["score"], 90)
        self.assertEqual(panel["criteria"], [{"criterion": "License", "met": True, "evidence": "Held"}])
        ids = [d["action_id"] for d in panel["available_decisions"]]
        self.assertEqual(ids, ["applicant.reach_out", "applicant.invite_interview",
                               "applicant.email_manager", "applicant.decline", "applicant.hold"])
        text = json.dumps(panel)
        for key, value in RESTRICTED.items():
            self.assertNotIn(value, text)
            self.assertNotIn(f'"{key}"', text)

    def test_missing_ref_rejected(self):
        with self.assertRaises(ValueError):
            self.registry.invoke("applicant.review", ITEM, {}, self.pending)
        with self.assertRaises(KeyError):
            self.registry.invoke("applicant.review", ITEM, {"applicant_ref": "nope"}, self.pending)


if __name__ == "__main__":
    unittest.main()
