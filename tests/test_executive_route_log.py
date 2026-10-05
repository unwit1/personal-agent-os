"""Tests for the executive routing decision log."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import event_bus, routing
from agent_os.executive.route_log import RouteLog


class ExecutiveRouteLogTests(unittest.TestCase):
    def test_records_routing_result_and_gets_it(self) -> None:
        event = event_bus._make_event("task.created", "test", "route-log", {"secret": "payload"})
        route = routing.route_event(event)
        with tempfile.TemporaryDirectory() as directory:
            log = RouteLog(directory)
            stored, created = log.record(route)
            self.assertTrue(created)
            self.assertEqual(log.get(event["id"]), stored)
            self.assertEqual(log.records(), [stored])

    def test_deduplicates_event_id(self) -> None:
        route = {"event_id": "e1", "event_type": "task.created", "disposition": "process", "rule": "default", "reason": "test"}
        with tempfile.TemporaryDirectory() as directory:
            log = RouteLog(directory)
            first, created = log.record(route)
            second, created_again = log.record({**route, "reason": "changed"})
            self.assertTrue(created)
            self.assertFalse(created_again)
            self.assertEqual(first, second)
            self.assertEqual(len(log.path.read_text(encoding="utf-8").splitlines()), 1)

    def test_drops_extra_fields(self) -> None:
        route = {"event_id": "e1", "event_type": "task.created", "disposition": "process", "rule": "default", "reason": "test", "payload": {"secret": "x"}}
        with tempfile.TemporaryDirectory() as directory:
            stored, _ = RouteLog(directory).record(route)
            self.assertEqual(set(stored), {"event_id", "event_type", "disposition", "rule", "reason", "routed_at"})
            self.assertNotIn("payload", stored)

    def test_rejects_bad_disposition_and_missing_key(self) -> None:
        route = {"event_id": "e1", "event_type": "task.created", "disposition": "invalid", "rule": "default", "reason": "test"}
        with tempfile.TemporaryDirectory() as directory:
            log = RouteLog(directory)
            with self.assertRaises(ValueError):
                log.record(route)
            del route["reason"]
            with self.assertRaises(ValueError):
                log.record(route)


if __name__ == "__main__":
    unittest.main()
