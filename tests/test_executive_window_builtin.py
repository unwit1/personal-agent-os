import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import unittest

from agent_os.executive.window import builtin, registry


class TestExecutiveWindowBuiltin(unittest.TestCase):
    """Tests for builtin provider and action registration."""

    def setUp(self):
        """Create a fresh registry for each test."""
        self.registry = registry.Registry()

    def test_default_registry_registers_providers(self):
        """Test that default_registry registers the expected provider names."""
        reg = builtin.default_registry()
        provider_names = set(reg._providers.keys())

        expected_providers = {"applicants", "orchestrator", "mail"}
        self.assertEqual(provider_names, expected_providers)

    def test_default_registry_registers_actions(self):
        """Test that default_registry registers all expected action IDs."""
        reg = builtin.default_registry()
        action_ids = set(reg._actions.keys())

        expected_actions = {
            "email.reply_draft",
            "email.send",
            "executive.plan_interviews",
            "executive.approve_batch",
            "executive.reach_out",
            "orchestrator.approve_gate",
            "orchestrator.decline_gate",
            "item.dismiss",
            "item.snooze",
        }
        self.assertEqual(action_ids, expected_actions)

    def test_default_registry_idempotent(self):
        """Test that calling default_registry twice does not duplicate anything."""
        reg1 = builtin.default_registry()
        provider_count_1 = len(reg1._providers)
        action_count_1 = len(reg1._actions)

        reg2 = builtin.default_registry()
        provider_count_2 = len(reg2._providers)
        action_count_2 = len(reg2._actions)

        # Should be the same registry
        self.assertIs(reg1, reg2)

        # Counts should not increase
        self.assertEqual(provider_count_1, provider_count_2)
        self.assertEqual(action_count_1, action_count_2)

    def test_consequential_flags(self):
        """Test that consequential flags are set correctly."""
        reg = builtin.default_registry()

        # These should be consequential (require confirmation)
        consequential_actions = {
            "email.send",
            "executive.reach_out",
            "orchestrator.approve_gate",
            "orchestrator.decline_gate",
        }

        for action_id in consequential_actions:
            action = reg._actions[action_id]
            self.assertTrue(
                action["consequential"],
                f"Action {action_id} should be consequential but is not",
            )

        # These should not be consequential
        non_consequential_actions = {
            "email.reply_draft",
            "executive.plan_interviews",
            "executive.approve_batch",
            "item.dismiss",
            "item.snooze",
        }

        for action_id in non_consequential_actions:
            action = reg._actions[action_id]
            self.assertFalse(
                action["consequential"],
                f"Action {action_id} should not be consequential but is",
            )


if __name__ == "__main__":
    unittest.main()
