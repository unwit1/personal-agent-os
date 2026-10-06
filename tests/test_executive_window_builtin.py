import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import tempfile
import unittest

from agent_os.executive.window import builtin, registry


def setUpModule():
    """Keep these tests out of the repository's real Executive Event Bus log."""
    global _BUS_DIR, _PREVIOUS_BUS
    from agent_os.executive.event_bus import EventBus
    from agent_os.executive.window import builtin as _builtin, registry as _registry

    _builtin.default_registry()
    _BUS_DIR = tempfile.TemporaryDirectory()
    _PREVIOUS_BUS = _registry.REGISTRY.event_bus
    _registry.REGISTRY.attach_event_bus(EventBus(_BUS_DIR.name))


def tearDownModule():
    from agent_os.executive.window import registry as _registry

    _registry.REGISTRY.attach_event_bus(_PREVIOUS_BUS)
    _BUS_DIR.cleanup()


class TestExecutiveWindowBuiltin(unittest.TestCase):
    """Tests for builtin provider and action registration."""

    def setUp(self):
        """Create a fresh registry for each test."""
        self.registry = registry.Registry()

    def test_default_registry_registers_providers(self):
        """Test that default_registry registers the expected provider names."""
        reg = builtin.default_registry()
        provider_names = set(reg._providers.keys())

        expected_providers = {"applicants", "orchestrator", "mail", "counties", "mail_cleanup", "projects", "brain_dump", "knowledge_gaps", "memory_candidates"}
        self.assertEqual(provider_names, expected_providers)

    def test_default_registry_registers_actions(self):
        """Test that default_registry registers all expected action IDs."""
        reg = builtin.default_registry()
        action_ids = set(reg._actions.keys())

        expected_actions = {
            "email.reply_draft",
            "executive.plan_interviews",
            "executive.approve_batch",
            "orchestrator.approve_gate",
            "orchestrator.decline_gate",
            "item.dismiss",
            "item.snooze",
            "applicant.reach_out",
            "applicant.invite_interview",
            "applicant.email_manager",
            "applicant.review",
            "applicant.decline",
            "applicant.hold",
            "county.refresh",
            "county.opening_change",
            "openings.event",
            "mail.organize_inbox",
            "mail.organize_apply",
            "brain_dump.clarify",
            "brain_dump.stage_candidate",
            "knowledge_gap.answer",
            "candidate.accept",
            "candidate.reject",
            "project.resume",
        }
        self.assertEqual(action_ids, expected_actions)

    def test_new_actions_are_item_options_and_tools(self):
        reg = builtin.default_registry()
        listed = {a["id"] for a in reg.actions()}
        self.assertTrue({"applicant.decline", "applicant.hold", "openings.event"} <= listed)
        tools = {a["id"]: a for a in reg.actions()}
        for action_id in ("applicant.reach_out", "applicant.invite_interview", "applicant.email_manager",
                          "applicant.review", "applicant.decline", "applicant.hold", "openings.event"):
            self.assertIn(action_id, tools)
            self.assertNotIn("handler", tools[action_id])
            self.assertIn("params_schema", tools[action_id])
            self.assertTrue(tools[action_id]["label"])
        for action_id in ("applicant.decline", "applicant.hold", "openings.event"):
            self.assertTrue(reg._actions[action_id]["consequential"])
        for action_id in ("applicant.reach_out", "applicant.invite_interview", "applicant.email_manager"):
            self.assertFalse(reg._actions[action_id]["consequential"])

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
        self.assertEqual(sorted(reg1._providers), sorted(reg2._providers))
        self.assertEqual([a["id"] for a in reg1.actions()], [a["id"] for a in reg2.actions()])
        self.assertIn("counties", reg2._providers)
        self.assertIn("openings.event", reg2._actions)

        # Counts should not increase
        self.assertEqual(provider_count_1, provider_count_2)
        self.assertEqual(action_count_1, action_count_2)

    def test_consequential_flags(self):
        """Test that consequential flags are set correctly."""
        reg = builtin.default_registry()

        # These should be consequential (require confirmation)
        consequential_actions = {
            "orchestrator.approve_gate",
            "orchestrator.decline_gate",
            "mail.organize_apply",
            "applicant.decline",
            "county.opening_change",
            "knowledge_gap.answer",
            "candidate.accept",
            "candidate.reject",
        }
        # The old direct senders are gone: every email goes through compose.
        self.assertNotIn("email.send", reg._actions)
        self.assertNotIn("executive.reach_out", reg._actions)

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
            "mail.organize_inbox",
            "project.resume",
        }

        for action_id in non_consequential_actions:
            action = reg._actions[action_id]
            self.assertFalse(
                action["consequential"],
                f"Action {action_id} should not be consequential but is",
            )


if __name__ == "__main__":
    unittest.main()
