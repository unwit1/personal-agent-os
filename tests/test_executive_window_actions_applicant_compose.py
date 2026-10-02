from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import applicants as ex
from agent_os.executive.gateway import SyntheticDashboardGateway
from agent_os.executive.window import actions_applicant_compose as aac
from agent_os.executive.window import actions_executive, registry

EEO = ("gender", "race", "veteran", "disability", "ethnicity", "self_id")
SLOT = datetime(2026, 10, 5, 9)


def _app(ref, county="Kent"):
    return {
        "applicant_ref": ref, "name": ref.upper(), "position": "Tech", "submitted": "2026-09-20",
        "status": "New", "county": county, "city": "Dover", "email": ref + "@example.test",
        "gender": "SECRET", "race": "SECRET", "veteran": "SECRET", "disability": "SECRET",
        "match": {"match": "Tech", "pending": False, "reasons": ["fits-" + ref], "groups": []},
    }


def _review(score):
    detail = {"summary": "Solid candidate", "strengths": ["reliable"], "concerns": ["far away"],
              "criteria": [{"criterion": "Has license", "met": True, "evidence": "on resume"}]}
    return {"score": score, "recommendation": "interview", "result_json": detail}


def _gateway(managers_by_county=None):
    return SyntheticDashboardGateway(
        applicants=[_app("a"), _app("b")],
        reviews={"a": _review(90), "b": _review(70)},
        managers={"a": "Manager One", "b": "Manager One"},
        calendar={"Manager One": [SLOT]},
        managers_by_county=managers_by_county if managers_by_county is not None
        else {"Kent": {"name": "Mia Manager", "email": "mia@example.test"}},
        openings={"Kent": 1},
    )


class ComposeActionTests(unittest.TestCase):
    def setUp(self):
        self.gateway = _gateway()
        with patch.object(ex.rtec_applicants, "_audit_access"), \
                patch.object(ex, "_reviewable_applicants", return_value={}):
            group = ex.county_candidates("Kent", top_n=5, gateway=self.gateway)
        self.item = {"id": "county:kent", "kind": "county_openings",
                     "context": {"county": "Kent", "applicants": group["applicants"]}}
        patcher = patch.object(actions_executive, "GATEWAY_FACTORY", lambda: self.gateway)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_action(self, name, **params):
        reg = registry.Registry()
        aac.register(reg)
        return reg.invoke(name, self.item, params, None)

    def assert_no_write(self):
        names = {name for name, _args in self.gateway.calls}
        self.assertFalse(names & {"send_now", "record_applicant_sent", "set_applicant_status",
                                  "record_outreach_drafted"})
        self.assertEqual(self.gateway.sent, [])
        self.assertEqual(self.gateway.status_log, [])

    def test_reach_out_payload(self):
        out = self.run_action("applicant.reach_out", applicant_ref="a")
        self.assertEqual(out["status"], "done")
        compose = out["result"]["compose"]
        self.assertEqual(compose["to"], "a@example.test")
        self.assertEqual(compose["kind"], "outreach")
        self.assertEqual(compose["applicant_ref"], "a")
        self.assertEqual(compose["county"], "Kent")
        self.assertIn("Tech", compose["subject"])
        self.assertIn("Hello A", compose["body"])
        self.assert_no_write()

    def test_invite_interview_payload(self):
        out = self.run_action("applicant.invite_interview", applicant_ref="a", location="Dover office")
        compose = out["result"]["compose"]
        self.assertEqual(compose["kind"], "interview")
        self.assertEqual(compose["to"], "a@example.test")
        self.assertEqual(compose["subject"], "Interview invitation: Tech")
        self.assertIn("Dover office", compose["body"])
        names = [name for name, _args in self.gateway.calls]
        for needed in ("manager_for", "suggest_slots", "render_outreach"):
            self.assertIn(needed, names)
        self.assert_no_write()

    def test_invite_without_manager_or_slots_raises(self):
        self.gateway.managers.clear()
        with self.assertRaises(ValueError):
            self.run_action("applicant.invite_interview", applicant_ref="a")

    def test_email_manager_has_criteria_and_no_eeo(self):
        out = self.run_action("applicant.email_manager", applicant_ref="a", note="Please call soon.")
        compose = out["result"]["compose"]
        self.assertEqual(compose["kind"], "manager")
        self.assertEqual(compose["to"], "mia@example.test")
        self.assertEqual(compose["applicant_ref"], "a")
        self.assertIn("A (Kent County)", compose["subject"])
        body = compose["body"]
        for text in ("Hello Mia Manager", "Score: 90/100", "recommendation: interview",
                     "Solid candidate", "reliable", "far away", "Has license: True (on resume)",
                     "fits-a", "Please call soon."):
            self.assertIn(text, body)
        blob = json.dumps(compose).lower()
        self.assertNotIn("secret", blob)
        for key in EEO:
            self.assertNotIn(key, compose)
        self.assert_no_write()

    def test_email_manager_requires_manager_email(self):
        self.gateway.managers_by_county.clear()
        with self.assertRaises(ValueError):
            self.run_action("applicant.email_manager", applicant_ref="a")

    def test_applicant_must_be_in_item_context(self):
        for name in ("applicant.reach_out", "applicant.invite_interview", "applicant.email_manager"):
            with self.assertRaises(ValueError):
                self.run_action(name, applicant_ref="zzz")
            with self.assertRaises(ValueError):
                self.run_action(name)

    def test_register_kinds(self):
        reg = registry.Registry()
        aac.register(reg)
        actions = {a["id"]: a for a in reg.actions()}
        self.assertEqual(set(actions), {"applicant.reach_out", "applicant.invite_interview",
                                        "applicant.email_manager"})
        for action in actions.values():
            self.assertEqual(action["applies_to"], ["county_openings"])
            self.assertFalse(action["consequential"])
            self.assertIn("applicant_ref", action["params_schema"])


if __name__ == "__main__":
    unittest.main()
