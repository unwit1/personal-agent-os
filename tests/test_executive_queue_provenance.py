"""Tests for privacy-safe executive queue provenance."""

import json
import tempfile
import unittest

from agent_os.executive import event_bus, routing, window_queue


class TestQueueProvenance(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.bus = event_bus.EventBus(self.temp_dir.name)
        self.item = {
            "id": "w1", "title": "Secret Applicant Name", "kind": "k",
            "tab": "work", "why": "private why", "score": 2,
        }
        self.qi = window_queue.queue_item_from_window_item(self.item, "prov")

    def tearDown(self):
        self.temp_dir.cleanup()

    def publish_history(self):
        window_queue.publish_window_item(self.bus, self.item, "prov", self.qi)
        window_queue.publish_deferral(self.bus, self.qi["entity_id"], "w1", deferred_at="2026-01-01T00:00:00+00:00", until="2026-01-02T00:00:00+00:00")
        window_queue.publish_status_change(self.bus, self.qi["entity_id"], "w1", "cancelled", changed_at="2026-01-03T00:00:00+00:00")

    def test_history_is_ordered_private_and_lookup_accepts_both_ids(self):
        self.publish_history()
        other = window_queue.queue_item_from_window_item({"id": "other", "kind": "k", "tab": "work"}, "prov")
        window_queue.publish_window_item(self.bus, {"id": "other", "kind": "k", "tab": "work"}, "prov", other)
        result = window_queue.item_provenance([None, self.qi, other], self.bus, "w1")
        self.assertEqual(result["item_id"], "w1")
        self.assertEqual(result["history"], window_queue.entity_history(self.bus, self.qi["entity_id"]))
        history = result["history"]
        self.assertEqual([event["type"] for event in history], ["task.created", "task.deferred", "task.cancelled"])
        self.assertEqual(result["repeated_deferrals"], 1)
        self.assertEqual(history[1]["until"], "2026-01-02T00:00:00+00:00")
        self.assertEqual(history[2]["status"], "cancelled")
        self.assertTrue(all(event["route"] is None for event in history))
        self.assertEqual(window_queue.item_provenance([self.qi], self.bus, self.qi["id"])["queue_item_id"], self.qi["id"])
        serialized = json.dumps(result)
        self.assertNotIn("Secret Applicant Name", serialized)
        self.assertNotIn("private why", serialized)
        self.assertIsNone(window_queue.item_provenance([self.qi], self.bus, "missing"))

    def test_none_bus_and_routed_history(self):
        self.publish_history()
        result = window_queue.item_provenance([self.qi], None, "w1")
        self.assertEqual(result["history"], [])
        self.assertEqual(result["repeated_deferrals"], 0)
        self.assertEqual(window_queue.entity_history(None, self.qi["entity_id"]), [])
        routing.dispatch_pending(self.bus, consumer="router")
        routed = window_queue.entity_history(self.bus, self.qi["entity_id"])
        self.assertIsInstance(routed[0]["route"], dict)


if __name__ == "__main__":
    unittest.main()
