from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import applicants as ex
from agent_os.executive.gateway import SyntheticDashboardGateway
from agent_os.executive.window import (
    actions_applicant_compose, actions_applicant_decisions, actions_executive, actions_openings,
    providers_applicants, registry,
)
from agent_os.executive.window.server import Api
from agent_os.executive.window.transport import FakeTransport

SLOT = datetime(2026, 10, 5, 9)
RESTRICTED = {
    "gender": "EEOWF_GENDER_5521", "race": "EEOWF_RACE_5521", "ethnicity": "EEOWF_ETHNIC_5521",
    "veteran": "EEOWF_VETERAN_5521", "disability": "EEOWF_DISABLED_5521",
    "self_id": "EEOWF_SELFID_5521", "eeo_class": "EEOWF_EEOCLASS_5521",
    "eeo_notes": "EEOWF_EEONOTES_5521", "eeo_json": {"k": "EEOWF_EEOJSON_5521"},
}
KEYS = list(RESTRICTED)
VALUES = ["EEOWF_GENDER_5521", "EEOWF_RACE_5521", "EEOWF_ETHNIC_5521", "EEOWF_VETERAN_5521",
          "EEOWF_DISABLED_5521", "EEOWF_SELFID_5521", "EEOWF_EEOCLASS_5521",
          "EEOWF_EEONOTES_5521", "EEOWF_EEOJSON_5521"]


def leaks(payload):
    text = json.dumps(payload, default=str)
    found = [v for v in VALUES if v in text]
    found += [k for k in KEYS if re.search(r'"%s"' % re.escape(k), text)]
    return found


def no_leak(case, payload, where):
    found = leaks(payload)
    case.assertEqual(found, [], "EEO/self-ID LEAK in %s: %s" % (where, found))


def _app(ref, county="Kent"):
    return {
        "applicant_ref": ref, "name": ref.upper(), "position": "Transit Driver", "submitted": "2026-09-20",
        "status": "New", "county": county, "city": "Dover", "email": ref + "@example.test",
        "match": dict(match="Tech", pending=False, reasons=["fits-" + ref], groups=[], **RESTRICTED),
        **RESTRICTED,
    }


def _review(score):
    criterion = dict(criterion="Has license", met=True, evidence="on resume", **RESTRICTED)
    detail = dict(summary="Solid candidate", strengths=["reliable"], concerns=["far away"],
                  criteria=[criterion], **RESTRICTED)
    return dict(score=score, recommendation="interview", result_json=detail, **RESTRICTED)


def _gateway():
    return SyntheticDashboardGateway(
        applicants=[_app("a"), _app("b")],
        reviews={"a": _review(90), "b": _review(70)},
        managers={"a": "Manager One", "b": "Manager One"},
        calendar={"Manager One": [SLOT]},
        managers_by_county={"Kent": {"name": "Mia Manager", "email": "mia@example.test"}},
        openings={"Kent": {"open_count": 1, "group_label": "g"}},
    )


class _Bridge:
    def send(self, conversation_id, text):
        return {"reply": "ok"}


class EeoWorkflowFirewallTests(unittest.TestCase):
    def setUp(self):
        self.gateway = _gateway()
        for p in (
            patch.object(ex.rtec_applicants, "_audit_access", lambda *a, **k: None),
            patch.object(ex, "_reviewable_applicants", return_value={}),
            patch.object(actions_executive, "GATEWAY_FACTORY", lambda: self.gateway),
            patch.object(actions_openings, "GATEWAY", self.gateway),
            patch.object(actions_applicant_decisions, "_gateway", lambda: self.gateway),
        ):
            p.start()
            self.addCleanup(p.stop)
        self.group = ex.county_candidates("Kent", top_n=5, gateway=self.gateway)

    def _invoke(self, module, name, **params):
        reg = registry.Registry()
        module.register(reg)
        item = {"id": "county:Kent", "kind": "county_openings",
                "context": {"county": "Kent", "applicants": self.group["applicants"]}}
        return reg.invoke(name, item, params, None)

    def test_county_candidates(self):
        self.assertTrue(self.group["applicants"])
        no_leak(self, self.group, "county_candidates")

    def test_county_items(self):
        items = providers_applicants.county_items(lambda: ex.open_county_groups(gateway=self.gateway))
        self.assertTrue(items)
        no_leak(self, items, "providers_applicants.county_items")

    def test_applicant_review(self):
        out = self._invoke(actions_applicant_decisions, "applicant.review", applicant_ref="a")
        self.assertEqual(out["status"], "done")
        no_leak(self, out, "applicant.review")

    def test_email_manager_compose(self):
        out = self._invoke(actions_applicant_compose, "applicant.email_manager", applicant_ref="a")
        compose = out["result"]["compose"]
        self.assertIn("fits-a", compose["body"])
        no_leak(self, out, "applicant.email_manager compose")
        no_leak(self, compose["body"], "applicant.email_manager body")

    def test_reach_out_and_invite_compose(self):
        for name in ("applicant.reach_out", "applicant.invite_interview"):
            out = self._invoke(actions_applicant_compose, name, applicant_ref="a")
            no_leak(self, out, name)

    def test_openings_event_refreshed_group(self):
        out = actions_openings.openings_event({}, {"county": "Kent", "change": "new"}, confirm=True)
        self.assertTrue(out["county_group"]["applicants"])
        no_leak(self, out["county_group"], "openings.event refreshed group")
        no_leak(self, out, "openings.event result")
        preview = actions_openings.openings_event({}, {"text": "a driver quit in Kent"}, confirm=False)
        no_leak(self, preview, "openings.event preview")

    def test_send_audit_omits_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = Api(registry.Registry(), _Bridge(), Path(tmp), transport=FakeTransport(),
                      gateway_factory=lambda: self.gateway)
            secret = "BODYSECRET_5521 " + RESTRICTED["gender"]
            result = api.post("/api/send", dict(
                to="a@example.test", subject="Hello", body=secret, kind="outreach",
                applicant_ref="a", county="Kent"))
            self.assertTrue(result["sent"])
            text = api.pending.audit_path.read_text(encoding="utf-8")
            self.assertTrue(text.strip())
            self.assertNotIn("BODYSECRET_5521", text, "send audit record contains the body")
            self.assertNotIn(RESTRICTED["gender"], text, "send audit record contains body text")
            for line in text.splitlines():
                self.assertNotIn("body", json.loads(line)["send"], "send audit has a body key")


if __name__ == "__main__":
    unittest.main()
