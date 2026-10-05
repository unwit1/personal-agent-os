"""Tests for window_queue module: window item <-> queue item conversion."""

from __future__ import annotations

import sys
import json
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import contracts, event_bus, window_queue


class TestQueueItemFromWindowItem(unittest.TestCase):
    """Tests for queue_item_from_window_item conversion."""

    def test_basic_conversion(self) -> None:
        """Basic window item converts to valid queue item."""
        window_item = {
            "id": "test-1",
            "kind": "task",
            "tab": "work",
            "title": "Test Task",
        }
        qi = window_queue.queue_item_from_window_item(window_item, "mail")

        self.assertEqual(qi["schema"], contracts.QUEUE_ITEM_SCHEMA)
        self.assertEqual(qi["status"], "queued")
        self.assertEqual(qi["source"], "window:mail")
        self.assertEqual(qi["domain"], "executive-window")
        self.assertEqual(qi["sensitivity"], "personal")
        self.assertEqual(qi["provider"], "mail")
        self.assertIn("id", qi)
        self.assertIn("entity_id", qi)
        self.assertIn("queued_at", qi)

        errors = contracts.validate_queue_item(qi)
        self.assertEqual(errors, [])

    def test_with_why_converts_to_reason(self) -> None:
        """Window item 'why' field converts to queue item 'reason'."""
        window_item = {
            "id": "gate-123",
            "kind": "orchestrator_gate",
            "tab": "work",
            "title": "Approval needed",
            "why": "Operator approval required for next step",
        }
        qi = window_queue.queue_item_from_window_item(window_item, "orchestrator")

        self.assertEqual(qi["reason"], "Operator approval required for next step")

        errors = contracts.validate_queue_item(qi)
        self.assertEqual(errors, [])

    def test_non_string_why_is_omitted(self) -> None:
        """Non-string 'why' field is omitted from queue item."""
        window_item = {
            "id": "test-2",
            "kind": "task",
            "tab": "work",
            "title": "Test",
            "why": 123,
        }
        qi = window_queue.queue_item_from_window_item(window_item, "mail")

        self.assertNotIn("reason", qi)
        errors = contracts.validate_queue_item(qi)
        self.assertEqual(errors, [])

    def test_score_converts_to_priority(self) -> None:
        """Window item 'score' (int/float) converts to queue item 'priority'."""
        window_item = {
            "id": "test-3",
            "kind": "task",
            "tab": "work",
            "title": "Test with score",
            "score": 42,
        }
        qi = window_queue.queue_item_from_window_item(window_item, "mail")

        self.assertEqual(qi["priority"], 42)
        errors = contracts.validate_queue_item(qi)
        self.assertEqual(errors, [])

    def test_float_score_converts_to_priority(self) -> None:
        """Float score converts to priority."""
        window_item = {
            "id": "test-4",
            "kind": "task",
            "tab": "work",
            "title": "Test with float score",
            "score": 3.14,
        }
        qi = window_queue.queue_item_from_window_item(window_item, "mail")

        self.assertEqual(qi["priority"], 3.14)
        errors = contracts.validate_queue_item(qi)
        self.assertEqual(errors, [])

    def test_negative_score_is_omitted(self) -> None:
        """Negative score is omitted (not a valid priority)."""
        window_item = {
            "id": "test-5",
            "kind": "task",
            "tab": "work",
            "title": "Test with negative score",
            "score": -5,
        }
        qi = window_queue.queue_item_from_window_item(window_item, "mail")

        self.assertNotIn("priority", qi)
        errors = contracts.validate_queue_item(qi)
        self.assertEqual(errors, [])

    def test_zero_score_is_included(self) -> None:
        """Zero score is included as priority (valid, >= 0)."""
        window_item = {
            "id": "test-6",
            "kind": "task",
            "tab": "work",
            "title": "Test with zero score",
            "score": 0,
        }
        qi = window_queue.queue_item_from_window_item(window_item, "mail")

        self.assertEqual(qi["priority"], 0)
        errors = contracts.validate_queue_item(qi)
        self.assertEqual(errors, [])

    def test_bool_score_is_omitted(self) -> None:
        """Boolean score (which is technically int in Python) is omitted."""
        window_item = {
            "id": "test-7",
            "kind": "task",
            "tab": "work",
            "title": "Test with bool score",
            "score": True,
        }
        qi = window_queue.queue_item_from_window_item(window_item, "mail")

        self.assertNotIn("priority", qi)
        errors = contracts.validate_queue_item(qi)
        self.assertEqual(errors, [])

    def test_non_numeric_score_is_omitted(self) -> None:
        """Non-numeric score is omitted."""
        window_item = {
            "id": "test-8",
            "kind": "task",
            "tab": "work",
            "title": "Test with string score",
            "score": "high",
        }
        qi = window_queue.queue_item_from_window_item(window_item, "mail")

        self.assertNotIn("priority", qi)
        errors = contracts.validate_queue_item(qi)
        self.assertEqual(errors, [])

    def test_sensitivity_personal(self) -> None:
        """Valid 'personal' sensitivity is preserved."""
        window_item = {
            "id": "test-9",
            "kind": "task",
            "tab": "work",
            "title": "Test",
            "sensitivity": "personal",
        }
        qi = window_queue.queue_item_from_window_item(window_item, "mail")

        self.assertEqual(qi["sensitivity"], "personal")
        self.assertNotIn("local_only", qi)
        errors = contracts.validate_queue_item(qi)
        self.assertEqual(errors, [])

    def test_sensitivity_public(self) -> None:
        """Valid 'public' sensitivity is preserved."""
        window_item = {
            "id": "test-10",
            "kind": "task",
            "tab": "work",
            "title": "Test",
            "sensitivity": "public",
        }
        qi = window_queue.queue_item_from_window_item(window_item, "mail")

        self.assertEqual(qi["sensitivity"], "public")
        self.assertNotIn("local_only", qi)
        errors = contracts.validate_queue_item(qi)
        self.assertEqual(errors, [])

    def test_sensitivity_sensitive_requires_local_only(self) -> None:
        """'sensitive' sensitivity requires local_only=true."""
        window_item = {
            "id": "test-11",
            "kind": "task",
            "tab": "work",
            "title": "Test",
            "sensitivity": "sensitive",
        }
        qi = window_queue.queue_item_from_window_item(window_item, "mail")

        self.assertEqual(qi["sensitivity"], "sensitive")
        self.assertTrue(qi["local_only"])
        errors = contracts.validate_queue_item(qi)
        self.assertEqual(errors, [])

    def test_sensitivity_secret_requires_local_only(self) -> None:
        """'secret' sensitivity requires local_only=true."""
        window_item = {
            "id": "test-12",
            "kind": "task",
            "tab": "work",
            "title": "Test",
            "sensitivity": "secret",
        }
        qi = window_queue.queue_item_from_window_item(window_item, "mail")

        self.assertEqual(qi["sensitivity"], "secret")
        self.assertTrue(qi["local_only"])
        errors = contracts.validate_queue_item(qi)
        self.assertEqual(errors, [])

    def test_invalid_sensitivity_defaults_to_personal(self) -> None:
        """Invalid sensitivity defaults to 'personal'."""
        window_item = {
            "id": "test-13",
            "kind": "task",
            "tab": "work",
            "title": "Test",
            "sensitivity": "unknown",
        }
        qi = window_queue.queue_item_from_window_item(window_item, "mail")

        self.assertEqual(qi["sensitivity"], "personal")
        errors = contracts.validate_queue_item(qi)
        self.assertEqual(errors, [])

    def test_non_string_sensitivity_defaults_to_personal(self) -> None:
        """Non-string sensitivity defaults to 'personal'."""
        window_item = {
            "id": "test-14",
            "kind": "task",
            "tab": "work",
            "title": "Test",
            "sensitivity": 123,
        }
        qi = window_queue.queue_item_from_window_item(window_item, "mail")

        self.assertEqual(qi["sensitivity"], "personal")
        errors = contracts.validate_queue_item(qi)
        self.assertEqual(errors, [])

    def test_window_item_is_deep_copied(self) -> None:
        """Original window item is not modified."""
        window_item = {
            "id": "test-15",
            "kind": "task",
            "tab": "work",
            "title": "Test",
            "nested": {"value": "original"},
        }
        original_nested = window_item["nested"]

        qi = window_queue.queue_item_from_window_item(window_item, "mail")

        qi["window_item"]["nested"]["value"] = "modified"
        self.assertEqual(window_item["nested"]["value"], "original")
        self.assertEqual(original_nested["value"], "original")

    def test_queued_at_defaults_to_now(self) -> None:
        """queued_at defaults to current timestamp if not provided."""
        window_item = {
            "id": "test-16",
            "kind": "task",
            "tab": "work",
            "title": "Test",
        }

        before = datetime.now(timezone.utc).isoformat()
        qi = window_queue.queue_item_from_window_item(window_item, "mail")
        after = datetime.now(timezone.utc).isoformat()

        queued_at = qi["queued_at"]
        # Check it's a valid ISO timestamp
        datetime.fromisoformat(queued_at.replace("Z", "+00:00"))
        # Check it's within reasonable bounds
        self.assertGreaterEqual(queued_at, before)
        self.assertLessEqual(queued_at, after)

    def test_queued_at_can_be_provided(self) -> None:
        """queued_at can be explicitly provided."""
        window_item = {
            "id": "test-17",
            "kind": "task",
            "tab": "work",
            "title": "Test",
        }
        custom_time = "2026-01-15T10:30:00+00:00"

        qi = window_queue.queue_item_from_window_item(
            window_item, "mail", queued_at=custom_time
        )

        self.assertEqual(qi["queued_at"], custom_time)
        errors = contracts.validate_queue_item(qi)
        self.assertEqual(errors, [])

    def test_stable_ids_same_input_same_provider(self) -> None:
        """Same window item + provider produce stable IDs."""
        window_item = {
            "id": "gate-123",
            "kind": "orchestrator_gate",
            "tab": "work",
            "title": "Test",
        }

        qi1 = window_queue.queue_item_from_window_item(window_item, "orchestrator")
        qi2 = window_queue.queue_item_from_window_item(window_item, "orchestrator")

        self.assertEqual(qi1["id"], qi2["id"])
        self.assertEqual(qi1["entity_id"], qi2["entity_id"])

    def test_different_providers_produce_different_ids(self) -> None:
        """Different providers produce different IDs."""
        window_item = {
            "id": "item-123",
            "kind": "task",
            "tab": "work",
            "title": "Test",
        }

        qi_mail = window_queue.queue_item_from_window_item(window_item, "mail")
        qi_app = window_queue.queue_item_from_window_item(window_item, "applicants")

        self.assertNotEqual(qi_mail["id"], qi_app["id"])
        self.assertNotEqual(qi_mail["entity_id"], qi_app["entity_id"])

    def test_different_item_ids_produce_different_queue_ids(self) -> None:
        """Different window item IDs produce different queue item IDs."""
        item1 = {
            "id": "id-1",
            "kind": "task",
            "tab": "work",
            "title": "Test",
        }
        item2 = {
            "id": "id-2",
            "kind": "task",
            "tab": "work",
            "title": "Test",
        }

        qi1 = window_queue.queue_item_from_window_item(item1, "mail")
        qi2 = window_queue.queue_item_from_window_item(item2, "mail")

        self.assertNotEqual(qi1["id"], qi2["id"])
        self.assertNotEqual(qi1["entity_id"], qi2["entity_id"])

    def test_entity_id_format_from_window_item(self) -> None:
        """Entity ID is properly formatted for window items."""
        window_item = {
            "id": "test-id",
            "kind": "task",
            "tab": "work",
            "title": "Test",
        }

        qi = window_queue.queue_item_from_window_item(window_item, "testprov")

        self.assertRegex(qi["entity_id"], r"^ex-task-[0-9a-f]{16}$")
        self.assertRegex(qi["id"], r"^qi-[0-9a-f]{16}$")


