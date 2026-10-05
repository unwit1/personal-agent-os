"""Tests for executive event routing."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import contracts, event_bus, routing


class ExecutiveRoutingTests(unittest.TestCase):
    def make_event(self, event_type: str = "task.created", **kwargs: object) -> dict:
        return event_bus._make_event(event_type, "test", f"routing-{event_type}", {"private": "payload"}, **kwargs)

    def test_default_routes_cover_all_event_types_and_dispositions(self) -> None:
        self.assertEqual(set(routing.DEFAULT_ROUTES), contracts.EVENT_TYPES)
        self.assertTrue(set(routing.DEFAULT_ROUTES.values()) <= set(routing.DISPOSITIONS))

    def test_example_for_each_disposition(self) -> None:
        examples = {
            "ignore": "skill.used",
            "defer": "task.deferred",
            "process": "task.created",
            "delegate": "skill.failed",
            "surface": "decision.required",
        }
        for expected, event_type in examples.items():
            with self.subTest(disposition=expected):
                result = routing.route_event(self.make_event(event_type))
                self.assertEqual(result["disposition"], expected)

    def test_rules_override_default(self) -> None:
        result = routing.route_event(self.make_event(), {"task.created": "ignore"})
        self.assertEqual(result["disposition"], "ignore")
        self.assertEqual(result["rule"], "override")
        self.assertEqual(result["reason"], "override route for task.created")

    def test_invalid_rule_disposition_raises(self) -> None:
        with self.assertRaises(ValueError):
            routing.route_event(self.make_event(), {"task.created": "invalid"})

    def test_unknown_rule_type_raises(self) -> None:
        with self.assertRaises(ValueError):
            routing.route_event(self.make_event(), {"task.unknown": "ignore"})

    def test_invalid_event_raises(self) -> None:
        with self.assertRaises(ValueError):
            routing.route_event({"type": "task.created"})

    def test_sensitive_delegation_is_surfaced(self) -> None:
        event = self.make_event("task.created", sensitivity="sensitive")
        result = routing.route_event(event, {"task.created": "delegate"})
        self.assertEqual(result["disposition"], "surface")
        self.assertEqual(result["rule"], "local_only")
        self.assertEqual(result["reason"], "local-only event cannot be delegated; surfaced for the user")

    def test_result_never_contains_payload(self) -> None:
        result = routing.route_event(self.make_event())
        self.assertNotIn("payload", result)
        self.assertNotIn("private", result.values())


if __name__ == "__main__":
    unittest.main()
