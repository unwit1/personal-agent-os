"""Queue status events are reflected in the Executive Queue."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_os.executive import event_bus
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


if __name__ == "__main__":
    unittest.main()
