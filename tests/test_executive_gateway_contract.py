import sys
import types
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import gateway as gw


# Signatures copied from the real Applicant Dashboard. Keyword defaults and no
# **kwargs, so a positional mix-up fails the same way it does in production.
def suggest_slots(manager, duration_minutes=60, now=None, count=3, exclude_applicant_key=None):
    start = now if now is not None else datetime(2026, 10, 20, 9, 0)
    return [(start + timedelta(days=i), f"{manager}:{duration_minutes}") for i in range(count)]


def render_outreach(name, position, slots, interview_type='phone', location='', duration_minutes=30,
                    message='', template=None, position_overview='', county=''):
    return (f"{name}|{position}|{len(slots)}|{interview_type}|{location}|{duration_minutes}|"
            f"{message}|{template}|{position_overview}|{county}", "body")


class DashboardContractTests(unittest.TestCase):
    def setUp(self):
        self.calendar = types.ModuleType("interview_calendar")
        self.calendar.suggest_slots = suggest_slots
        self.outreach = types.ModuleType("interview_outreach")
        self.outreach.render_outreach = render_outreach
        modules = {"interview_calendar": self.calendar, "interview_outreach": self.outreach}
        patcher = mock.patch.object(gw.LocalDashboardGateway, "_module", staticmethod(lambda name: modules[name]))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.gateway = gw.LocalDashboardGateway()

    def test_suggest_slots_passes_count_and_duration_by_keyword(self):
        slots = self.gateway.suggest_slots("Mgr", 45, 2)
        self.assertEqual(len(slots), 2)
        self.assertEqual(slots[0][1], "Mgr:45")
        self.assertIsInstance(slots[0][0], datetime)

    def test_render_outreach_routes_county_and_fields_to_their_parameters(self):
        subject, body = self.gateway.render_outreach(
            "Ada", "Driver", ["s1", "s2"], "in-person", "Depot", 30, "Hi", "Sussex")
        self.assertEqual(subject, "Ada|Driver|2|in-person|Depot|30|Hi|None||Sussex")
        self.assertEqual(body, "body")


if __name__ == "__main__":
    unittest.main()
