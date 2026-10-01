from __future__ import annotations

import sqlite3
import sys
import tempfile
import types
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import rtec_applicants
from agent_os.executive.gateway import LocalDashboardGateway


class LocalGatewayTests(unittest.TestCase):
    def test_lazy_modules_and_opaque_ref(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            conn = sqlite3.connect(root / "dashboard.db")
            conn.execute("CREATE TABLE applicants (applicant_key TEXT, agent_ref TEXT, name TEXT, status TEXT, email TEXT)")
            conn.execute("INSERT INTO applicants VALUES ('private-key', 'app-test', 'Test Person', 'New', 'test@example.invalid')")
            conn.commit()
            conn.close()
            raw = {"applicant_key": "private-key", "name": "Test Person", "status": "New",
                   "aa_pdf_path": "restricted.pdf", "source_key": "private-source"}
            called = []

            def fake_import(name):
                called.append(name)
                if name == "candidate_review":
                    return types.SimpleNamespace(ranked=lambda min_score: [(raw, {"score": 75,
                        "recommendation": "maybe", "result_json": '{"summary":"Good"}'})])
                if name == "opening_match":
                    def match_for(applicant):
                        self.assertNotIn("aa_pdf_path", applicant)
                        self.assertNotIn("source_key", applicant)
                        return {"match": True, "reasons": ["Fit"], "source_key": "private-source"}
                    return types.SimpleNamespace(match_for=match_for)
                if name == "interview_calendar":
                    return types.SimpleNamespace(manager_for_applicant=lambda applicant: "Manager",
                        suggest_slots=lambda manager, duration, count: [(datetime(2026, 10, 5, 10), "free")])
                if name == "interview_outreach":
                    return types.SimpleNamespace(render_outreach=lambda *args: ("Subject", "Body"),
                        record_outreach_drafted=lambda *args: "draft-1")
                if name == "email_sender":
                    return types.SimpleNamespace(send_now=lambda *args: "email-1")
                raise AssertionError(name)

            with patch.object(rtec_applicants, "_project_root", return_value=root), \
                 patch("agent_os.executive.gateway.importlib.import_module", side_effect=fake_import):
                gateway = LocalDashboardGateway()
                self.assertEqual(called, [])
                applicant, review = gateway.ranked()[0]
                self.assertEqual(applicant["applicant_ref"], "app-test")
                self.assertEqual(review["score"], 75)
                self.assertNotIn("applicant_key", applicant)
                self.assertNotIn("aa_pdf_path", applicant)
                self.assertNotIn("source_key", gateway.match_for(applicant))
                manager = gateway.manager_for(applicant)
                slots = gateway.suggest_slots(manager, 30, 1)
                self.assertEqual(gateway.render_outreach("Test Person", "Driver", slots, "phone", "office", 30, "", "Test"), ("Subject", "Body"))
                self.assertEqual(gateway.record_outreach_drafted("app-test", slots, "phone", "office", 30, "draft", manager), "draft-1")
                self.assertEqual(gateway.send_now("app-test", "interview", "test@example.invalid", "Subject", "Body"), "email-1")
                self.assertNotIn("review_all", called)
                self.assertNotIn("review_applicant", called)


if __name__ == "__main__":
    unittest.main()
