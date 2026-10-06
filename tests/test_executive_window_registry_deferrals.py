"""Repeated deferrals are tracked without changing the window before threshold."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_os.executive import event_bus, window_queue
from agent_os.executive.window.registry import Registry


class RegistryDeferralTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.bus = event_bus.EventBus(self.tmp.name)
        self.reg = Registry()
        self.reg.register_provider("work", lambda: [
            {"id": "x1", "tab": "work", "kind": "task", "title": "Do task", "why": "waiting on review"}
        ])
        self.reg.attach_event_bus(self.bus)

    def defer(self, number: int) -> None:
        self.reg.outstanding()
        entity_id = self.reg.queue()["queue_items"][0]["entity_id"]
        window_queue.publish_deferral(
            self.bus, entity_id, "x1", deferred_at=f"2026-01-01T00:00:0{number}+00:00"
        )

    def test_no_deferrals_leave_outstanding_unchanged(self) -> None:
        item = self.reg.outstanding()["items"][0]
        self.assertNotIn("deferrals", item)
        self.assertEqual(item["why"], "waiting on review")

    def test_record_deferral_returns_event_and_unknown_id_returns_none(self) -> None:
        self.reg.outstanding()
        event = self.reg.record_deferral("x1")
        self.assertIsInstance(event, dict)
        self.assertEqual(event["type"], "task.deferred")
        self.assertIsNone(self.reg.record_deferral("missing"))

    def test_two_deferrals_are_in_queue_without_window_flag(self) -> None:
        self.defer(1)
        self.defer(2)
        queue_item = self.reg.queue()["queue_items"][0]
        self.assertEqual(queue_item["repeated_deferrals"], 2)
        item = self.reg.outstanding()["items"][0]
        self.assertNotIn("deferrals", item)
        self.assertEqual(item["why"], "waiting on review")

    def test_three_deferrals_are_flagged_in_outstanding(self) -> None:
        self.defer(1)
        self.defer(2)
        self.defer(3)
        item = self.reg.outstanding()["items"][0]
        self.assertEqual(item["deferrals"], 3)
        self.assertTrue(item["why"].startswith("Deferred 3 times; waiting on review"))

    def test_same_item_id_from_two_providers_defers_both_entities(self) -> None:
        reg = Registry()
        reg.register_provider("a", lambda: [{"id": "dup", "kind": "task", "title": "A"}])
        reg.register_provider("b", lambda: [{"id": "dup", "kind": "task", "title": "B"}])
        reg.attach_event_bus(self.bus)
        entity_ids = {qi["entity_id"] for qi in reg.queue()["queue_items"]}
        self.assertEqual(len(entity_ids), 2)
        reg.record_deferral("dup")
        reg.record_status("dup", "cancelled")
        self.assertEqual(window_queue.deferral_counts(self.bus), {entity_id: 1 for entity_id in entity_ids})
        self.assertEqual(window_queue.queue_statuses(self.bus), {entity_id: "cancelled" for entity_id in entity_ids})

    def test_record_deferral_without_bus_returns_none(self) -> None:
        reg = Registry()
        reg.register_provider("work", lambda: [{"id": "x1", "kind": "task", "title": "Do task"}])
        reg.outstanding()
        self.assertIsNone(reg.record_deferral("x1"))


if __name__ == "__main__":
    unittest.main()
