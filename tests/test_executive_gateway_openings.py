import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import gateway as gw


class FakeDriveTimes:
    @staticmethod
    def group_names():
        return ["Alpha", "Beta", "Gamma"]


class FakeOpenings:
    """Mirrors the Dashboard's openings.py: open Transit Driver groups are a
    list, office positions are company-wide booleans, and save_settings takes
    them positionally."""

    dt = FakeDriveTimes

    def __init__(self):
        self.groups = ["Alpha", "Gamma"]
        self.office = {"Garage Attendant": False, "Dispatcher": True, "CSR": False}
        self.saved = []

    def load_settings(self):
        return {"transit_driver_groups": list(self.groups), "office_positions": dict(self.office),
                "max_drive_minutes": 30, "nearby_offer_minutes": 30}

    def save_settings(self, transit_driver_groups, office_positions, max_drive_minutes, nearby_offer_minutes=None):
        self.saved.append((list(transit_driver_groups), dict(office_positions), max_drive_minutes, nearby_offer_minutes))
        self.groups = list(transit_driver_groups)
        self.office = dict(office_positions)
        return True


class LocalOpeningsTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeOpenings()
        patcher = mock.patch.object(gw.LocalDashboardGateway, "_module", staticmethod(lambda name: self.fake))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.gateway = gw.LocalDashboardGateway()

    def test_open_counties_are_the_open_groups(self):
        rows = self.gateway.open_counties(date(2026, 10, 2))
        self.assertEqual(rows, [
            {"county": "Alpha", "open_count": 1, "group_label": "Alpha"},
            {"county": "Gamma", "open_count": 1, "group_label": "Gamma"}])

    def test_preview_does_not_save(self):
        preview = self.gateway.preview_opening_change("Beta County", "new")
        self.assertEqual(preview["before"]["open_count"], 0)
        self.assertEqual(preview["after"]["open_count"], 1)
        self.assertIn("from closed to open", preview["summary"])
        self.assertEqual(self.fake.saved, [])

    def test_close_removes_the_group_and_keeps_other_settings(self):
        result = self.gateway.apply_opening_change("gamma", "close")
        self.assertEqual(self.fake.saved, [(["Alpha"], {"Garage Attendant": False, "Dispatcher": True, "CSR": False}, 30, 30)])
        self.assertTrue(result["applied"])
        self.assertEqual(result["before"]["open_count"], 1)
        self.assertEqual(result["after"]["open_count"], 0)
        self.assertIsNone(result["group"])

    def test_quit_or_new_opens_a_closed_group(self):
        result = self.gateway.apply_opening_change("Beta", "quit")
        self.assertEqual(self.fake.groups, ["Alpha", "Gamma", "Beta"])
        self.assertEqual(result["after"]["open_count"], 1)
        self.assertEqual(result["group"]["group_label"], "Beta")

    def test_quit_in_an_open_group_keeps_it_open(self):
        preview = self.gateway.preview_opening_change("Alpha", "quit", count=3)
        self.assertEqual(preview["after"]["open_count"], 1)
        result = self.gateway.apply_opening_change("Alpha", "quit")
        self.assertEqual(sorted(self.fake.groups), ["Alpha", "Gamma"])
        self.assertEqual(result["after"]["open_count"], 1)

    def test_errors_do_not_save(self):
        with self.assertRaises(ValueError):
            self.gateway.apply_opening_change("Beta", "close")
        with self.assertRaises(ValueError):
            self.gateway.apply_opening_change("Nowhere", "new")
        with self.assertRaises(ValueError):
            self.gateway.apply_opening_change("Alpha", "explode")
        with self.assertRaises(ValueError):
            self.gateway.apply_opening_change("Alpha", "new", count=21)
        self.assertEqual(self.fake.saved, [])

    def test_failed_save_is_reported(self):
        self.fake.save_settings = lambda *a, **k: False
        with self.assertRaises(gw.DashboardGatewayError):
            self.gateway.apply_opening_change("Beta", "new")


class SyntheticOpeningsTests(unittest.TestCase):
    def setUp(self):
        self.gateway = gw.SyntheticDashboardGateway(
            openings={"Alpha": {"open_count": 1, "group_label": "Alpha Transit"}, "Beta": 0})

    def test_flow_and_calls(self):
        self.assertEqual(self.gateway.open_counties(),
                         [{"county": "Alpha", "open_count": 1, "group_label": "Alpha Transit"}])
        preview = self.gateway.preview_opening_change("Alpha", "quit")
        self.assertEqual(preview["after"]["open_count"], 2)
        self.assertEqual(self.gateway.open_counties()[0]["open_count"], 1)
        self.gateway.apply_opening_change("Alpha", "quit")
        self.assertEqual(self.gateway.open_counties()[0]["open_count"], 2)
        self.gateway.apply_opening_change("Alpha", "close")
        self.assertEqual(self.gateway.open_counties(), [])
        self.assertIn("apply_opening_change", [name for name, _ in self.gateway.calls])

    def test_errors(self):
        with self.assertRaises(ValueError):
            self.gateway.apply_opening_change("Beta", "close")
        with self.assertRaises(ValueError):
            self.gateway.preview_opening_change("Nowhere", "new")
        self.assertEqual(self.gateway.apply_opening_change("Beta", "quit")["after"]["open_count"], 1)


if __name__ == "__main__":
    unittest.main()
