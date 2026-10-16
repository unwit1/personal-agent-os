from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import applicants as ex

EEO = {
    "aa_pdf_path": "SECRET-AA.pdf",
    "race": "SECRET-RACE",
    "applicant_key": "SECRET-KEY",
    "source_key": "SECRET-SRC",
}
ROWS = {
    "New": [
        {"agent_ref": "ref-a", "name": "Ann", "position": "Tech", "submitted": "2026-09-20", "status": "New", "county": "Kent", "city": "Dover"},
        {"agent_ref": "ref-b", "name": "Bo", "position": "Tech", "submitted": "2026-09-25", "status": "New", "county": "Kent", "city": "Dover"},
    ],
    "Interested": [
        {"agent_ref": "ref-c", "name": "Cy", "position": "Clerk", "submitted": "2026-09-30", "status": "Interested", "county": "Sussex", "city": "Lewes"},
    ],
}
MATCHES = {
    "ref-a": {"match": "Tech", "pending": False, "alternates": [], "reasons": ["m-a"]},
    "ref-b": {"match": "Tech", "pending": False, "alternates": [], "reasons": ["m-b"]},
    "ref-c": {"match": "Clerk", "pending": False, "alternates": ["Tech"], "reasons": ["m-c"]},
}


def list_applicants(status=None, limit=50, offset=0):
    rows = [r for group in ROWS.values() for r in group]
    if status:
        rows = [r for r in rows if r["status"] == status]
    rows = rows[offset:offset + limit]
    return {"count": len(rows), "results": [dict(r) for r in rows]}


def review(score, rec="interview"):
    return {
        "score": score,
        "recommendation": rec,
        "result_json": {
            "summary": f"s{score}",
            "strengths": ["st"],
            "concerns": ["co"],
            "criteria": [{"criterion": "c1", "met": "yes", "evidence": "ev"}],
        },
    }


class FakeGateway:
    def __init__(self, reviews=None):
        self.calls = []
        self.reviews = reviews or {}
        self.matches = dict(MATCHES)

    def ranked(self, min_score=0):
        self.calls.append("ranked")
        out = []
        for rows in ROWS.values():
            for r in rows:
                if r["agent_ref"] in self.reviews:
                    out.append(({k: v for k, v in r.items() if k != "agent_ref"} | {"applicant_ref": r["agent_ref"]} | EEO, self.reviews[r["agent_ref"]]))
        return out

    def match_for(self, ref):
        self.calls.append("match_for")
        return self.matches[ref]


class SuggestionTests(unittest.TestCase):
    def go(self, gw, opening="Tech"):
        with patch.object(ex.rtec_applicants, "list_applicants", side_effect=list_applicants), \
                patch.object(ex.rtec_applicants, "_audit_access") as audit:
            return ex.suggestions(opening, gateway=gw), audit

    def test_score_order_label_reasons_and_unreviewed(self):
        gw = FakeGateway({"ref-a": review(60, "maybe"), "ref-c": review(90)})
        out, audit = self.go(gw)
        top = out["suggestions"][0]
        self.assertEqual(top["label"], "Dashboard AI review: advisory; you decide")
        self.assertEqual(top["score"], 90)
        self.assertEqual(top["recommendation"], "interview")
        self.assertEqual(top["match_reasons"], ["m-c"])
        self.assertEqual(top["review_reasons"]["strengths"], ["st"])
        self.assertEqual(top["review_reasons"]["criteria"][0]["met"], "yes")
        self.assertEqual(out["unreviewed_matching_count"], 1)
        # Unreviewed fit follows the reviewed ones with score None.
        self.assertEqual([s["applicant_ref"] for s in out["suggestions"]], ["ref-c", "ref-a", "ref-b"])
        self.assertIsNone(out["suggestions"][-1]["score"])
        audit.assert_called_once()

    def test_non_matching_and_pending_excluded(self):
        gw = FakeGateway({"ref-a": review(60), "ref-c": review(90)})
        out, _ = self.go(gw, "Clerk")
        self.assertEqual([s["applicant_ref"] for s in out["suggestions"]], ["ref-c"])
        self.assertEqual(out["unreviewed_matching_count"], 0)
        gw.matches["ref-b"] = {"match": "Tech", "pending": True, "alternates": [], "reasons": []}
        out, _ = self.go(gw)
        self.assertEqual(out["unreviewed_matching_count"], 0)

    def test_no_reviews_creates_none(self):
        gw = FakeGateway()
        out, _ = self.go(gw)
        self.assertEqual([s["score"] for s in out["suggestions"]], [None] * 3)
        self.assertEqual(out["unreviewed_matching_count"], 3)
        self.assertEqual(set(gw.calls), {"ranked", "match_for"})

    def test_audit_failure_fails_closed(self):
        with patch.object(ex.rtec_applicants, "list_applicants", side_effect=list_applicants), \
                patch.object(ex.rtec_applicants, "_audit_access", side_effect=RuntimeError("audit")):
            with self.assertRaises(RuntimeError):
                ex.suggestions("Tech", gateway=FakeGateway())

    def test_eeo_fields_absent_and_audit_privacy(self):
        gw = FakeGateway({"ref-a": review(60)})
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(ex.rtec_applicants, "list_applicants", side_effect=list_applicants), \
                patch.object(ex.rtec_applicants, "_AUDIT_PATH", Path(tmp) / "audit.jsonl"):
            out = ex.suggestions("Tech", gateway=gw)
            audit_text = (Path(tmp) / "audit.jsonl").read_text()
        text = json.dumps(out) + audit_text
        for secret in ("SECRET-AA", "SECRET-RACE", "SECRET-KEY", "SECRET-SRC"):
            self.assertNotIn(secret, text)
        self.assertNotIn("Ann", audit_text)