class TestWindowItemFromQueueItem(unittest.TestCase):
    """Tests for window_item_from_queue_item conversion."""

    def test_basic_round_trip(self) -> None:
        """Window item round-trips through queue item conversion."""
        original = {
            "id": "test-1",
            "kind": "task",
            "tab": "work",
            "title": "Test Task",
        }

        qi = window_queue.queue_item_from_window_item(original, "mail")
        recovered = window_queue.window_item_from_queue_item(qi)

        self.assertEqual(recovered, original)

    def test_round_trip_with_why(self) -> None:
        """Window item with 'why' round-trips correctly."""
        original = {
            "id": "test-2",
            "kind": "task",
            "tab": "work",
            "title": "Test Task",
            "why": "This is why",
        }

        qi = window_queue.queue_item_from_window_item(original, "mail")
        recovered = window_queue.window_item_from_queue_item(qi)

        self.assertEqual(recovered, original)

    def test_round_trip_with_none_why(self) -> None:
        """Window item with why=None round-trips correctly."""
        original = {
            "id": "test-3",
            "kind": "task",
            "tab": "work",
            "title": "Test Task",
            "why": None,
        }

        qi = window_queue.queue_item_from_window_item(original, "mail")
        recovered = window_queue.window_item_from_queue_item(qi)

        self.assertEqual(recovered, original)

    def test_reason_maps_to_why(self) -> None:
        """Queue item 'reason' becomes window item 'why'."""
        qi = {
            "id": "qi-abc123def456abc1",
            "entity_id": "ex-task-abc123def456abc1",
            "queued_at": "2026-01-15T10:00:00+00:00",
            "source": "window:mail",
            "domain": "executive-window",
            "sensitivity": "personal",
            "schema": contracts.QUEUE_ITEM_SCHEMA,
            "status": "queued",
            "provider": "mail",
            "reason": "Important reason",
            "window_item": {
                "id": "mail-1",
                "kind": "email",
                "tab": "work",
                "title": "Check email",
            },
        }

        recovered = window_queue.window_item_from_queue_item(qi)

        self.assertEqual(recovered["why"], "Important reason")
        self.assertEqual(recovered["id"], "mail-1")

    def test_no_reason_no_why(self) -> None:
        """Queue item without reason doesn't add why."""
        qi = {
            "id": "qi-abc123def456abc1",
            "entity_id": "ex-task-abc123def456abc1",
            "queued_at": "2026-01-15T10:00:00+00:00",
            "source": "window:mail",
            "domain": "executive-window",
            "sensitivity": "personal",
            "schema": contracts.QUEUE_ITEM_SCHEMA,
            "status": "queued",
            "provider": "mail",
            "window_item": {
                "id": "mail-1",
                "kind": "email",
                "tab": "work",
                "title": "Check email",
            },
        }

        recovered = window_queue.window_item_from_queue_item(qi)

        self.assertNotIn("why", recovered)

    def test_reason_none_no_why(self) -> None:
        """Queue item with reason=None doesn't add why."""
        qi = {
            "id": "qi-abc123def456abc1",
            "entity_id": "ex-task-abc123def456abc1",
            "queued_at": "2026-01-15T10:00:00+00:00",
            "source": "window:mail",
            "domain": "executive-window",
            "sensitivity": "personal",
            "schema": contracts.QUEUE_ITEM_SCHEMA,
            "status": "queued",
            "provider": "mail",
            "reason": None,
            "window_item": {
                "id": "mail-1",
                "kind": "email",
                "tab": "work",
                "title": "Check email",
            },
        }

        recovered = window_queue.window_item_from_queue_item(qi)

        self.assertNotIn("why", recovered)

    def test_missing_window_item_returns_empty_dict(self) -> None:
        """Queue item without window_item returns empty dict."""
        qi = {
            "id": "qi-abc123def456abc1",
            "entity_id": "ex-task-abc123def456abc1",
        }

        recovered = window_queue.window_item_from_queue_item(qi)

        self.assertEqual(recovered, {})

    def test_window_item_is_deep_copied(self) -> None:
        """Window item is deep-copied, not referenced."""
        qi = {
            "id": "qi-abc123def456abc1",
            "entity_id": "ex-task-abc123def456abc1",
            "window_item": {
                "id": "test-1",
                "nested": {"value": "original"},
            },
        }

        recovered = window_queue.window_item_from_queue_item(qi)
        recovered["nested"]["value"] = "modified"

        self.assertEqual(qi["window_item"]["nested"]["value"], "original")


