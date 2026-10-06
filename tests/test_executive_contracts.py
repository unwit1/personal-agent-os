"""Tests for executive contracts module."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.contracts import (
    AUTONOMY_LEVELS,
    ENTITY_KINDS,
    ENTITY_SCHEMA,
    ENTITY_STATUSES,
    EVENT_SCHEMA,
    EVENT_TYPES,
    QUEUE_ITEM_SCHEMA,
    QUEUE_STATUSES,
    SENSITIVITIES,
    entity_id,
    event_id,
    queue_item_id,
    requires_local_only,
    stable_id,
    validate_entity,
    validate_event,
    validate_queue_item,
)


class TestStableId(unittest.TestCase):
    def test_stable_id_basic(self):
        result = stable_id("test", "part1", "part2")
        self.assertTrue(result.startswith("test-"))
        self.assertEqual(len(result), len("test-") + 16)
        # Should be deterministic
        result2 = stable_id("test", "part1", "part2")
        self.assertEqual(result, result2)

    def test_stable_id_different_parts(self):
        result1 = stable_id("test", "a", "b")
        result2 = stable_id("test", "a", "c")
        self.assertNotEqual(result1, result2)

    def test_stable_id_empty_parts(self):
        result = stable_id("test")
        self.assertTrue(result.startswith("test-"))


class TestEntityId(unittest.TestCase):
    def test_entity_id_valid_kind(self):
        result = entity_id("task", "source", "key")
        self.assertTrue(result.startswith("ex-task-"))
        self.assertEqual(len(result), len("ex-task-") + 16)
        # Verify it matches the entity id pattern
        self.assertTrue(result.startswith("ex-"))
        self.assertRegex(result, r"^ex-task-[0-9a-f]{16}$")

    def test_entity_id_invalid_kind(self):
        with self.assertRaises(ValueError) as ctx:
            entity_id("invalid_kind", "source", "key")
        self.assertIn("unknown entity kind", str(ctx.exception))

    def test_entity_id_all_kinds(self):
        for kind in ENTITY_KINDS:
            result = entity_id(kind, "source", "key")
            self.assertRegex(result, f"^ex-{kind}-[0-9a-f]{{16}}$")


class TestEventId(unittest.TestCase):
    def test_event_id(self):
        result = event_id("task.created", "source", "dedup")
        self.assertTrue(result.startswith("evt-"))
        self.assertEqual(len(result), len("evt-") + 16)
        self.assertRegex(result, r"^evt-[0-9a-f]{16}$")


class TestQueueItemId(unittest.TestCase):
    def test_queue_item_id(self):
        eid = entity_id("task", "source", "key")
        result = queue_item_id(eid)
        self.assertTrue(result.startswith("qi-"))
        self.assertRegex(result, r"^qi-[0-9a-f]{16}$")


class TestRequiresLocalOnly(unittest.TestCase):
    def test_public_not_local_only(self):
        self.assertFalse(requires_local_only("public"))

    def test_personal_not_local_only(self):
        self.assertFalse(requires_local_only("personal"))

    def test_sensitive_requires_local_only(self):
        self.assertTrue(requires_local_only("sensitive"))

    def test_secret_requires_local_only(self):
        self.assertTrue(requires_local_only("secret"))


class TestValidateEntity(unittest.TestCase):
    def _valid_entity(self) -> dict:
        return {
            "schema": ENTITY_SCHEMA,
            "id": "ex-task-0123456789abcdef",
            "kind": "task",
            "title": "Test Task",
            "status": "open",
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
            "source": "test-source",
            "domain": "test-domain",
            "sensitivity": "public",
            "provenance": ["source1"],
        }

    def test_valid_entity(self):
        errors = validate_entity(self._valid_entity())
        self.assertEqual(errors, [])

    def test_not_dict(self):
        errors = validate_entity("not a dict")
        self.assertEqual(len(errors), 1)
        self.assertIn("not a JSON object", errors[0])

    def test_missing_required_fields(self):
        data = self._valid_entity()
        del data["title"]
        errors = validate_entity(data)
        self.assertTrue(any("missing" in e and "title" in e for e in errors))

    def test_wrong_schema(self):
        data = self._valid_entity()
        data["schema"] = "wrong-schema"
        errors = validate_entity(data)
        self.assertTrue(any("schema must be" in e for e in errors))

    def test_invalid_id_format(self):
        data = self._valid_entity()
        data["id"] = "invalid-id"
        errors = validate_entity(data)
        self.assertTrue(any("invalid id" in e for e in errors))

    def test_id_kind_mismatch(self):
        data = self._valid_entity()
        data["id"] = "ex-commitment-0123456789abcdef"
        data["kind"] = "task"
        errors = validate_entity(data)
        self.assertTrue(any("id kind segment" in e for e in errors))

    def test_unknown_kind(self):
        data = self._valid_entity()
        data["kind"] = "unknown_kind"
        data["id"] = "ex-unknown_kind-0123456789abcdef"
        errors = validate_entity(data)
        self.assertTrue(any("unknown kind" in e for e in errors))

    def test_empty_title(self):
        data = self._valid_entity()
        data["title"] = ""
        errors = validate_entity(data)
        self.assertTrue(any("title must be non-empty" in e for e in errors))

    def test_unknown_status(self):
        data = self._valid_entity()
        data["status"] = "unknown_status"
        errors = validate_entity(data)
        self.assertTrue(any("unknown status" in e for e in errors))

    def test_invalid_timestamp(self):
        data = self._valid_entity()
        data["created_at"] = "not-a-timestamp"
        errors = validate_entity(data)
        self.assertTrue(any("created_at" in e and "invalid" in e for e in errors))

    def test_valid_timestamp_with_z(self):
        data = self._valid_entity()
        data["created_at"] = "2026-01-01T00:00:00Z"
        errors = validate_entity(data)
        # Should not have created_at error
        self.assertFalse(any("created_at" in e and "invalid" in e for e in errors))

    def test_created_at_null(self):
        data = self._valid_entity()
        data["created_at"] = None
        errors = validate_entity(data)
        self.assertTrue(any("created_at" in e and "not a string" in e for e in errors))

    def test_updated_at_null(self):
        data = self._valid_entity()
        data["updated_at"] = None
        errors = validate_entity(data)
        self.assertTrue(any("updated_at" in e and "not a string" in e for e in errors))

    def test_unknown_sensitivity(self):
        data = self._valid_entity()
        data["sensitivity"] = "unknown_sensitivity"
        errors = validate_entity(data)
        self.assertTrue(any("unknown sensitivity" in e for e in errors))

    def test_empty_source(self):
        data = self._valid_entity()
        data["source"] = ""
        errors = validate_entity(data)
        self.assertTrue(any("source must be non-empty" in e for e in errors))

    def test_empty_domain(self):
        data = self._valid_entity()
        data["domain"] = ""
        errors = validate_entity(data)
        self.assertTrue(any("domain must be non-empty" in e for e in errors))

    def test_invalid_confidence_high(self):
        data = self._valid_entity()
        data["confidence"] = 1.5
        errors = validate_entity(data)
        self.assertTrue(any("confidence must be in [0, 1]" in e for e in errors))

    def test_invalid_confidence_low(self):
        data = self._valid_entity()
        data["confidence"] = -0.1
        errors = validate_entity(data)
        self.assertTrue(any("confidence must be in [0, 1]" in e for e in errors))

    def test_valid_confidence(self):
        data = self._valid_entity()
        data["confidence"] = 0.5
        errors = validate_entity(data)
        self.assertFalse(any("confidence" in e for e in errors))

    def test_null_confidence(self):
        data = self._valid_entity()
        data["confidence"] = None
        errors = validate_entity(data)
        self.assertFalse(any("confidence" in e for e in errors))

    def test_empty_provenance(self):
        data = self._valid_entity()
        data["provenance"] = []
        errors = validate_entity(data)
        self.assertTrue(any("provenance must be non-empty" in e for e in errors))

    def test_provenance_not_list(self):
        data = self._valid_entity()
        data["provenance"] = "not-a-list"
        errors = validate_entity(data)
        self.assertTrue(any("provenance must be a list" in e for e in errors))

    def test_superseded_without_superseded_by(self):
        data = self._valid_entity()
        data["status"] = "superseded"
        errors = validate_entity(data)
        self.assertTrue(any("superseded" in e and "requires non-empty" in e for e in errors))

    def test_superseded_with_superseded_by(self):
        data = self._valid_entity()
        data["status"] = "superseded"
        data["superseded_by"] = "ex-task-0123456789abcdef"
        errors = validate_entity(data)
        self.assertFalse(any("superseded" in e for e in errors))

    def test_sensitive_without_local_only(self):
        data = self._valid_entity()
        data["sensitivity"] = "sensitive"
        errors = validate_entity(data)
        self.assertTrue(any("requires local_only=true" in e for e in errors))

    def test_sensitive_with_local_only(self):
        data = self._valid_entity()
        data["sensitivity"] = "sensitive"
        data["local_only"] = True
        errors = validate_entity(data)
        self.assertFalse(any("requires local_only=true" in e for e in errors))

    def test_secret_without_local_only(self):
        data = self._valid_entity()
        data["sensitivity"] = "secret"
        errors = validate_entity(data)
        self.assertTrue(any("requires local_only=true" in e for e in errors))

    def test_kind_as_list(self):
        data = self._valid_entity()
        data["kind"] = ["task"]
        errors = validate_entity(data)
        self.assertTrue(any("kind is not a string" in e for e in errors))

    def test_kind_as_dict(self):
        data = self._valid_entity()
        data["kind"] = {"name": "task"}
        errors = validate_entity(data)
        self.assertTrue(any("kind is not a string" in e for e in errors))

    def test_status_as_list(self):
        data = self._valid_entity()
        data["status"] = ["open"]
        errors = validate_entity(data)
        self.assertTrue(any("status is not a string" in e for e in errors))

    def test_sensitivity_as_list(self):
        data = self._valid_entity()
        data["sensitivity"] = ["public"]
        errors = validate_entity(data)
        self.assertTrue(any("sensitivity is not a string" in e for e in errors))

    def test_title_as_list(self):
        data = self._valid_entity()
        data["title"] = ["Test"]
        errors = validate_entity(data)
        self.assertTrue(any("title must be non-empty string" in e for e in errors))

    def test_source_as_list(self):
        data = self._valid_entity()
        data["source"] = ["test-source"]
        errors = validate_entity(data)
        self.assertTrue(any("source must be non-empty string" in e for e in errors))

    def test_domain_as_list(self):
        data = self._valid_entity()
        data["domain"] = ["test-domain"]
        errors = validate_entity(data)
        self.assertTrue(any("domain must be non-empty string" in e for e in errors))

    def test_confidence_as_bool(self):
        data = self._valid_entity()
        data["confidence"] = True
        errors = validate_entity(data)
        self.assertTrue(any("confidence must be in [0, 1]" in e for e in errors))


class TestValidateEvent(unittest.TestCase):
    def _valid_event(self) -> dict:
        return {
            "schema": EVENT_SCHEMA,
            "id": "evt-0123456789abcdef",
            "type": "task.created",
            "occurred_at": "2026-01-01T00:00:00+00:00",
            "source": "test-source",
            "domain": "test-domain",
            "sensitivity": "public",
            "dedup_key": "test-dedup",
            "payload": {"data": "value"},
        }

    def test_valid_event(self):
        errors = validate_event(self._valid_event())
        self.assertEqual(errors, [])

    def test_not_dict(self):
        errors = validate_event("not a dict")
        self.assertEqual(len(errors), 1)
        self.assertIn("not a JSON object", errors[0])

    def test_missing_required_fields(self):
        data = self._valid_event()
        del data["type"]
        errors = validate_event(data)
        self.assertTrue(any("missing" in e and "type" in e for e in errors))

    def test_wrong_schema(self):
        data = self._valid_event()
        data["schema"] = "wrong-schema"
        errors = validate_event(data)
        self.assertTrue(any("schema must be" in e for e in errors))

    def test_invalid_id_format(self):
        data = self._valid_event()
        data["id"] = "invalid-id"
        errors = validate_event(data)
        self.assertTrue(any("invalid id" in e for e in errors))

    def test_unknown_type(self):
        data = self._valid_event()
        data["type"] = "unknown.type"
        errors = validate_event(data)
        self.assertTrue(any("unknown type" in e for e in errors))

    def test_invalid_occurred_at(self):
        data = self._valid_event()
        data["occurred_at"] = "not-a-timestamp"
        errors = validate_event(data)
        self.assertTrue(any("occurred_at" in e and "invalid" in e for e in errors))

    def test_unknown_sensitivity(self):
        data = self._valid_event()
        data["sensitivity"] = "unknown_sensitivity"
        errors = validate_event(data)
        self.assertTrue(any("unknown sensitivity" in e for e in errors))

    def test_empty_source(self):
        data = self._valid_event()
        data["source"] = ""
        errors = validate_event(data)
        self.assertTrue(any("source must be non-empty" in e for e in errors))

    def test_empty_domain(self):
        data = self._valid_event()
        data["domain"] = ""
        errors = validate_event(data)
        self.assertTrue(any("domain must be non-empty" in e for e in errors))

    def test_empty_dedup_key(self):
        data = self._valid_event()
        data["dedup_key"] = ""
        errors = validate_event(data)
        self.assertTrue(any("dedup_key must be non-empty" in e for e in errors))

    def test_invalid_payload(self):
        data = self._valid_event()
        data["payload"] = "not-an-object"
        errors = validate_event(data)
        self.assertTrue(any("payload must be a JSON object" in e for e in errors))

    def test_sensitive_without_local_only(self):
        data = self._valid_event()
        data["sensitivity"] = "sensitive"
        errors = validate_event(data)
        self.assertTrue(any("requires local_only=true" in e for e in errors))

    def test_sensitive_with_local_only(self):
        data = self._valid_event()
        data["sensitivity"] = "sensitive"
        data["local_only"] = True
        errors = validate_event(data)
        self.assertFalse(any("requires local_only=true" in e for e in errors))

    def test_type_as_list(self):
        data = self._valid_event()
        data["type"] = ["task.created"]
        errors = validate_event(data)
        self.assertTrue(any("type is not a string" in e for e in errors))

    def test_sensitivity_as_list(self):
        data = self._valid_event()
        data["sensitivity"] = ["public"]
        errors = validate_event(data)
        self.assertTrue(any("sensitivity is not a string" in e for e in errors))

    def test_source_as_list(self):
        data = self._valid_event()
        data["source"] = ["test-source"]
        errors = validate_event(data)
        self.assertTrue(any("source must be non-empty string" in e for e in errors))

    def test_domain_as_list(self):
        data = self._valid_event()
        data["domain"] = ["test-domain"]
        errors = validate_event(data)
        self.assertTrue(any("domain must be non-empty string" in e for e in errors))

    def test_dedup_key_as_list(self):
        data = self._valid_event()
        data["dedup_key"] = ["test-dedup"]
        errors = validate_event(data)
        self.assertTrue(any("dedup_key must be non-empty string" in e for e in errors))

    def test_occurred_at_null(self):
        data = self._valid_event()
        data["occurred_at"] = None
        errors = validate_event(data)
        self.assertTrue(any("occurred_at" in e and "not a string" in e for e in errors))


class TestValidateQueueItem(unittest.TestCase):
    def _valid_queue_item(self) -> dict:
        return {
            "schema": QUEUE_ITEM_SCHEMA,
            "id": "qi-0123456789abcdef",
            "entity_id": "ex-task-0123456789abcdef",
            "queued_at": "2026-01-01T00:00:00+00:00",
            "source": "test-source",
            "domain": "test-domain",
            "sensitivity": "public",
            "status": "queued",
        }

    def test_valid_queue_item(self):
        errors = validate_queue_item(self._valid_queue_item())
        self.assertEqual(errors, [])

    def test_valid_queue_item_without_status(self):
        data = self._valid_queue_item()
        del data["status"]
        errors = validate_queue_item(data)
        self.assertEqual(errors, [])

    def test_not_dict(self):
        errors = validate_queue_item("not a dict")
        self.assertEqual(len(errors), 1)
        self.assertIn("not a JSON object", errors[0])

    def test_missing_required_fields(self):
        data = self._valid_queue_item()
        del data["entity_id"]
        errors = validate_queue_item(data)
        self.assertTrue(any("missing" in e and "entity_id" in e for e in errors))

    def test_wrong_schema(self):
        data = self._valid_queue_item()
        data["schema"] = "wrong-schema"
        errors = validate_queue_item(data)
        self.assertTrue(any("schema must be" in e for e in errors))

    def test_invalid_id_format(self):
        data = self._valid_queue_item()
        data["id"] = "invalid-id"
        errors = validate_queue_item(data)
        self.assertTrue(any("invalid id" in e for e in errors))

    def test_invalid_entity_id_format(self):
        data = self._valid_queue_item()
        data["entity_id"] = "invalid-entity-id"
        errors = validate_queue_item(data)
        self.assertTrue(any("invalid entity_id" in e for e in errors))

    def test_invalid_queued_at(self):
        data = self._valid_queue_item()
        data["queued_at"] = "not-a-timestamp"
        errors = validate_queue_item(data)
        self.assertTrue(any("queued_at" in e and "invalid" in e for e in errors))

    def test_unknown_sensitivity(self):
        data = self._valid_queue_item()
        data["sensitivity"] = "unknown_sensitivity"
        errors = validate_queue_item(data)
        self.assertTrue(any("unknown sensitivity" in e for e in errors))

    def test_empty_source(self):
        data = self._valid_queue_item()
        data["source"] = ""
        errors = validate_queue_item(data)
        self.assertTrue(any("source must be non-empty" in e for e in errors))

    def test_empty_domain(self):
        data = self._valid_queue_item()
        data["domain"] = ""
        errors = validate_queue_item(data)
        self.assertTrue(any("domain must be non-empty" in e for e in errors))

    def test_invalid_priority(self):
        data = self._valid_queue_item()
        data["priority"] = -1
        errors = validate_queue_item(data)
        self.assertTrue(any("priority must be >= 0" in e for e in errors))

    def test_valid_priority(self):
        data = self._valid_queue_item()
        data["priority"] = 50
        errors = validate_queue_item(data)
        self.assertFalse(any("priority" in e for e in errors))

    def test_invalid_importance_high(self):
        data = self._valid_queue_item()
        data["importance"] = 1.5
        errors = validate_queue_item(data)
        self.assertTrue(any("importance must be in [0, 1]" in e for e in errors))

    def test_valid_importance(self):
        data = self._valid_queue_item()
        data["importance"] = 0.5
        errors = validate_queue_item(data)
        self.assertFalse(any("importance" in e for e in errors))

    def test_invalid_blocking_impact(self):
        data = self._valid_queue_item()
        data["blocking_impact"] = -0.1
        errors = validate_queue_item(data)
        self.assertTrue(any("blocking_impact must be in [0, 1]" in e for e in errors))

    def test_unknown_urgency(self):
        data = self._valid_queue_item()
        data["urgency"] = "unknown_urgency"
        errors = validate_queue_item(data)
        self.assertTrue(any("unknown urgency" in e for e in errors))

    def test_valid_urgency(self):
        data = self._valid_queue_item()
        data["urgency"] = "high"
        errors = validate_queue_item(data)
        self.assertFalse(any("urgency" in e for e in errors))

    def test_invalid_repeated_deferrals(self):
        data = self._valid_queue_item()
        data["repeated_deferrals"] = -1
        errors = validate_queue_item(data)
        self.assertTrue(any("repeated_deferrals must be >= 0" in e for e in errors))

    def test_invalid_interruption_cost(self):
        data = self._valid_queue_item()
        data["interruption_cost"] = -0.1
        errors = validate_queue_item(data)
        self.assertTrue(any("interruption_cost must be >= 0" in e for e in errors))

    def test_unknown_status(self):
        data = self._valid_queue_item()
        data["status"] = "unknown_status"
        errors = validate_queue_item(data)
        self.assertTrue(any("unknown status" in e for e in errors))

    def test_sensitive_without_local_only(self):
        data = self._valid_queue_item()
        data["sensitivity"] = "sensitive"
        errors = validate_queue_item(data)
        self.assertTrue(any("requires local_only=true" in e for e in errors))

    def test_sensitive_with_local_only(self):
        data = self._valid_queue_item()
        data["sensitivity"] = "sensitive"
        data["local_only"] = True
        errors = validate_queue_item(data)
        self.assertFalse(any("requires local_only=true" in e for e in errors))

    def test_sensitivity_as_list(self):
        data = self._valid_queue_item()
        data["sensitivity"] = ["public"]
        errors = validate_queue_item(data)
        self.assertTrue(any("sensitivity is not a string" in e for e in errors))

    def test_source_as_list(self):
        data = self._valid_queue_item()
        data["source"] = ["test-source"]
        errors = validate_queue_item(data)
        self.assertTrue(any("source must be non-empty string" in e for e in errors))

    def test_domain_as_list(self):
        data = self._valid_queue_item()
        data["domain"] = ["test-domain"]
        errors = validate_queue_item(data)
        self.assertTrue(any("domain must be non-empty string" in e for e in errors))

    def test_urgency_as_list(self):
        data = self._valid_queue_item()
        data["urgency"] = ["high"]
        errors = validate_queue_item(data)
        self.assertTrue(any("urgency is not a string" in e for e in errors))

    def test_status_as_list(self):
        data = self._valid_queue_item()
        data["status"] = ["queued"]
        errors = validate_queue_item(data)
        self.assertTrue(any("status is not a string" in e for e in errors))

    def test_importance_as_bool(self):
        data = self._valid_queue_item()
        data["importance"] = True
        errors = validate_queue_item(data)
        self.assertTrue(any("importance must be in [0, 1]" in e for e in errors))

    def test_priority_as_bool(self):
        data = self._valid_queue_item()
        data["priority"] = True
        errors = validate_queue_item(data)
        self.assertTrue(any("priority must be >= 0" in e for e in errors))

    def test_blocking_impact_as_bool(self):
        data = self._valid_queue_item()
        data["blocking_impact"] = True
        errors = validate_queue_item(data)
        self.assertTrue(any("blocking_impact must be in [0, 1]" in e for e in errors))

    def test_interruption_cost_as_bool(self):
        data = self._valid_queue_item()
        data["interruption_cost"] = True
        errors = validate_queue_item(data)
        self.assertTrue(any("interruption_cost must be >= 0" in e for e in errors))

    def test_queued_at_null(self):
        data = self._valid_queue_item()
        data["queued_at"] = None
        errors = validate_queue_item(data)
        self.assertTrue(any("queued_at" in e and "not a string" in e for e in errors))


class TestConstants(unittest.TestCase):
    def test_entity_kinds_count(self):
        self.assertEqual(len(ENTITY_KINDS), 13)

    def test_event_types_count(self):
        self.assertEqual(len(EVENT_TYPES), 21)

    def test_task_cancelled_event_type(self):
        self.assertIn("task.cancelled", EVENT_TYPES)

    def test_autonomy_levels(self):
        self.assertEqual(AUTONOMY_LEVELS, {"OBSERVE", "SUGGEST", "PREPARE", "ASK_THEN_ACT", "AUTO_ACT"})

    def test_sensitivities(self):
        self.assertEqual(SENSITIVITIES, {"public", "personal", "sensitive", "secret"})

    def test_entity_statuses(self):
        self.assertEqual(ENTITY_STATUSES, {"open", "active", "waiting", "deferred", "done", "cancelled", "superseded"})

    def test_queue_statuses(self):
        self.assertEqual(QUEUE_STATUSES, {"queued", "presented", "accepted", "rejected", "deferred", "completed", "cancelled"})


if __name__ == "__main__":
    unittest.main()
