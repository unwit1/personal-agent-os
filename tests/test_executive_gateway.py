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
            conn.execute("CREATE TABLE applicants (applicant_key TEXT, agent_ref TEXT, name TEXT, status TEXT, email TEXT, county_preference TEXT, availability TEXT, aa_pdf_path TEXT, source_key TEXT)")
            conn.execute("INSERT INTO applicants VALUES ('private-key', 'app-test', 'Test Person', 'New', 'test@example.invalid', 'Pulaski', 'weekdays', 'restricted.pdf', 'private-source')")
            conn.commit()
            conn.close()
            raw = {"applicant_key": "private-key", "name": "Test Person", "status": "New",
                   "aa_pdf_path": "restricted.pdf", "source_key": "private-source"}
            skipped = [{**raw, "applicant_key": "other", "status": "Hired"},
                       {**raw, "applicant_key": "missing"}, {"status": "New"}]
            called = []

            def forbidden(*args, **kwargs):
                raise AssertionError("AI review must not be triggered")

            def fake_import(name):
                called.append(name)
                if name == "candidate_review":
                    review = {"score": 75, "recommendation": "maybe", "result_json": '{"summary":"Good"}'}
                    return types.SimpleNamespace(
                        ranked=lambda min_score: [(row, review) for row in [raw, *skipped]],
                        review_all=forbidden, review_applicant=forbidden)
                if name == "opening_match":
                    def match_for(applicant):
                        self.assertEqual(applicant["county_preference"], "Pulaski")
                        self.assertEqual(applicant["availability"], "weekdays")
                        self.assertEqual(applicant["aa_pdf_path"], "restricted.pdf")
                        self.assertEqual(applicant["source_key"], "private-source")
                        return {"match": True, "reasons": ["Fit"], "source_key": "private-source"}
                    return types.SimpleNamespace(match_for=match_for)
                if name == "interview_calendar":
                    def manager_for(applicant):
                        self.assertEqual(applicant["county_preference"], "Pulaski")
                        self.assertEqual(applicant["availability"], "weekdays")
                        return "Manager"
                    return types.SimpleNamespace(manager_for_applicant=manager_for,
                        suggest_slots=lambda manager, duration, count: [(datetime(2026, 10, 5, 10), "free")])
                if name == "interview_outreach":
                    return types.SimpleNamespace(render_outreach=lambda *args: ("Subject", "Body"),
                        record_outreach_drafted=lambda *args: "draft-1")
                if name == "email_sender":
                    def send_now(key, kind, to_addr, subject, body):
                        self.assertEqual(key, "private-key")
                        self.assertEqual(to_addr, "test@example.invalid")
                        return "email-1"
                    return types.SimpleNamespace(send_now=send_now)
                raise AssertionError(name)

            real_connect = rtec_applicants._connect_readonly
            connections = []
            def counted_connect():
                connections.append(1)
                return real_connect()

            with patch.object(rtec_applicants, "_project_root", return_value=root), \
                 patch.object(rtec_applicants, "_connect_readonly", side_effect=counted_connect), \
                 patch("agent_os.executive.gateway.importlib.import_module", side_effect=fake_import):
                gateway = LocalDashboardGateway()
                self.assertEqual(called, [])
                ranked = gateway.ranked()
                self.assertEqual(len(ranked), 1)
                self.assertEqual(len(connections), 1)
                applicant, review = ranked[0]
                self.assertEqual(applicant["applicant_ref"], "app-test")
                self.assertEqual(applicant["county"], "Pulaski")
                self.assertEqual(applicant["email"], "test@example.invalid")
                self.assertEqual(review["score"], 75)
                self.assertNotIn("applicant_key", applicant)
                self.assertNotIn("aa_pdf_path", applicant)
                self.assertNotIn("source_key", applicant)
                self.assertNotIn("availability", applicant)
                self.assertNotIn("source_key", gateway.match_for(applicant))
                self.assertNotIn("county_preference", applicant)
                manager = gateway.manager_for(applicant)
                slots = gateway.suggest_slots(manager, 30, 1)
                self.assertEqual(gateway.render_outreach("Test Person", "Driver", slots, "phone", "office", 30, "", "Test"), ("Subject", "Body"))
                self.assertEqual(gateway.record_outreach_drafted("app-test", slots, "phone", "office", 30, "draft", manager), "draft-1")
                self.assertEqual(gateway.send_now("app-test", "interview", applicant["email"], "Subject", "Body"), "email-1")
                with self.assertRaisesRegex(KeyError, "Unknown applicant_ref"):
                    gateway.match_for({"applicant_ref": "app-unknown"})


if __name__ == "__main__":
    unittest.main()
