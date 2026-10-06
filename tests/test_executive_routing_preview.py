"""Tests for read-only previews of pending EventBus routes."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import routing
from agent_os.executive.event_bus import EventBus
from agent_os.executive.route_log import RouteLog


class ExecutiveRoutingPreviewTests(unittest.TestCase):
    def test_preview_is_read_only_repeatable_and_matches_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = EventBus(tmpdir)
            consumer = "preview-test"
            types = ["task.created", "skill.used", "skill.failed"]
            events = [
                bus.publish(event_type, "test", event_type, {"secret": "payload"})[0]
                for event_type in types
            ]
            log = RouteLog(tmpdir)

            first = routing.preview_pending(bus, consumer=consumer, log=log)
            second = routing.preview_pending(bus, consumer=consumer, log=log)
            self.assertEqual(first, second)
            self.assertEqual([r["event_id"] for r in first], [e["id"] for e in events])
            self.assertEqual([r["disposition"] for r in first], ["process", "ignore", "delegate"])
            self.assertEqual(len(bus.pending(consumer)), len(events))
            self.assertFalse(log.path.exists())
            self.assertTrue(all("payload" not in result for result in first))
            self.assertTrue(all("payload" not in result.values() for result in first))

            dispatched = routing.dispatch_pending(bus, consumer=consumer, log=log)
            self.assertEqual(
                [(r["event_id"], r["disposition"]) for r in first],
                [(r["event_id"], r["disposition"]) for r in dispatched],
            )
            self.assertEqual(routing.preview_pending(bus, consumer=consumer, log=log), [])

    def test_preview_applies_per_call_rules_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = EventBus(tmpdir)
            event = bus.publish("task.created", "test", "task.created", {"secret": "payload"})[0]
            results = routing.preview_pending(
                bus, consumer="override-test", rules={"task.created": "ignore"},
                log=RouteLog(tmpdir),
            )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["event_id"], event["id"])
        self.assertEqual(results[0]["disposition"], "ignore")


if __name__ == "__main__":
    unittest.main()