REAL_ROWS = {
    "New": [
        {"agent_ref": "ref-d", "name": "Dee", "position": "Transit Driver", "submitted": "2026-09-20", "status": "New", "county": "Laurel", "city": "X"},
        {"agent_ref": "ref-e", "name": "Eli", "position": "Dispatcher", "submitted": "2026-09-21", "status": "New", "county": "Laurel", "city": "X"},
        {"agent_ref": "ref-f", "name": "Fay", "position": "Transit Driver", "submitted": "2026-09-22", "status": "New", "county": "Knox", "city": "X"},
    ],
}


def real_match(primary, alternates=(), match=True, pending=False):
    return {
        "match": match, "pending": pending, "primary": primary, "primary_minutes": 20,
        "alternates": [{"group": g, "minutes": 40, "applied": False} for g in alternates],
        "reasons": ["near " + str(primary)], "groups": [primary] if primary else [], "group_label": str(primary),
        "manager": None,
    }


class RealShapeTests(unittest.TestCase):
    def go(self, opening):
        matches = {
            "ref-d": real_match("Laurel", ["Knox"]),
            "ref-e": real_match("Laurel"),
            "ref-f": real_match("Knox"),
        }
        gw = FakeGateway({"ref-d": review(91), "ref-e": review(84)})
        gw.matches = matches
        rows = [r for group in REAL_ROWS.values() for r in group]

        def list_real(status=None, limit=50, offset=0):
            picked = [r for r in rows if not status or r["status"] == status][offset:offset + limit]
            return {"count": len(picked), "results": [dict(r) for r in picked]}

        def ranked(min_score=0):
            return [({k: v for k, v in r.items() if k != "agent_ref"} | {"applicant_ref": r["agent_ref"]}, gw.reviews[r["agent_ref"]])
                    for r in rows if r["agent_ref"] in gw.reviews]

        gw.ranked = ranked
        with patch.object(ex.rtec_applicants, "list_applicants", side_effect=list_real), \
                patch.object(ex.rtec_applicants, "_audit_access"):
            return ex.suggestions(opening, gateway=gw)

    def refs(self, opening):
        return [s["applicant_ref"] for s in self.go(opening)["suggestions"]]

    def test_bus_driver_maps_to_transit_driver(self):
        self.assertEqual(self.refs("Bus Driver"), ["ref-d", "ref-f"])

    def test_dispatcher_position(self):
        self.assertEqual(self.refs("Dispatcher"), ["ref-e"])

    def test_county_with_suffix(self):
        self.assertEqual(self.refs("Laurel County"), ["ref-d", "ref-e", ])
        self.assertEqual(self.refs("laurel"), ["ref-d", "ref-e"])
        self.assertEqual(self.go("Laurel County")["opening"], "Laurel")

    def test_alternate_group_and_pending(self):
        self.assertEqual(self.refs("Knox"), ["ref-d", "ref-f"])
        self.assertFalse(ex._fits(real_match("Laurel", pending=True), "Laurel"))
        self.assertFalse(ex._fits(real_match("Laurel", match=False), "Laurel"))

    def test_fits_position_needs_applicant_position(self):
        self.assertFalse(ex._fits(real_match("Laurel"), "Dispatcher", "Transit Driver"))
        self.assertTrue(ex._fits(real_match("Laurel"), "customer service representative", "CSR"))


if __name__ == "__main__":
    unittest.main()
