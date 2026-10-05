"""Tests for independent EventBus consumer acknowledgements."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.event_bus import EventBus


class EventBusConsumerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.bus = EventBus(self.temp_dir.name)
        self.events = [
            self.bus.publish("task.created", "test", f"k{i}", {"i": i})[0]
            for i in range(3)
        ]

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_pending_initially_returns_all_events(self) -> None:
        self.assertEqual(self.bus.pending("worker"), self.events)

    def test_acknowledge_once_and_pending_preserves_order(self) -> None:
        event = self.events[1]
        self.assertTrue(self.bus.acknowledge("worker", event["id"], "2026-01-01T00:00:00+00:00"))
        self.assertFalse(self.bus.acknowledge("worker", event["id"]))
        self.assertEqual(self.bus.pending("worker"), [self.events[0], self.events[2]])
        self.assertEqual(self.bus.acknowledged("worker"), {event["id"]})

    def test_consumers_are_independent(self) -> None:
        self.bus.acknowledge("a", self.events[0]["id"])
        self.assertEqual(self.bus.pending("a"), self.events[1:])
        self.assertEqual(self.bus.pending("b"), self.events)

    def test_pending_filters_event_type(self) -> None:
        self.bus.publish("task.completed", "test", "done", {})
        result = self.bus.pending("worker", event_type="task.completed")
        self.assertEqual([event["type"] for event in result], ["task.completed"])

    def test_unknown_event_id_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.bus.acknowledge("worker", "missing-event")

    def test_invalid_consumer_names_raise(self) -> None:
        for name in ("", "Bad Name", "../x"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.bus.pending(name)

    def test_missing_acknowledgement_file_is_empty(self) -> None:
        self.assertEqual(self.bus.acknowledged("worker"), set())


if __name__ == "__main__":
    unittest.main()
