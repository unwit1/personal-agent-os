"""Queue status events are reflected in the Executive Queue."""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_os.executive import event_bus
from agent_os.executive import window_queue
from agent_os.executive.next_action import next_item
from agent_os.executive.window.registry import Registry


class FakePending:
    def create(self, action_id, item, params, result):
        return "t1"

    def take(self, token):
        return {"action_id": "finish", "item": self.item, "params": {}}

    def audit(self, event):
        self.events.append(event)


class RegistryStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.bus = event_bus.EventBus(self.tmp.name)
        self.reg = Registry()
        self.reg.register_provider("work", lambda: [
            {"id": "x1", "tab": "work", "kind": "task", "title": "Do task"}
        ])
        self.reg.attach_event_bus(self.bus)

    def test_record_status_publishes_completed_and_cancelled(self) -> None:
        self.reg.outstanding()
        completed = self.reg.record_status("x1", "completed")
        cancelled = self.reg.record_status("x1", "cancelled")
        self.assertEqual(completed["type"], "task.completed")
        self.assertEqual(cancelled["type"], "task.cancelled")

    def test_record_status_unknown_or_without_bus_returns_none(self) -> None:
        self.reg.outstanding()
        self.assertIsNone(self.reg.record_status("missing", "completed"))
        reg = Registry()
        reg.register_provider("work", lambda: [{"id": "x1", "kind": "task", "title": "Do task"}])
        reg.outstanding()
        self.assertIsNone(reg.record_status("x1", "completed"))

    def test_queue_status_and_default(self) -> None:
        self.reg.outstanding()
        self.assertEqual(self.reg.queue()["queue_items"][0]["status"], "queued")
        self.reg.record_status("x1", "cancelled")
        self.assertEqual(self.reg.queue()["queue_items"][0]["status"], "cancelled")

    def test_outstanding_keys_do_not_change(self) -> None:
        before = self.reg.outstanding()["items"][0]
        self.reg.record_status("x1", "cancelled")
        after = self.reg.outstanding()["items"][0]
        self.assertEqual(set(before), set(after))

    def test_confirm_marks_queue_item_completed(self) -> None:
        pending = FakePending()
        pending.events = []
        self.reg.register_action(
            "finish", "Finish", "*", lambda item, params, confirm: {"ok": True},
            consequential=True,
        )
        item = self.reg.outstanding()["items"][0]
        pending.item = item
        invoked = self.reg.invoke("finish", item, {}, pending)
        result = self.reg.confirm(invoked["confirm_token"], pending)
        self.assertEqual(result, {"ok": True})
        self.assertEqual(self.reg.queue()["queue_items"][0]["status"], "completed")

    def test_next_action_skips_cancelled_and_confirmed_completed_items(self) -> None:
        reg = Registry()
        reg.register_provider("work", lambda: [
            {"id": "high", "tab": "work", "kind": "task", "title": "High", "score": 20},
            {"id": "low", "tab": "work", "kind": "task", "title": "Low", "score": 5},
        ])
        reg.attach_event_bus(self.bus)
        items = reg.queue()["queue_items"]
        by_window_id = {qi["window_item"]["id"]: qi for qi in items}

        cancelled, created = window_queue.publish_status_change(
            self.bus, by_window_id["high"]["entity_id"], "high", "cancelled",
            changed_at="2026-10-13T14:00:00+00:00",
        )
        self.assertTrue(created)
        result = next_item(reg.queue()["queue_items"])
        self.assertEqual(result["next"]["window_item"]["id"], "low")
        self.assertEqual(result["considered"], 1)
        self.assertEqual(reg.queue()["queue_items"][0]["status"], "cancelled")
        self.assertEqual(self.bus.get(cancelled["id"]), cancelled)

        pending = FakePending()
        pending.events = []
        reg.register_action("finish", "Finish", "*", lambda item, params, confirm: {"ok": True}, consequential=True)
        high_item = next(item for item in reg.outstanding()["items"] if item["id"] == "high")
        pending.item = high_item
        invoked = reg.invoke("finish", high_item, {}, pending)
        self.assertEqual(reg.confirm(invoked["confirm_token"], pending), {"ok": True})
        result = next_item(reg.queue()["queue_items"])
        self.assertEqual(result["next"]["window_item"]["id"], "low")
        self.assertEqual(result["considered"], 1)
        self.assertEqual(reg.queue()["queue_items"][0]["status"], "completed")
        self.assertEqual(
            [event["type"] for event in self.bus.events(subject=by_window_id["high"]["entity_id"])],
            ["task.created", "task.cancelled", "task.completed"],
        )

    def test_deferral_expiry_controls_next_action_selection(self) -> None:
        reg = Registry()
        reg.register_provider("work", lambda: [
            {"id": "high", "tab": "work", "kind": "task", "title": "High", "score": 20},
            {"id": "low", "tab": "work", "kind": "task", "title": "Low", "score": 5},
        ])
        reg.attach_event_bus(self.bus)
        items = reg.queue()["queue_items"]
        high = next(qi for qi in items if qi["window_item"]["id"] == "high")
        now = datetime(2026, 10, 13, 15, 0, tzinfo=timezone.utc)
        future, _ = window_queue.publish_deferral(
            self.bus, high["entity_id"], "high", deferred_at="2026-10-13T14:00:00+00:00",
            until="2026-10-13T16:00:00+00:00",
        )
        real_queue_statuses = window_queue.queue_statuses
        with patch.object(window_queue, "queue_statuses", side_effect=lambda bus: real_queue_statuses(bus, now=now)):
            result = next_item(reg.queue()["queue_items"])
        self.assertEqual(result["next"]["window_item"]["id"], "low")
        self.assertEqual(reg.queue()["queue_items"][0]["status"], "deferred")
        self.assertEqual(self.bus.get(future["id"]), future)

        expired, _ = window_queue.publish_deferral(
            self.bus, high["entity_id"], "high", deferred_at="2026-10-13T14:30:00+00:00",
            until="2026-10-13T14:45:00+00:00",
        )
        with patch.object(window_queue, "queue_statuses", side_effect=lambda bus: real_queue_statuses(bus, now=now)):
            queue_items = reg.queue()["queue_items"]
            result = next_item(queue_items)
        self.assertEqual(result["next"]["window_item"]["id"], "high")
        self.assertEqual(result["considered"], 2)
        self.assertEqual(next(qi for qi in queue_items if qi["window_item"]["id"] == "high")["status"], "queued")
        self.assertEqual(self.bus.get(expired["id"]), expired)


if __name__ == "__main__":
    unittest.main()
