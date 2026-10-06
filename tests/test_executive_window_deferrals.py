"""Tests for identifier-only Executive Window deferral events."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import event_bus, window_queue


class TestWindowDeferrals(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.bus = event_bus.EventBus(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_publishes_identifier_only_event(self) -> None:
        event, created = window_queue.publish_deferral(
            self.bus, "entity-1", "item-1", "2026-10-05T12:00:00+00:00", "later"
        )

        self.assertTrue(created)
        self.assertEqual(event["type"], "task.deferred")
        self.assertEqual(event["subject"], "entity-1")
        self.assertEqual(
            set(event["payload"]), {"entity_id", "item_id", "deferred_at", "until"}
        )
        self.assertNotIn("title", event["payload"])
        self.assertNotIn("Private title", event["payload"].values())

    def test_deduplicates_same_timestamp_but_records_distinct_deferrals(self) -> None:
        first, created_first = window_queue.publish_deferral(
            self.bus, "entity-1", "item-1", "2026-10-05T12:00:00+00:00"
        )
        repeated, created_repeated = window_queue.publish_deferral(
            self.bus, "entity-1", "item-1", "2026-10-05T12:00:00+00:00"
        )
        second, created_second = window_queue.publish_deferral(
            self.bus, "entity-1", "item-1", "2026-10-05T13:00:00+00:00"
        )

        self.assertTrue(created_first)
        self.assertFalse(created_repeated)
        self.assertEqual(first["id"], repeated["id"])
        self.assertTrue(created_second)
        self.assertNotEqual(first["id"], second["id"])

    def test_counts_are_separate_by_entity(self) -> None:
        for stamp in ("a", "b", "c"):
            window_queue.publish_deferral(self.bus, "entity-1", "item-1", stamp)
        window_queue.publish_deferral(self.bus, "entity-2", "item-2", "d")

        self.assertEqual(
            window_queue.deferral_counts(self.bus), {"entity-1": 3, "entity-2": 1}
        )

    def test_empty_bus_and_none_have_no_counts(self) -> None:
        self.assertEqual(window_queue.deferral_counts(self.bus), {})
        self.assertEqual(window_queue.deferral_counts(None), {})


if __name__ == "__main__":
    unittest.main()
