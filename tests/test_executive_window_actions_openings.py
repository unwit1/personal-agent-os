import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import unittest
from unittest import mock

from agent_os.executive import applicants
from agent_os.executive.gateway import SyntheticDashboardGateway
from agent_os.executive.window import actions_openings
from agent_os.executive.window.registry import Registry


class ParseTests(unittest.TestCase):
    def test_variants(self):
        cases = {
            "We closed the opening in Example": ("Example", "close"),
            "we closed the opening in Example County.": ("Example", "close"),
            "A driver quit in Example county": ("Example", "quit"),
            "we have a new opening in Example": ("Example", "new"),
            "NEW DRIVER OPENING IN Big Town": ("Big Town", "new"),
        }
        for text, (county, change) in cases.items():
            self.assertEqual(
                actions_openings.parse_opening_event(text), {"county": county, "change": change}, text
            )

    def test_non_matches(self):
        for text in ["", "hello there", "did we close the opening in Example?", "send an email to Bob"]:
            self.assertIsNone(actions_openings.parse_opening_event(text), text)


class ActionTests(unittest.TestCase):
    def setUp(self):
        self.gateway = SyntheticDashboardGateway(
            openings={"Example": {"open_count": 1, "group_label": "g"}}
        )
        for patcher in (
            mock.patch.object(actions_openings, "GATEWAY", self.gateway),
            mock.patch.object(applicants.rtec_applicants, "_audit_access", lambda *a, **k: None),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.registry = Registry()
        actions_openings.register(self.registry)

    def test_registered(self):
        action = self.registry.actions()[0]
        self.assertEqual(action["id"], "openings.event")
        self.assertTrue(action["consequential"])
        self.assertEqual(action["applies_to"], "*")

    def test_preview_does_not_save(self):
        out = actions_openings.openings_event({}, {"text": "a driver quit in Example"}, confirm=False)
        self.assertEqual(out["after"]["open_count"], 2)
        self.assertEqual(self.gateway.openings["Example"]["open_count"], 1)
        self.assertNotIn("apply_opening_change", [c[0] for c in self.gateway.calls])

    def test_confirm_saves_and_refreshes(self):
        out = actions_openings.openings_event({}, {"county": "Example", "change": "new"}, confirm=True)
        self.assertEqual(self.gateway.openings["Example"]["open_count"], 2)
        self.assertTrue(out["applied"]["applied"])
        self.assertEqual(out["county_group"]["county"], "Example")

    def test_unknown_change(self):
        with self.assertRaises(ValueError):
            actions_openings.openings_event({}, {"county": "Example", "change": "explode"}, confirm=False)


if __name__ == "__main__":
    unittest.main()
