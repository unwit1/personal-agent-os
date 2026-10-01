from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.gateway import SyntheticDashboardGateway
from agent_os import rtec_applicants


class SyntheticGatewayTests(unittest.TestCase):
    def test_all_operations_and_privacy(self):
        slot = datetime(2026, 10, 5, 10)
        gateway = SyntheticDashboardGateway(
            applicants=[{
                "applicant_key": "internal-key", "agent_ref": "app-opaque", "name": "Example Person",
                "position": "Driver", "status": "New", "county": "Test", "email": "test@example.invalid",
                "aa_pdf_path": "RESTRICTED_PATH", "race": "RESTRICTED_RACE",
                "source_key": "RESTRICTED_SOURCE", "match": {"match": True, "reasons": ["County fit"]},
            }],
            reviews={"app-opaque": {"score": 80, "recommendation": "interview",
                                    "result_json": {"summary": "Relevant work", "strengths": ["Experience"]}}},
            managers={"app-opaque": "Manager One"},
            calendar={"Manager One": [slot, slot + timedelta(hours=1)]},
        )
        with patch.object(rtec_applicants, "_project_root", side_effect=AssertionError("real Dashboard discovery")), \
             patch("socket.create_connection", side_effect=AssertionError("network access")), \
             patch("agent_os.executive.gateway.importlib.import_module", side_effect=AssertionError("real Dashboard import")):
            self._exercise_gateway(gateway, slot)

    def _exercise_gateway(self, gateway, slot):
        applicant, review = gateway.ranked()[0]
        self.assertEqual(applicant["applicant_ref"], "app-opaque")
        self.assertNotIn("applicant_key", applicant)
        self.assertEqual(review["score"], 80)
        self.assertTrue(gateway.match_for(applicant)["match"])
        manager = gateway.manager_for(applicant)
        gateway.busy[manager] = [(slot, slot + timedelta(minutes=30))]
        slots = gateway.suggest_slots(manager, 30, 2)
        self.assertEqual(slots, [(slot + timedelta(hours=1), "available")])
        subject, body = gateway.render_outreach("Example Person", "Driver", slots, "phone", "office", 30, "Please reply", "Test")
        self.assertIn("Driver", subject)
        self.assertIn("Please reply", body)
        self.assertEqual(gateway.record_outreach_drafted("app-opaque", slots, "phone", "office", 30, "draft.txt", manager), "synthetic-draft-1")
        self.assertEqual(gateway.send_now("app-opaque", "interview", "test@example.invalid", subject, body), "synthetic-email-1")
        self.assertEqual([call[0] for call in gateway.calls[:7]], [
            "ranked", "match_for", "manager_for", "suggest_slots", "render_outreach",
            "record_outreach_drafted", "send_now"])
        visible = repr((applicant, review, gateway.match_for(applicant), gateway.drafts, gateway.sent))
        for secret in ("RESTRICTED_PATH", "RESTRICTED_RACE", "RESTRICTED_SOURCE", "internal-key"):
            self.assertNotIn(secret, visible)


if __name__ == "__main__":
    unittest.main()
