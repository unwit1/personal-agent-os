from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import applicants as ex
from agent_os.executive.gateway import SyntheticDashboardGateway

EEO_KEYS = ("gender", "race", "veteran", "disability")


def _app(ref, county, status="New", match=None):
    return {
        "applicant_ref": ref, "name": ref.upper(), "position": "Tech", "submitted": "2026-09-20",
        "status": status, "county": county, "city": "X",
        "gender": "SECRET", "race": "SECRET", "veteran": "SECRET", "disability": "SECRET",
        "match": match or {"match": "Tech", "pending": False, "reasons": ["r-" + ref], "groups": []},
    }


def _rev(score):
    return {"score": score, "recommendation": "interview", "summary": "s", "strengths": [], "concerns": []}


def _gateway():
    apps = [
        _app("a", "Kent"), _app("b", "Kent"), _app("c", "Kent"),
        _app("d", "Kent", status="Rejected"),
        _app("e", "Sussex", match={"match": "Tech", "pending": False, "reasons": ["g"], "groups": ["Kent"]}),
        _app("f", "Sussex"),
    ]
    reviews = {"a": _rev(60), "b": _rev(90), "c": _rev(75), "d": _rev(99), "e": _rev(80), "f": _rev(70)}
    return SyntheticDashboardGateway(applicants=apps, reviews=reviews,
                                     openings={"Kent": 2, "Sussex": 1})


class CountyCandidateTests(unittest.TestCase):
    def go(self, fn, *args, **kw):
        with patch.object(ex.rtec_applicants, "_audit_access"), \
                patch.object(ex, "_reviewable_applicants", return_value={}):
            return fn(*args, gateway=_gateway(), **kw)

    def test_ordering_and_group_fit(self):
        out = self.go(ex.county_candidates, "kent", top_n=10)
        self.assertEqual([a["applicant_ref"] for a in out["applicants"]], ["b", "e", "c", "a"])
        self.assertEqual(out["count"], 4)
        self.assertEqual(out["applicants"][0]["match_reasons"], ["r-b"])

    def test_top_n_cut(self):
        out = self.go(ex.county_candidates, "Kent", top_n=2)
        self.assertEqual([a["applicant_ref"] for a in out["applicants"]], ["b", "e"])
        self.assertEqual(out["top_n"], 2)

    def test_env_default(self):
        with patch.dict(os.environ, {"AGENT_OS_EXEC_TOP_N": "1"}):
            self.assertEqual(self.go(ex.county_candidates, "Kent")["count"], 1)
        env = {k: v for k, v in os.environ.items() if k != "AGENT_OS_EXEC_TOP_N"}
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(self.go(ex.county_candidates, "Kent")["top_n"], 5)

    def test_non_reviewable_excluded(self):
        out = self.go(ex.county_candidates, "Kent", top_n=10)
        self.assertNotIn("d", [a["applicant_ref"] for a in out["applicants"]])

    def test_no_eeo_keys(self):
        out = self.go(ex.county_candidates, "Kent", top_n=10)
        for a in out["applicants"]:
            for key in EEO_KEYS:
                self.assertNotIn(key, a)
        self.assertNotIn("SECRET", repr(out))

    def test_unreviewed_applicants_listed_after_reviewed(self):
        gateway = _gateway()
        gateway.applicants["g"] = _app("g", "Kent")  # no AI review yet
        with patch.object(ex.rtec_applicants, "_audit_access"),                 patch.object(ex, "_reviewable_applicants", return_value={}):
            out = ex.county_candidates("Kent", top_n=10, gateway=gateway)
        self.assertEqual([a["applicant_ref"] for a in out["applicants"]], ["b", "e", "c", "a", "g"])
        self.assertIsNone(out["applicants"][-1]["score"])

    def test_open_county_groups(self):
        groups = self.go(ex.open_county_groups, top_n=1)
        self.assertEqual([(g["county"], g["open_count"]) for g in groups], [("Kent", 2), ("Sussex", 1)])
        self.assertEqual(groups[1]["applicants"][0]["applicant_ref"], "e")


if __name__ == "__main__":
    unittest.main()
