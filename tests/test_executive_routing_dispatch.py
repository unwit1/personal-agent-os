"""Tests for routing events read from the EventBus consumer queue."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import contracts, routing
from agent_os.executive.event_bus import EventBus
from agent_os.executive.route_log import RouteLog


class ExecutiveRoutingDispatchTests(unittest.TestCase):
    def test_pending_events_can_be_routed_without_exposing_payload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bus = EventBus(directory)
            created = [
                bus.publish(event_type, "test", event_type, {"private": event_type})[0]
                for event_type in sorted(contracts.EVENT_TYPES)
            ]

            results = [routing.route_event(event) for event in bus.pending("executive")]

        self.assertEqual([result["event_id"] for result in results], [event["id"] for event in created])
        self.assertEqual([result["event_type"] for result in results], [event["type"] for event in created])
        self.assertTrue(all(result["disposition"] in routing.DISPOSITIONS for result in results))
        self.assertTrue(all("payload" not in result for result in results))
        self.assertTrue(all("private" not in result.values() for result in results))

    def test_dispatch_is_idempotent_and_routes_new_events_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bus = EventBus(directory)
            consumer = "dispatch-test"
            types = ["task.created", "skill.used", "skill.failed", "task.deferred", "decision.required"]
            events = [bus.publish(t, "test", t, {"secret": "payload"})[0] for t in types]
            log = RouteLog(directory)

            records = routing.dispatch_pending(bus, consumer=consumer, log=log, routed_at="fixed")
            self.assertEqual([r["event_id"] for r in records], [e["id"] for e in events])
            self.assertEqual([r["disposition"] for r in records], ["process", "ignore", "delegate", "defer", "surface"])
            self.assertTrue(log.path.exists())
            before = log.path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(before), len(events))
            self.assertEqual(routing.dispatch_pending(bus, consumer=consumer, log=log), [])
            self.assertEqual(log.path.read_text(encoding="utf-8").splitlines(), before)

            added = bus.publish("task.completed", "test", "later", {"secret": "payload"})[0]
            later = routing.dispatch_pending(bus, consumer=consumer, log=log)
            self.assertEqual([r["event_id"] for r in later], [added["id"]])

    def test_route_reason_returns_record_and_unknown_is_none(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bus = EventBus(directory)
            event = bus.publish("task.created", "test", "reason", {"private": "payload"})[0]
            [record] = routing.dispatch_pending(bus, consumer="reason-test")
            self.assertEqual(routing.route_reason(event["id"], bus=bus), record)
            self.assertEqual(record["reason"], "default route for task.created")
            self.assertEqual(record["rule"], "default")
            self.assertEqual(record["disposition"], "process")
            self.assertIsNone(routing.route_reason("unknown", bus=bus))

    def test_recovers_existing_route_and_acknowledges_without_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bus = EventBus(directory)
            event = bus.publish("task.created", "test", "recover", {"private": "payload"})[0]
            log = RouteLog(directory)
            saved, _ = log.record(routing.route_event(event), routed_at="original")
            lines_before = log.path.read_text(encoding="utf-8").splitlines()
            records = routing.dispatch_pending(bus, consumer="recovery-test", log=log)
            self.assertEqual(records, [saved])
            self.assertEqual(log.path.read_text(encoding="utf-8").splitlines(), lines_before)
            self.assertEqual(bus.pending("recovery-test"), [])

    def test_overrides_and_local_only_routes_are_persisted_without_payload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bus = EventBus(directory)
            ordinary = bus.publish("task.created", "test", "override", {"private": "payload"})[0]
            sensitive = bus.publish(
                "task.created", "test", "sensitive", {"private": "payload"}, sensitivity="sensitive"
            )[0]
            records = routing.dispatch_pending(
                bus, consumer="override-test", rules={"task.created": "delegate"},
                log=RouteLog(directory),
            )
            self.assertEqual([r["event_id"] for r in records], [ordinary["id"], sensitive["id"]])
            self.assertEqual((records[0]["disposition"], records[0]["rule"]), ("delegate", "override"))
            self.assertEqual((records[1]["disposition"], records[1]["rule"]), ("surface", "local_only"))
            stored = RouteLog(directory).path.read_text(encoding="utf-8")
            self.assertNotIn("payload", stored)


if __name__ == "__main__":
    unittest.main()
