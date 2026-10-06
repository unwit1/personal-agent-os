from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import event_bus, window_queue


class TestExecutiveWindowQueueStatus(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.bus = event_bus.EventBus(self.temp_dir.name)

    def test_publish_completed_and_cancelled_status_events(self) -> None:
        for status, event_type in (
            ("completed", "task.completed"),
            ("cancelled", "task.cancelled"),
        ):
            with self.subTest(status=status):
                changed_at = "2026-10-05T12:00:00+00:00"
                event, created = window_queue.publish_status_change(
                    self.bus, "entity-1", "item-1", status, changed_at=changed_at
                )

                self.assertTrue(created)
                self.assertEqual(event["type"], event_type)
                self.assertEqual(event["source"], "window:status")
                self.assertEqual(event["dedup_key"], f"entity-1:{status}:{changed_at}")
                self.assertEqual(event["domain"], "executive-window")
                self.assertEqual(event["sensitivity"], "personal")
                self.assertEqual(event["subject"], "entity-1")
                self.assertEqual(
                    set(event["payload"]),
                    {"entity_id", "item_id", "status", "changed_at"},
                )
                self.assertEqual(
                    event["payload"],
                    {
                        "entity_id": "entity-1",
                        "item_id": "item-1",
                        "status": status,
                        "changed_at": changed_at,
                    },
                )

    def test_publish_rejects_invalid_status(self) -> None:
        with self.assertRaises(ValueError):
            window_queue.publish_status_change(self.bus, "entity-1", "item-1", "deferred")

    def test_latest_event_wins(self) -> None:
        window_queue.publish_deferral(
            self.bus,
            "entity-1",
            "item-1",
            deferred_at="2026-10-05T12:00:00+00:00",
        )
        window_queue.publish_status_change(
            self.bus,
            "entity-1",
            "item-1",
            "cancelled",
            changed_at="2026-10-05T12:01:00+00:00",
        )

        self.assertEqual(window_queue.queue_statuses(self.bus), {"entity-1": "cancelled"})

    def test_expired_and_future_deferrals(self) -> None:
        window_queue.publish_deferral(
            self.bus,
            "expired",
            "item-1",
            deferred_at="2026-10-05T12:00:00+00:00",
            until="2026-10-05T12:30:00+00:00",
        )
        window_queue.publish_deferral(
            self.bus,
            "future",
            "item-2",
            deferred_at="2026-10-05T12:00:00+00:00",
            until="2026-10-05T13:30:00+00:00",
        )

        self.assertEqual(
            window_queue.queue_statuses(
                self.bus, now=datetime(2026, 10, 5, 13, 0, tzinfo=timezone.utc)
            ),
            {"expired": "queued", "future": "deferred"},
        )

    def test_none_bus_has_no_statuses(self) -> None:
        self.assertEqual(window_queue.queue_statuses(None), {})


if __name__ == "__main__":
    unittest.main()
