import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

import agent_os.executive.window.actions_items as actions_items
from agent_os.executive.window.confirm import ItemState, ENV_HOME
from agent_os.executive.window.registry import Registry


def gate_item(gate_id="g1", run_id="run1"):
    return {
        "id": f"gate:{run_id}:{gate_id}",
        "tab": "work",
        "kind": "orchestrator_gate",
        "run_id": run_id,
        "gate_id": gate_id,
        "gate_summary": "Test gate",
    }


def regular_item(item_id="item1", tab="work"):
    return {
        "id": item_id,
        "tab": tab,
        "kind": "note",
        "title": item_id,
        "why": "test",
        "source": "test",
    }


class ActionsItemsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        # Set env var so actions can find the test home
        self._env_patcher = mock.patch.dict(os.environ, {ENV_HOME: self.tmp.name})
        self._env_patcher.start()
        self.addCleanup(self._env_patcher.stop)

        self.registry = Registry()
        actions_items.register(self.registry)

    def test_approve_gate_preview_no_decide(self):
        """Gate preview with confirm=False must not call DECIDE."""
        def fake_decide(run_id, gate_id, approve, note=None):
            raise AssertionError("DECIDE should not be called in preview")

        with mock.patch.object(actions_items, 'DECIDE', fake_decide):
            action = self.registry._get("orchestrator.approve_gate")
            preview = action["handler"](gate_item(), {}, confirm=False)
            self.assertEqual(preview["approve"], True)
            self.assertEqual(preview["run_id"], "run1")
            self.assertEqual(preview["gate_id"], "g1")

    def test_approve_gate_confirm_calls_decide(self):
        """Gate with confirm=True must call DECIDE with approve=True."""
        decide_calls = []
        def fake_decide(run_id, gate_id, approve, note=None):
            decide_calls.append((run_id, gate_id, approve, note))
            return {"decided": True}

        with mock.patch.object(actions_items, 'DECIDE', fake_decide):
            action = self.registry._get("orchestrator.approve_gate")
            result = action["handler"](gate_item(), {"note": "approved"}, confirm=True)
            self.assertEqual(len(decide_calls), 1)
            self.assertEqual(decide_calls[0], ("run1", "g1", True, "approved"))
            self.assertEqual(result, {"decided": True})

    def test_decline_gate_preview_no_decide(self):
        """Gate preview with confirm=False must not call DECIDE."""
        def fake_decide(run_id, gate_id, approve, note=None):
            raise AssertionError("DECIDE should not be called in preview")

        with mock.patch.object(actions_items, 'DECIDE', fake_decide):
            action = self.registry._get("orchestrator.decline_gate")
            preview = action["handler"](gate_item(), {}, confirm=False)
            self.assertEqual(preview["approve"], False)
            self.assertEqual(preview["run_id"], "run1")
            self.assertEqual(preview["gate_id"], "g1")

    def test_decline_gate_confirm_calls_decide(self):
        """Gate with confirm=True must call DECIDE with approve=False."""
        decide_calls = []
        def fake_decide(run_id, gate_id, approve, note=None):
            decide_calls.append((run_id, gate_id, approve, note))
            return {"decided": False}

        with mock.patch.object(actions_items, 'DECIDE', fake_decide):
            action = self.registry._get("orchestrator.decline_gate")
            result = action["handler"](gate_item(), {"note": "rejected"}, confirm=True)
            self.assertEqual(len(decide_calls), 1)
            self.assertEqual(decide_calls[0], ("run1", "g1", False, "rejected"))
            self.assertEqual(result, {"decided": False})

    def test_dismiss_item(self):
        """Dismiss action hides item from registry."""
        state = ItemState(self.tmp.name)
        item = regular_item("work:item1")
        action = self.registry._get("item.dismiss")

        # Item is visible before dismiss
        self.assertFalse(state.is_hidden(item["id"]))

        # Call dismiss with confirm=True
        result = action["handler"](item, {}, confirm=True)
        self.assertEqual(result, {"dismissed": True})

        # Item is hidden after dismiss
        self.assertTrue(state.is_hidden(item["id"]))

    def test_dismiss_hides_item_in_registry(self):
        """Dismiss action hides item from Registry.outstanding()."""
        item = regular_item("work:item2")
        action = self.registry._get("item.dismiss")

        # Define a provider that returns the item
        def test_provider():
            return [item]
        self.registry.register_provider("test", test_provider)

        # Item is visible before dismiss
        state = ItemState(self.tmp.name)
        result = self.registry.outstanding(state=state)
        self.assertEqual(len(result["items"]), 1)

        # Call dismiss
        action["handler"](item, {}, confirm=False)

        # Item is hidden after dismiss
        state = ItemState(self.tmp.name)
        result = self.registry.outstanding(state=state)
        self.assertEqual(len(result["items"]), 0)

    def test_snooze_item_with_until(self):
        """Snooze action with until parameter hides item until that time."""
        state = ItemState(self.tmp.name)
        item = regular_item("personal:email1")
        action = self.registry._get("item.snooze")

        now = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)
        until = (now + timedelta(hours=2)).isoformat()

        # Call snooze with confirm=True
        result = action["handler"](item, {"until": until}, confirm=True)
        self.assertEqual(result["snoozed_until"], until)

        # Item should be hidden now but visible after the time
        self.assertTrue(state.is_hidden(item["id"], now=now))
        self.assertFalse(state.is_hidden(item["id"], now=now + timedelta(hours=3)))

    def test_snooze_item_with_hours(self):
        """Snooze action with hours parameter hides item for that many hours."""
        item = regular_item("work:item3")
        action = self.registry._get("item.snooze")

        now = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)
        future = now + timedelta(hours=3)

        # Mock datetime.now to return our fixed time
        with mock.patch("agent_os.executive.window.actions_items.datetime") as mock_dt_class:
            mock_dt_class.now.return_value = now
            # Keep datetime constructor working for creating new datetimes
            mock_dt_class.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            # Keep timezone and timedelta available
            mock_dt_class.timezone = timezone
            mock_dt_class.timedelta = timedelta

            result = action["handler"](item, {"hours": 3}, confirm=True)

        # Read state with fresh instance
        state = ItemState(self.tmp.name)
        # Item should be hidden until 3 hours later
        self.assertTrue(state.is_hidden(item["id"], now=now + timedelta(hours=1)))
        self.assertFalse(state.is_hidden(item["id"], now=now + timedelta(hours=4)))

    def test_snooze_item_default_hours(self):
        """Snooze action defaults to 24 hours when no params given."""
        item = regular_item("work:item4")
        action = self.registry._get("item.snooze")

        now = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)

        with mock.patch("agent_os.executive.window.actions_items.datetime") as mock_dt_class:
            mock_dt_class.now.return_value = now
            mock_dt_class.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            mock_dt_class.timezone = timezone
            mock_dt_class.timedelta = timedelta
            result = action["handler"](item, {}, confirm=True)

        # Read state with fresh instance
        state = ItemState(self.tmp.name)
        # Item should be hidden for 24 hours
        self.assertTrue(state.is_hidden(item["id"], now=now + timedelta(hours=1)))
        self.assertFalse(state.is_hidden(item["id"], now=now + timedelta(hours=25)))


    def test_snooze_hides_item_until_time(self):
        """Snoozed item is hidden until the specified time."""
        item = regular_item("work:item6")
        action = self.registry._get("item.snooze")

        now = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)
        until = (now + timedelta(hours=2)).isoformat()

        # Call snooze
        action["handler"](item, {"until": until}, confirm=False)

        # Verify state tracks the snooze
        state = ItemState(self.tmp.name)
        self.assertTrue(state.is_hidden(item["id"], now=now + timedelta(hours=1)))
        self.assertFalse(state.is_hidden(item["id"], now=now + timedelta(hours=3)))

    def test_actions_are_registered(self):
        """All expected actions must be registered."""
        actions = {a["id"] for a in self.registry.actions()}
        self.assertIn("orchestrator.approve_gate", actions)
        self.assertIn("orchestrator.decline_gate", actions)
        self.assertIn("item.dismiss", actions)
        self.assertIn("item.snooze", actions)

    def test_gate_actions_consequential(self):
        """Gate actions must be marked consequential."""
        actions_by_id = {a["id"]: a for a in self.registry.actions()}
        self.assertTrue(actions_by_id["orchestrator.approve_gate"]["consequential"])
        self.assertTrue(actions_by_id["orchestrator.decline_gate"]["consequential"])

    def test_item_actions_not_consequential(self):
        """Item actions must not be consequential."""
        actions_by_id = {a["id"]: a for a in self.registry.actions()}
        self.assertFalse(actions_by_id["item.dismiss"]["consequential"])
        self.assertFalse(actions_by_id["item.snooze"]["consequential"])

    def test_gate_actions_apply_to_orchestrator_gate(self):
        """Gate actions must apply to orchestrator_gate kind."""
        actions_by_id = {a["id"]: a for a in self.registry.actions()}
        self.assertIn("orchestrator_gate", actions_by_id["orchestrator.approve_gate"]["applies_to"])
        self.assertIn("orchestrator_gate", actions_by_id["orchestrator.decline_gate"]["applies_to"])

    def test_item_actions_apply_to_all(self):
        """Item actions must apply to all kinds."""
        actions_by_id = {a["id"]: a for a in self.registry.actions()}
        self.assertEqual(actions_by_id["item.dismiss"]["applies_to"], "*")
        self.assertEqual(actions_by_id["item.snooze"]["applies_to"], "*")

    def test_missing_run_id_raises_error(self):
        """Gate actions must raise error if run_id is missing."""
        action = self.registry._get("orchestrator.approve_gate")
        item = gate_item()
        del item["run_id"]
        with self.assertRaises(ValueError):
            action["handler"](item, {}, confirm=False)

    def test_missing_gate_id_raises_error(self):
        """Gate actions must raise error if gate_id is missing."""
        action = self.registry._get("orchestrator.approve_gate")
        item = gate_item()
        del item["gate_id"]
        with self.assertRaises(ValueError):
            action["handler"](item, {}, confirm=False)

    def test_missing_item_id_raises_error(self):
        """Item actions must raise error if id is missing."""
        action = self.registry._get("item.dismiss")
        item = regular_item()
        del item["id"]
        with self.assertRaises(ValueError):
            action["handler"](item, {}, confirm=False)


if __name__ == "__main__":
    unittest.main()