class TestPublishWindowItem(unittest.TestCase):
    """Tests for publish_window_item."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.bus = event_bus.EventBus(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_publish_creates_event_with_queue_item_payload(self) -> None:
        """publish_window_item creates a task.created event."""
        window_item = {
            "id": "gate-123",
            "kind": "orchestrator_gate",
            "tab": "work",
            "title": "Approval needed",
            "why": "Operator approval required",
        }

        event, created = window_queue.publish_window_item(self.bus, window_item, "orchestrator")

        self.assertTrue(created)
        self.assertEqual(event["type"], "task.created")
        self.assertEqual(event["source"], "window:orchestrator")
        self.assertEqual(event["domain"], "executive-window")

    def test_publish_includes_queue_item_data_in_payload(self) -> None:
        """Published event payload includes queue item IDs and metadata."""
        window_item = {
            "id": "test-1",
            "kind": "task",
            "tab": "work",
            "title": "Test Task",
        }

        event, _ = window_queue.publish_window_item(self.bus, window_item, "mail")

        payload = event["payload"]
        self.assertIn("queue_item_id", payload)
        self.assertIn("entity_id", payload)
        self.assertIn("provider", payload)
        self.assertIn("item_id", payload)
        self.assertIn("kind", payload)
        self.assertIn("tab", payload)

        self.assertEqual(payload["provider"], "mail")
        self.assertEqual(payload["item_id"], "test-1")
        self.assertEqual(payload["kind"], "task")

    def test_publish_payload_holds_no_item_text(self) -> None:
        """The persisted payload never carries title, why or the window item."""
        window_item = {"id": "t-2", "kind": "task", "tab": "work", "title": "Jane Doe - Tech", "why": "waiting 3 days"}

        event, _ = window_queue.publish_window_item(self.bus, window_item, "applicants")

        self.assertEqual(
            sorted(event["payload"]),
            ["entity_id", "item_id", "kind", "provider", "queue_item_id", "tab"],
        )
        self.assertNotIn("Jane Doe", json.dumps(event))
        self.assertNotIn("waiting 3 days", json.dumps(event))

    def test_publish_reuses_a_prebuilt_queue_item(self) -> None:
        window_item = {"id": "t-3", "kind": "task", "tab": "work", "title": "x"}
        qi = window_queue.queue_item_from_window_item(window_item, "mail")
        with patch.object(window_queue, "queue_item_from_window_item", side_effect=AssertionError("converted twice")):
            event, created = window_queue.publish_window_item(self.bus, window_item, "mail", qi)
        self.assertTrue(created)
        self.assertEqual(event["payload"]["queue_item_id"], qi["id"])

    def test_publish_returns_created_true_on_first_publish(self) -> None:
        """First publish of an item returns created=True."""
        window_item = {
            "id": "unique-item-1",
            "kind": "task",
            "tab": "work",
            "title": "Test",
        }

        _, created = window_queue.publish_window_item(self.bus, window_item, "mail")

        self.assertTrue(created)

    def test_publish_returns_created_false_on_duplicate(self) -> None:
        """Duplicate publish of same item returns created=False."""
        window_item = {
            "id": "unique-item-2",
            "kind": "task",
            "tab": "work",
            "title": "Test",
        }

        _, created1 = window_queue.publish_window_item(self.bus, window_item, "mail")
        _, created2 = window_queue.publish_window_item(self.bus, window_item, "mail")

        self.assertTrue(created1)
        self.assertFalse(created2)

    def test_publish_respects_sensitivity(self) -> None:
        """Published event respects item sensitivity."""
        window_item = {
            "id": "sensitive-item",
            "kind": "task",
            "tab": "work",
            "title": "Sensitive",
            "sensitivity": "sensitive",
        }

        event, _ = window_queue.publish_window_item(self.bus, window_item, "mail")

        self.assertEqual(event["sensitivity"], "sensitive")
        self.assertTrue(event.get("local_only"))

    def test_publish_uses_subject_as_entity_id(self) -> None:
        """Published event subject matches the entity_id."""
        window_item = {
            "id": "test-1",
            "kind": "task",
            "tab": "work",
            "title": "Test",
        }

        event, _ = window_queue.publish_window_item(self.bus, window_item, "mail")

        self.assertIn("subject", event)
        self.assertEqual(event["subject"], event["payload"]["entity_id"])


if __name__ == "__main__":
    unittest.main()
