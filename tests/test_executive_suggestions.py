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
    rows = ROWS.get(status, [])
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
        self.assertEqual([s["applicant_ref"] for s in out["suggestions"]], ["ref-c", "ref-a"])
        top = out["suggestions"][0]
        self.assertEqual(top["label"], "Dashboard AI review: advisory; you decide")
        self.assertEqual(top["score"], 90)
        self.assertEqual(top["recommendation"], "interview")
        self.assertEqual(top["match_reasons"], ["m-c"])
        self.assertEqual(top["review_reasons"]["strengths"], ["st"])
        self.assertEqual(top["review_reasons"]["criteria"][0]["met"], "yes")
        self.assertEqual(out["unreviewed_matching_count"], 1)
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
        self.assertEqual(out["suggestions"], [])
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


if __name__ == "__main__":
    unittest.main()
