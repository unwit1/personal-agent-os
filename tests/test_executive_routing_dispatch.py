"""Tests for routing events read from the EventBus consumer queue."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import contracts, routing
from agent_os.executive.event_bus import EventBus


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


if __name__ == "__main__":
    unittest.main()
