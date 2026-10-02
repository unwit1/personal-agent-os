from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.gateway import (
    DashboardGatewayError,
    LocalDashboardGateway,
    SyntheticDashboardGateway,
)


def _synthetic(status="New"):
    return SyntheticDashboardGateway(
        [{"applicant_ref": "a1", "name": "Test", "status": status}],
        managers_by_county={"Pulaski": {"name": "Mgr", "email": "m@example.invalid", "phone": "x"},
                            "Empty": {"name": "No Email", "email": ""}},
    )


class SyntheticStatusTests(unittest.TestCase):
    def test_outreach_sets_interested_from_new(self):
        g = _synthetic()
        jid = g.record_applicant_sent("a1", "outreach", "t@example.invalid", "Hi")
        self.assertTrue(jid)
        self.assertEqual(g.applicants["a1"]["status"], "Interested")
        self.assertEqual(g.calls[-1][0], "record_applicant_sent")

    def test_other_statuses_kept(self):
        g = _synthetic("Interviewing")
        g.record_applicant_sent("a1", "outreach", "t@example.invalid", "Hi")
        g.record_applicant_sent("a1", "interview", "t@example.invalid", "Hi")
        g.record_applicant_sent("a1", "manager", "m@example.invalid", "Hi")
        self.assertEqual(g.applicants["a1"]["status"], "Interviewing")
        self.assertEqual(len(g.status_log), 3)

    def test_interview_sets_requested(self):
        g = _synthetic()
        g.record_applicant_sent("a1", "interview", "t@example.invalid", "Hi")
        self.assertEqual(g.applicants["a1"]["status"], "Interview Requested")

    def test_bad_arguments(self):
        g = _synthetic()
        with self.assertRaises(ValueError):
            g.record_applicant_sent("a1", "reply", "t@example.invalid", "Hi")
        with self.assertRaises(KeyError):
            g.record_applicant_sent("nope", "outreach", "t@example.invalid", "Hi")
        with self.assertRaises(KeyError):
            g.set_applicant_status("nope", "Denied", "no")
        with self.assertRaises(ValueError):
            g.set_applicant_status("a1", "Bogus", "no")
        with self.assertRaises(ValueError):
            g.set_applicant_status("a1", None, "x" * 501)

    def test_decline_and_hold(self):
        g = _synthetic()
        g.set_applicant_status("a1", None, "Hold for now")
        self.assertEqual(g.applicants["a1"]["status"], "New")
        g.set_applicant_status("a1", "Denied", "Declined")
        self.assertEqual(g.applicants["a1"]["status"], "Denied")
        self.assertEqual([e["status"] for e in g.status_log], [None, "Denied"])

    def test_manager_for_county(self):
        g = _synthetic()
        self.assertEqual(g.manager_for_county("pulaski"), {"name": "Mgr", "email": "m@example.invalid"})
        self.assertIsNone(g.manager_for_county("Empty"))
        self.assertIsNone(g.manager_for_county("Other"))
        with self.assertRaises(ValueError):
            g.manager_for_county(" ")


class LocalStatusTests(unittest.TestCase):
    def _gateway(self, status="New"):
        calls = []
        database = types.SimpleNamespace(
            set_status=lambda key, st: calls.append(("set_status", key, st)),
            add_journal_entry=lambda key, text: calls.append(("journal", key, text)) or 42,
        )
        managers = types.SimpleNamespace(
            manager_for_county=lambda c: {"name": "Mgr", "email": "m@example.invalid", "phone": "1"})
        modules = {"database": database, "area_managers": managers}
        patches = [
            patch.object(LocalDashboardGateway, "_module", staticmethod(lambda n: modules[n])),
            patch.object(LocalDashboardGateway, "_raw",
                         lambda self, ref: {"applicant_key": "private-key", "status": status}),
            patch("sqlite3.connect", side_effect=AssertionError("sqlite used")),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        return LocalDashboardGateway(), calls

    def test_record_sent_uses_key(self):
        g, calls = self._gateway()
        self.assertEqual(g.record_applicant_sent("a1", "outreach", "t@example.invalid", "Hi"), "42")
        self.assertEqual(calls[0], ("set_status", "private-key", "Interested"))
        self.assertEqual(calls[1][:2], ("journal", "private-key"))
        self.assertNotIn("private-key", calls[1][2])

    def test_record_sent_manager_only_journals(self):
        g, calls = self._gateway()
        g.record_applicant_sent("a1", "manager", "m@example.invalid", "Hi")
        self.assertEqual([c[0] for c in calls], ["journal"])

    def test_set_status(self):
        g, calls = self._gateway()
        g.set_applicant_status("a1", "Denied", "Declined")
        self.assertEqual(calls[0], ("set_status", "private-key", "Denied"))
        g.set_applicant_status("a1", None, "Hold")
        self.assertEqual([c[0] for c in calls], ["set_status", "journal", "journal"])
        with self.assertRaises(ValueError):
            g.set_applicant_status("a1", "Bogus", "x")

    def test_missing_dashboard_function(self):
        g, _ = self._gateway()
        with patch.object(LocalDashboardGateway, "_module", staticmethod(lambda n: types.SimpleNamespace())):
            with self.assertRaises(DashboardGatewayError):
                g.set_applicant_status("a1", "Denied", "x")
            with self.assertRaises(DashboardGatewayError):
                g.manager_for_county("Pulaski")

    def test_manager_projection(self):
        g, _ = self._gateway()
        self.assertEqual(g.manager_for_county("Pulaski"), {"name": "Mgr", "email": "m@example.invalid"})


if __name__ == "__main__":
    unittest.main()
