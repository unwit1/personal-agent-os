import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import gateway as gw


class FakeOpenings:
    def __init__(self):
        self.settings = {"county_openings": {"Alpha": 2, "Beta": 0, "Gamma": 1}}
        self.saved = []

    def load_settings(self):
        return {"county_openings": dict(self.settings["county_openings"])}

    def evaluate(self, settings, today=None):
        return dict(settings["county_openings"])

    def open_groups_in_range(self, settings, county, *args, **kwargs):
        return [f"{county} Transit"]

    def save_settings(self, settings):
        self.saved.append(settings)
        self.settings = settings


class LocalOpeningsTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeOpenings()
        patcher = mock.patch.object(gw.LocalDashboardGateway, "_module", staticmethod(lambda name: self.fake))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.gateway = gw.LocalDashboardGateway()

    def test_open_counties_minimal_and_sorted(self):
        rows = self.gateway.open_counties(date(2026, 10, 2))
        self.assertEqual(rows, [
            {"county": "Alpha", "open_count": 2, "group_label": "Alpha Transit"},
            {"county": "Gamma", "open_count": 1, "group_label": "Gamma Transit"}])

    def test_preview_does_not_save(self):
        preview = self.gateway.preview_opening_change("Alpha County", "quit")
        self.assertEqual(preview["before"]["open_count"], 2)
        self.assertEqual(preview["after"]["open_count"], 3)
        self.assertEqual(self.fake.saved, [])

    def test_apply_saves(self):
        result = self.gateway.apply_opening_change("gamma", "close")
        self.assertTrue(result["applied"])
        self.assertEqual(len(self.fake.saved), 1)
        self.assertEqual(self.fake.settings["county_openings"]["Gamma"], 0)
        self.assertIsNone(result["group"])
        self.assertEqual([r["county"] for r in self.gateway.open_counties()], ["Alpha"])

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

    def test_apply_without_settings_key_raises_and_does_not_save(self):
        self.fake.load_settings = lambda: {}
        self.fake.evaluate = lambda settings, today=None: {"Alpha": 2}
        with self.assertRaises(gw.DashboardGatewayError):
            self.gateway.apply_opening_change("Alpha", "quit")
        self.assertEqual(self.fake.saved, [])

    def test_new_on_closed_county_increments(self):
        result = self.gateway.apply_opening_change("Beta", "new", count=2)
        self.assertEqual(result["after"]["open_count"], 2)
        self.assertEqual(result["group"]["county"], "Beta")


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
