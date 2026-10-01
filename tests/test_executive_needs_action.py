from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import applicants as ex

NOW = datetime(2026, 10, 1, 12, 0)


class NeedsActionTests(unittest.TestCase):
    def run_it(self, results):
        payload = {"count": len(results), "results": results}
        with patch.object(ex.rtec_applicants, "pending_actions", return_value=payload):
            return ex.needs_action(now=NOW)

    def row(self, ref, action, submitted, status="New"):
        return {
            "applicant_ref": ref,
            "name": ref,
            "position": "Tech",
            "submitted": submitted,
            "status": status,
            "administrative_action": action,
        }

    def test_groups_ages_and_next_step(self):
        out = self.run_it(
            [
                self.row("r1", "human_review_pending", "2026-09-20"),
                self.row("r2", "interview_request_outstanding", "2026-09-30T08:00:00", "Interview Requested"),
                self.row("r3", "human_review_pending", "2026-09-28"),
            ]
        )
        self.assertEqual(out["count"], 3)
        self.assertEqual(
            [g["reason"] for g in out["groups"]],
            ["human_review_pending", "interview_request_outstanding"],
        )
        first = out["groups"][0]
        self.assertEqual(first["count"], 2)
        self.assertEqual([i["applicant_ref"] for i in first["items"]], ["r1", "r3"])
        self.assertEqual([i["age_days"] for i in first["items"]], [11, 3])
        self.assertEqual(out["groups"][1]["items"][0]["age_days"], 1)
        self.assertTrue(first["next_step"])
        self.assertNotIn("recommend", first["next_step"].lower())

    def test_bad_date_and_unknown_reason(self):
        out = self.run_it([self.row("r1", "weird", "not a date")])
        self.assertIsNone(out["groups"][0]["items"][0]["age_days"])
        self.assertTrue(out["groups"][0]["next_step"])

    def test_empty(self):
        self.assertEqual(self.run_it([]), {"count": 0, "groups": []})


if __name__ == "__main__":
    unittest.main()
