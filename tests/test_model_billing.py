"""Billing and privacy profile normalization and spend gate behavior."""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator.model_profile import allowance_summary, is_paid, normalize_profile


class ModelBillingTests(unittest.TestCase):
    def test_absent_blocks_preserve_existing_profile(self):
        profile = normalize_profile({"deployment": "api"})
        self.assertNotIn("billing", profile)
        self.assertNotIn("privacy", profile)
        self.assertTrue(is_paid({"profile": profile}))
        self.assertFalse(is_paid({"profile": normalize_profile({"deployment": "subscription"})}))
        self.assertIsNone(allowance_summary(profile))

    def test_normalizes_declared_blocks(self):
        profile = normalize_profile({
            "deployment": "api",
            "billing": {
                "mode": "allowance",
                "plan": "Pro",
                "allowance": {"unit": "prompts", "amount": 1350, "reset_window": "5h_rolling"},
                "overage": "blocked",
                "metered_triggers": ["explicit provider selection"],
            },
            "privacy": {
                "training_on_prompts": "opt_out",
                "retention": "30 days",
                "zdr": False,
                "weights_location": "third_party",
            },
        })
        self.assertEqual(profile["billing"], {
            "mode": "allowance", "plan": "Pro",
            "allowance": {"unit": "prompts", "amount": 1350, "reset_window": "5h_rolling"},
            "overage": "blocked", "metered_triggers": ["explicit provider selection"],
        })
        self.assertEqual(profile["privacy"], {
            "training_on_prompts": "opt_out", "retention": "30 days", "zdr": False,
            "weights_location": "third_party",
        })
        self.assertFalse(is_paid({"profile": profile}))
        self.assertEqual(allowance_summary(profile), "allowance 1350 prompts / 5h_rolling, overage blocked")

    def test_unknown_values_do_not_weaken_paid_gate(self):
        profile = normalize_profile({
            "deployment": "subscription",
            "billing": {
                "mode": "allowance", "allowance": {"unit": "bad", "amount": True, "reset_window": "bad"},
                "overage": "bad", "metered_triggers": "not a list",
            },
            "privacy": {"training_on_prompts": "bad", "zdr": "false", "weights_location": "bad"},
        })
        self.assertEqual(profile["billing"], {
            "mode": "allowance", "plan": None,
            "allowance": {"unit": "unknown", "amount": None, "reset_window": "unknown"},
            "overage": "unknown", "metered_triggers": [],
        })
        self.assertEqual(profile["privacy"], {
            "training_on_prompts": "unknown", "retention": None, "zdr": None,
            "weights_location": "unknown",
        })
        self.assertTrue(is_paid({"profile": profile}))

    def test_metered_modes_are_paid_on_subscription_deployments(self):
        for mode in ("metered", "credits", "per_gpu_time"):
            with self.subTest(mode=mode):
                profile = normalize_profile({"deployment": "subscription", "billing": {"mode": mode}})
                self.assertTrue(is_paid({"profile": profile}))
        profile = normalize_profile({"deployment": "subscription", "billing": {"mode": "allowance", "overage": "metered"}})
        self.assertTrue(is_paid({"profile": profile}))


if __name__ == "__main__":
    unittest.main()
