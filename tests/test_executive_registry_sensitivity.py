"""Lifecycle Event Bus events retain each converted queue entity's sensitivity."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_os.executive import event_bus
from agent_os.executive.window.registry import Registry


class RegistrySensitivityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.bus = event_bus.EventBus(self.tmp.name)

    def test_sensitive_lifecycle_events_are_local_only(self) -> None:
        for sensitivity in ("sensitive", "secret"):
            with self.subTest(sensitivity=sensitivity):
                reg = Registry()
                reg.register_provider("work", lambda s=sensitivity: [
                    {"id": s, "tab": "work", "kind": "task", "title": "private", "sensitivity": s}
                ])
                reg.attach_event_bus(self.bus)
                reg.outstanding()
                reg.record_deferral(sensitivity)
                reg.record_status(sensitivity, "completed")
                reg.record_status(sensitivity, "cancelled")
                events = self.bus.events()
                selected = [
                    e for e in events
                    if e.get("payload", {}).get("item_id") == sensitivity
                    and e["type"] != "task.created"
                ]
                self.assertEqual([e["type"] for e in selected], [
                    "task.deferred", "task.completed", "task.cancelled"
                ])
                self.assertTrue(all(e["local_only"] is True for e in selected))
                self.assertTrue(all(e["sensitivity"] == sensitivity for e in selected))

    def test_shared_window_id_keeps_each_provider_sensitivity(self) -> None:
        reg = Registry()
        reg.register_provider("sensitive-provider", lambda: [
            {"id": "shared", "kind": "task", "title": "one", "sensitivity": "sensitive"}
        ])
        reg.register_provider("secret-provider", lambda: [
            {"id": "shared", "kind": "task", "title": "two", "sensitivity": "secret"}
        ])
        reg.attach_event_bus(self.bus)
        reg.outstanding()
        reg.record_deferral("shared")
        events = [e for e in self.bus.events(event_type="task.deferred")]
        self.assertEqual({e["sensitivity"] for e in events}, {"sensitive", "secret"})
        self.assertTrue(all(e["local_only"] is True for e in events))
        self.assertEqual(len({e["subject"] for e in events}), 2)

    def test_personal_and_filtered_items_are_collected_for_lifecycle(self) -> None:
        reg = Registry()
        reg.register_provider("personal", lambda: [
            {"id": "personal-item", "tab": "personal", "kind": "task", "title": "ordinary"}
        ])
        reg.register_provider("hidden", lambda: [
            {"id": "hidden-item", "tab": "personal", "kind": "task", "title": "private", "sensitivity": "secret"}
        ])
        reg.attach_event_bus(self.bus)
        self.assertEqual(reg.outstanding(tab="work")["items"], [])
        reg.record_status("personal-item", "completed")
        reg.record_deferral("hidden-item")
        events = self.bus.events()
        personal = next(e for e in events if e["type"] == "task.completed")
        hidden = next(e for e in events if e["type"] == "task.deferred")
        self.assertEqual(personal["sensitivity"], "personal")
        self.assertNotIn("local_only", personal)
        self.assertEqual(hidden["sensitivity"], "secret")
        self.assertIs(hidden["local_only"], True)


if __name__ == "__main__":
    unittest.main()
