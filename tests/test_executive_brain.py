from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import applicants, brain

SECRET = "SECRET-EEO"
PENDING = {
    "results": [
        {
            "applicant_ref": "ref-a",
            "name": "Ann",
            "position": "Tech",
            "status": "New",
            "submitted": "2026-09-20",
            "administrative_action": "human_review_pending",
            "aa_pdf_path": SECRET,
        }
    ]
}


class FakeStore:
    def __init__(self, batches):
        self.batches = {b["batch_id"]: b for b in batches}
        self.loads = 0

    def load(self, batch_id):
        self.loads += 1
        return self.batches[batch_id]


BATCH = {
    "batch_id": "batch-1",
    "state": "PENDING_APPROVAL",
    "opening": "Tech",
    "created_at": "2026-10-01T09:00:00",
    "items": [{"applicant_ref": "ref-a", "state": "PLANNED", "body": "x"}],
    "excluded": [],
}
NOW = datetime(2026, 10, 1)


class BrainTests(unittest.TestCase):
    def test_needs_action_deterministic_and_no_model(self):
        with patch.object(applicants.rtec_applicants, "pending_actions", return_value=PENDING):
            brn = brain.ExecutiveBrain()
            first = brn.needs_action(now=NOW)
            second = brn.needs_action(now=NOW)
        self.assertEqual(first, second)
        self.assertEqual(first["groups"][0]["items"][0]["age_days"], 11)
        self.assertNotIn(SECRET, repr(first))

    def test_batch_status(self):
        brn = brain.ExecutiveBrain(store=FakeStore([BATCH]))
        status = brn.batch_status("batch-1")
        self.assertEqual(status["state"], "PENDING_APPROVAL")
        self.assertEqual(status["item_states"], {"PLANNED": 1})
        self.assertNotIn("body", repr(status))
        with self.assertRaises(ValueError):
            brain.ExecutiveBrain().batch_status("batch-1")

    def test_briefing_skips_suggestions_without_opening(self):
        with patch.object(applicants.rtec_applicants, "pending_actions", return_value=PENDING), \
                patch.object(applicants, "suggestions") as sug:
            out = brain.ExecutiveBrain(store=FakeStore([BATCH])).briefing(batch_ids=["batch-1"], now=NOW)
        sug.assert_not_called()
        self.assertNotIn("suggestions", out)
        self.assertEqual(out["batches"][0]["batch_id"], "batch-1")

    def test_suggestions_delegates_with_gateway(self):
        gateway = object()
        with patch.object(applicants, "suggestions", return_value={"suggestions": []}) as sug:
            brain.ExecutiveBrain(gateway=gateway).suggestions("Tech")
        sug.assert_called_once_with("Tech", gateway=gateway)

    def test_prompt_is_pure_and_whitelisted(self):
        briefing = {
            "needs_action": {
                "groups": [
                    {
                        "reason": "human_review_pending",
                        "count": 1,
                        "next_step": "Review.",
                        "items": [{"applicant_ref": "ref-a", "name": "Ann", "aa_pdf_path": SECRET, "age_days": 3}],
                    }
                ]
            },
            "suggestions": {
                "label": applicants.ADVISORY_LABEL,
                "opening": "Tech",
                "unreviewed_matching_count": 2,
                "suggestions": [{"applicant_ref": "ref-a", "score": 90, "race": SECRET}],
            },
            "batches": [brain.batch_status(BATCH)],
        }
        with patch.object(applicants, "suggestions") as sug, \
                patch.object(applicants.rtec_applicants, "pending_actions") as pend:
            text = brain.build_prompt(briefing, question="Who first?")
        sug.assert_not_called()
        pend.assert_not_called()
        self.assertNotIn(SECRET, text)
        self.assertIn("ref-a", text)
        self.assertIn("Who first?", text)

    def test_no_implicit_model_or_send_calls(self):
        source = Path(brain.__file__).read_text(encoding="utf-8")
        for forbidden in ("review_all", "review_applicant", "send_now", "send_batch", "urllib", "requests", "anthropic", "openai"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
