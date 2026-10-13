from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import event_bus, window_queue


class TestExecutiveLifecycleSensitivity(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.bus = event_bus.EventBus(self.temp_dir.name)

    def test_sensitive_and_secret_lifecycle_events_are_local_only(self) -> None:
        for sensitivity in ("sensitive", "secret"):
            with self.subTest(sensitivity=sensitivity):
                deferred, _ = window_queue.publish_deferral(
                    self.bus, f"entity-{sensitivity}", "item-1", deferred_at=f"{sensitivity}-deferred",
                    sensitivity=sensitivity,
                )
                completed, _ = window_queue.publish_status_change(
                    self.bus, f"entity-{sensitivity}", "item-1", "completed",
                    changed_at=f"{sensitivity}-completed", sensitivity=sensitivity,
                )
                cancelled, _ = window_queue.publish_status_change(
                    self.bus, f"entity-{sensitivity}", "item-1", "cancelled",
                    changed_at=f"{sensitivity}-cancelled", sensitivity=sensitivity,
                )

                for event in (deferred, completed, cancelled):
                    stored = self.bus.get(event["id"])
                    self.assertEqual(stored["sensitivity"], sensitivity)
                    self.assertIs(stored["local_only"], True)
                    self.assertNotIn("title", stored["payload"])
                    self.assertNotIn("reason", stored["payload"])

    def test_omitted_sensitivity_remains_personal(self) -> None:
        deferred, _ = window_queue.publish_deferral(
            self.bus, "entity-default", "item-1", deferred_at="default-deferred"
        )
        completed, _ = window_queue.publish_status_change(
            self.bus, "entity-default", "item-1", "completed", changed_at="default-completed"
        )
        self.assertEqual(deferred["sensitivity"], "personal")
        self.assertEqual(completed["sensitivity"], "personal")
        self.assertNotIn("local_only", deferred)
        self.assertNotIn("local_only", completed)

    def test_invalid_sensitivity_is_rejected_before_append(self) -> None:
        with self.assertRaises(ValueError):
            window_queue.publish_deferral(
                self.bus, "entity-invalid", "item-1", deferred_at="invalid-deferred",
                sensitivity="invalid",
            )
        with self.assertRaises(ValueError):
            window_queue.publish_status_change(
                self.bus, "entity-invalid", "item-1", "cancelled",
                changed_at="invalid-cancelled", sensitivity="invalid",
            )
        self.assertEqual(self.bus.events(), [])


if __name__ == "__main__":
    unittest.main()
