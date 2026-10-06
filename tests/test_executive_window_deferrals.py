from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import event_bus, window_queue


class TestExecutiveWindowDeferrals(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.bus = event_bus.EventBus(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_publish_creates_identifier_only_deferral_event(self) -> None:
        entity_id = "ex-task-123"
        event, created = window_queue.publish_deferral(
            self.bus, entity_id, "item-1", deferred_at="2026-10-05T12:00:00+00:00", until="later"
        )

        self.assertTrue(created)
        self.assertEqual(event["type"], "task.deferred")
        self.assertEqual(event["subject"], entity_id)
        self.assertEqual(
            event["payload"],
            {
                "entity_id": entity_id,
                "item_id": "item-1",
                "deferred_at": "2026-10-05T12:00:00+00:00",
                "until": "later",
            },
        )
        self.assertNotIn("title", event["payload"])
        self.assertEqual(event["domain"], "executive-window")
        self.assertEqual(event["sensitivity"], "personal")

    def test_same_timestamp_deduplicates_but_new_timestamp_creates_event(self) -> None:
        args = (self.bus, "entity-1", "item-1")
        _, first = window_queue.publish_deferral(*args, deferred_at="t1")
        _, duplicate = window_queue.publish_deferral(*args, deferred_at="t1")
        _, second = window_queue.publish_deferral(*args, deferred_at="t2")

        self.assertTrue(first)
        self.assertFalse(duplicate)
        self.assertTrue(second)

    def test_counts_are_separate_by_entity(self) -> None:
        for timestamp in ("t1", "t2", "t3"):
            window_queue.publish_deferral(self.bus, "entity-1", "item-1", deferred_at=timestamp)
        window_queue.publish_deferral(self.bus, "entity-2", "item-2", deferred_at="t1")

        self.assertEqual(window_queue.deferral_counts(self.bus), {"entity-1": 3, "entity-2": 1})

    def test_empty_bus_and_none_have_no_counts(self) -> None:
        self.assertEqual(window_queue.deferral_counts(self.bus), {})
        self.assertEqual(window_queue.deferral_counts(None), {})


if __name__ == "__main__":
    unittest.main()
