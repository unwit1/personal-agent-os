"""Tests for EventBus implementation."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import event_bus, contracts


class EventBusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.bus = event_bus.EventBus(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_publish_creates_file_and_returns_created_true(self) -> None:
        """publish creates file on first publish."""
        self.assertFalse(self.bus.path.exists())

        event, created = self.bus.publish(
            event_type="task.created",
            source="test-agent",
            dedup_key="key-1",
            payload={"title": "Test Task"},
        )

        self.assertTrue(created)
        self.assertTrue(self.bus.path.exists())
        self.assertEqual(event["type"], "task.created")
        self.assertEqual(event["source"], "test-agent")
        self.assertEqual(event["dedup_key"], "key-1")

    def test_publish_same_dedup_key_returns_created_false(self) -> None:
        """publish with same dedup_key returns created=False."""
        event1, created1 = self.bus.publish(
            event_type="task.created",
            source="test-agent",
            dedup_key="key-1",
            payload={"title": "Test Task"},
        )
        self.assertTrue(created1)

        event2, created2 = self.bus.publish(
            event_type="task.created",
            source="test-agent",
            dedup_key="key-1",
            payload={"title": "Different Task"},
        )
        self.assertFalse(created2)
        self.assertEqual(event1["id"], event2["id"])

        # Only one line in file
        with open(self.bus.path, "r") as f:
            lines = [l for l in f if l.strip()]
        self.assertEqual(len(lines), 1)

    def test_publish_different_dedup_key_creates_second_event(self) -> None:
        """publish with different dedup_key creates a new event."""
        event1, _ = self.bus.publish(
            event_type="task.created",
            source="test-agent",
            dedup_key="key-1",
            payload={"title": "Task 1"},
        )

        event2, created = self.bus.publish(
            event_type="task.created",
            source="test-agent",
            dedup_key="key-2",
            payload={"title": "Task 2"},
        )

        self.assertTrue(created)
        self.assertNotEqual(event1["id"], event2["id"])

        # Two lines in file
        with open(self.bus.path, "r") as f:
            lines = [l for l in f if l.strip()]
        self.assertEqual(len(lines), 2)

    def test_invalid_event_type_raises_value_error_and_writes_nothing(self) -> None:
        """publish with invalid event type raises ValueError."""
        self.assertFalse(self.bus.path.exists())

        with self.assertRaises(ValueError):
            self.bus.publish(
                event_type="invalid.type",
                source="test-agent",
                dedup_key="key-1",
                payload={},
            )

        # File should not be created
        self.assertFalse(self.bus.path.exists())

    def test_sensitive_event_gets_local_only_true(self) -> None:
        """publish with sensitive sensitivity sets local_only=True."""
        event, _ = self.bus.publish(
            event_type="task.created",
            source="test-agent",
            dedup_key="key-1",
            payload={},
            sensitivity="sensitive",
        )

        self.assertEqual(event.get("local_only"), True)

    def test_secret_event_gets_local_only_true(self) -> None:
        """publish with secret sensitivity sets local_only=True."""
        event, _ = self.bus.publish(
            event_type="task.created",
            source="test-agent",
            dedup_key="key-1",
            payload={},
            sensitivity="secret",
        )

        self.assertEqual(event.get("local_only"), True)

    def test_events_filters_by_type(self) -> None:
        """events() filters by exact type match."""
        self.bus.publish(
            event_type="task.created",
            source="test-agent",
            dedup_key="k1",
            payload={},
        )
        self.bus.publish(
            event_type="task.completed",
            source="test-agent",
            dedup_key="k2",
            payload={},
        )

        result = self.bus.events(event_type="task.created")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "task.created")

    def test_events_filters_by_subject(self) -> None:
        """events() filters by subject."""
        self.bus.publish(
            event_type="task.created",
            source="test-agent",
            dedup_key="k1",
            payload={},
            subject="project-a",
        )
        self.bus.publish(
            event_type="task.created",
            source="test-agent",
            dedup_key="k2",
            payload={},
            subject="project-b",
        )

        result = self.bus.events(subject="project-a")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].get("subject"), "project-a")

    def test_events_filters_by_since(self) -> None:
        """events() filters by occurred_at >= since."""
        self.bus.publish(
            event_type="task.created",
            source="test-agent",
            dedup_key="k1",
            payload={},
            occurred_at="2025-01-01T10:00:00+00:00",
        )
        self.bus.publish(
            event_type="task.created",
            source="test-agent",
            dedup_key="k2",
            payload={},
            occurred_at="2025-01-02T10:00:00+00:00",
        )

        result = self.bus.events(since="2025-01-02T00:00:00+00:00")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["dedup_key"], "k2")

    def test_get_by_id(self) -> None:
        """get() returns event by id."""
        event, _ = self.bus.publish(
            event_type="task.created",
            source="test-agent",
            dedup_key="key-1",
            payload={"title": "Test"},
        )

        found = self.bus.get(event["id"])
        self.assertIsNotNone(found)
        self.assertEqual(found["id"], event["id"])

    def test_get_nonexistent_returns_none(self) -> None:
        """get() returns None for unknown id."""
        result = self.bus.get("evt-0000000000000000")
        self.assertIsNone(result)

    def test_missing_log_returns_empty_list(self) -> None:
        """events() returns [] when log doesn't exist."""
        # Don't publish anything, so file won't exist
        result = self.bus.events()
        self.assertEqual(result, [])

    def test_append_validates_event(self) -> None:
        """append() validates the event before writing."""
        invalid = {
            "type": "task.created",
            # Missing required fields
        }

        with self.assertRaises(ValueError):
            self.bus.append(invalid)

        # Nothing should be written
        self.assertFalse(self.bus.path.exists())

    def test_append_valid_event(self) -> None:
        """append() writes a valid event."""
        event, _ = self.bus.publish(
            event_type="task.created",
            source="test-agent",
            dedup_key="key-1",
            payload={"title": "Test"},
        )

        self.bus.append(event)
        self.assertTrue(self.bus.path.exists())

        found = self.bus.get(event["id"])
        self.assertIsNotNone(found)
        self.assertEqual(found["id"], event["id"])

    def test_append_deduplicates_by_id(self) -> None:
        """append() skips if event id already exists."""
        event, _ = self.bus.publish(
            event_type="task.created",
            source="test-agent",
            dedup_key="key-1",
            payload={"title": "Test"},
        )

        self.bus.append(event)
        self.bus.append(event)

        # Only one line in file
        with open(self.bus.path, "r") as f:
            lines = [l for l in f if l.strip()]
        self.assertEqual(len(lines), 1)

    def test_events_skips_blank_lines(self) -> None:
        """events() skips blank lines in the log."""
        # Manually create a log with blank lines
        event, _ = self.bus.publish(
            event_type="task.created",
            source="test-agent",
            dedup_key="key-1",
            payload={},
        )

        with open(self.bus.path, "w") as f:
            f.write(json.dumps(event) + "\n")
            f.write("\n")  # blank line
            f.write(json.dumps(event) + "\n")

        result = self.bus.events()
        # Should only get unique events (one per id)
        self.assertEqual(len(result), 2)

    def test_events_multiple_filters_combined(self) -> None:
        """events() applies multiple filters together."""
        self.bus.publish(
            event_type="task.created",
            source="test-agent",
            dedup_key="k1",
            payload={},
            occurred_at="2025-01-01T10:00:00+00:00",
            subject="project-a",
        )
        self.bus.publish(
            event_type="task.completed",
            source="test-agent",
            dedup_key="k2",
            payload={},
            occurred_at="2025-01-02T10:00:00+00:00",
            subject="project-a",
        )
        self.bus.publish(
            event_type="task.created",
            source="test-agent",
            dedup_key="k3",
            payload={},
            occurred_at="2025-01-02T10:00:00+00:00",
            subject="project-b",
        )

        result = self.bus.events(
            event_type="task.created",
            subject="project-a",
            since="2025-01-01T00:00:00+00:00",
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["dedup_key"], "k1")

    def test_publish_with_custom_occurred_at(self) -> None:
        """publish() respects custom occurred_at parameter."""
        event, _ = self.bus.publish(
            event_type="task.created",
            source="test-agent",
            dedup_key="key-1",
            payload={},
            occurred_at="2025-06-15T12:30:00+00:00",
        )

        self.assertEqual(event["occurred_at"], "2025-06-15T12:30:00+00:00")

    def test_publish_with_provenance(self) -> None:
        """publish() includes provenance when provided."""
        event, _ = self.bus.publish(
            event_type="task.created",
            source="test-agent",
            dedup_key="key-1",
            payload={},
            provenance=["agent-id-1", "agent-id-2"],
        )

        self.assertEqual(event.get("provenance"), ["agent-id-1", "agent-id-2"])


if __name__ == "__main__":
    unittest.main()
