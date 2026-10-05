from __future__ import annotations

import json
import unittest
from pathlib import Path

try:
    import jsonschema
except ImportError:
    jsonschema = None


class ExecutiveEntityValidTest(unittest.TestCase):
    """Test executive entity schema with valid and invalid instances."""

    def setUp(self) -> None:
        schema_file = Path(__file__).parent.parent / "schemas" / "executive-entity-v1.schema.json"
        self.schema = json.loads(schema_file.read_text(encoding="utf-8"))

    def test_minimal_valid_entity_passes(self) -> None:
        if jsonschema is None:
            self.skipTest("jsonschema not available")
        valid_entity = {
            "schema": "personal-agent/executive-entity/v1",
            "id": "ex-task-0123456789abcdef",
            "kind": "task",
            "title": "Do something",
            "status": "open",
            "created_at": "2026-10-05T00:00:00Z",
            "updated_at": "2026-10-05T00:00:00Z",
            "source": "user",
            "domain": "work",
            "sensitivity": "personal",
            "provenance": ["user-input"]
        }
        try:
            jsonschema.validate(valid_entity, self.schema)
        except jsonschema.ValidationError as e:
            self.fail(f"Minimal valid entity failed validation: {e}")

    def test_entity_missing_required_field_fails(self) -> None:
        if jsonschema is None:
            self.skipTest("jsonschema not available")
        invalid_entity = {
            "schema": "personal-agent/executive-entity/v1",
            "id": "ex-task-0123456789abcdef",
            "kind": "task",
            "title": "Do something",
            "status": "open",
            "created_at": "2026-10-05T00:00:00Z",
            "updated_at": "2026-10-05T00:00:00Z",
            "source": "user"
            # Missing: domain, sensitivity, provenance
        }
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(invalid_entity, self.schema)

    def test_entity_bad_enum_fails(self) -> None:
        if jsonschema is None:
            self.skipTest("jsonschema not available")
        invalid_entity = {
            "schema": "personal-agent/executive-entity/v1",
            "id": "ex-task-0123456789abcdef",
            "kind": "invalid_kind",
            "title": "Do something",
            "status": "open",
            "created_at": "2026-10-05T00:00:00Z",
            "updated_at": "2026-10-05T00:00:00Z",
            "source": "user",
            "domain": "work",
            "sensitivity": "personal",
            "provenance": ["user-input"]
        }
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(invalid_entity, self.schema)

    def test_entity_with_additional_properties_passes(self) -> None:
        if jsonschema is None:
            self.skipTest("jsonschema not available")
        valid_entity = {
            "schema": "personal-agent/executive-entity/v1",
            "id": "ex-task-0123456789abcdef",
            "kind": "task",
            "title": "Do something",
            "status": "open",
            "created_at": "2026-10-05T00:00:00Z",
            "updated_at": "2026-10-05T00:00:00Z",
            "source": "user",
            "domain": "work",
            "sensitivity": "personal",
            "provenance": ["user-input"],
            "custom_field": "custom_value"
        }
        try:
            jsonschema.validate(valid_entity, self.schema)
        except jsonschema.ValidationError as e:
            self.fail(f"Entity with additional properties failed validation: {e}")


class ExecutiveEventValidTest(unittest.TestCase):
    """Test executive event schema with valid and invalid instances."""

    def setUp(self) -> None:
        schema_file = Path(__file__).parent.parent / "schemas" / "executive-event-v1.schema.json"
        self.schema = json.loads(schema_file.read_text(encoding="utf-8"))

    def test_minimal_valid_event_passes(self) -> None:
        if jsonschema is None:
            self.skipTest("jsonschema not available")
        valid_event = {
            "schema": "personal-agent/executive-event/v1",
            "id": "evt-0123456789abcdef",
            "type": "task.created",
            "occurred_at": "2026-10-05T00:00:00Z",
            "source": "user",
            "domain": "work",
            "sensitivity": "personal",
            "dedup_key": "task-123",
            "payload": {}
        }
        try:
            jsonschema.validate(valid_event, self.schema)
        except jsonschema.ValidationError as e:
            self.fail(f"Minimal valid event failed validation: {e}")

    def test_event_missing_required_field_fails(self) -> None:
        if jsonschema is None:
            self.skipTest("jsonschema not available")
        invalid_event = {
            "schema": "personal-agent/executive-event/v1",
            "id": "evt-0123456789abcdef",
            "type": "task.created",
            "occurred_at": "2026-10-05T00:00:00Z",
            "source": "user",
            # Missing: domain, sensitivity, dedup_key, payload
        }
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(invalid_event, self.schema)

    def test_event_bad_enum_fails(self) -> None:
        if jsonschema is None:
            self.skipTest("jsonschema not available")
        invalid_event = {
            "schema": "personal-agent/executive-event/v1",
            "id": "evt-0123456789abcdef",
            "type": "invalid.event.type",
            "occurred_at": "2026-10-05T00:00:00Z",
            "source": "user",
            "domain": "work",
            "sensitivity": "personal",
            "dedup_key": "task-123",
            "payload": {}
        }
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(invalid_event, self.schema)

    def test_event_with_additional_properties_passes(self) -> None:
        if jsonschema is None:
            self.skipTest("jsonschema not available")
        valid_event = {
            "schema": "personal-agent/executive-event/v1",
            "id": "evt-0123456789abcdef",
            "type": "task.created",
            "occurred_at": "2026-10-05T00:00:00Z",
            "source": "user",
            "domain": "work",
            "sensitivity": "personal",
            "dedup_key": "task-123",
            "payload": {},
            "custom_metadata": "some_value"
        }
        try:
            jsonschema.validate(valid_event, self.schema)
        except jsonschema.ValidationError as e:
            self.fail(f"Event with additional properties failed validation: {e}")


class ExecutiveQueueItemValidTest(unittest.TestCase):
    """Test executive queue item schema with valid and invalid instances."""

    def setUp(self) -> None:
        schema_file = Path(__file__).parent.parent / "schemas" / "executive-queue-item-v1.schema.json"
        self.schema = json.loads(schema_file.read_text(encoding="utf-8"))

    def test_minimal_valid_queue_item_passes(self) -> None:
        if jsonschema is None:
            self.skipTest("jsonschema not available")
        valid_queue_item = {
            "schema": "personal-agent/executive-queue-item/v1",
            "id": "qi-0123456789abcdef",
            "entity_id": "ex-task-0123456789abcdef",
            "queued_at": "2026-10-05T00:00:00Z",
            "source": "user",
            "domain": "work",
            "sensitivity": "personal"
        }
        try:
            jsonschema.validate(valid_queue_item, self.schema)
        except jsonschema.ValidationError as e:
            self.fail(f"Minimal valid queue item failed validation: {e}")

    def test_queue_item_missing_required_field_fails(self) -> None:
        if jsonschema is None:
            self.skipTest("jsonschema not available")
        invalid_queue_item = {
            "schema": "personal-agent/executive-queue-item/v1",
            "id": "qi-0123456789abcdef",
            "entity_id": "ex-task-0123456789abcdef",
            "queued_at": "2026-10-05T00:00:00Z",
            "source": "user"
            # Missing: domain, sensitivity
        }
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(invalid_queue_item, self.schema)

    def test_queue_item_bad_enum_fails(self) -> None:
        if jsonschema is None:
            self.skipTest("jsonschema not available")
        invalid_queue_item = {
            "schema": "personal-agent/executive-queue-item/v1",
            "id": "qi-0123456789abcdef",
            "entity_id": "ex-task-0123456789abcdef",
            "queued_at": "2026-10-05T00:00:00Z",
            "source": "user",
            "domain": "work",
            "sensitivity": "invalid_sensitivity"
        }
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(invalid_queue_item, self.schema)

    def test_queue_item_with_additional_properties_passes(self) -> None:
        if jsonschema is None:
            self.skipTest("jsonschema not available")
        valid_queue_item = {
            "schema": "personal-agent/executive-queue-item/v1",
            "id": "qi-0123456789abcdef",
            "entity_id": "ex-task-0123456789abcdef",
            "queued_at": "2026-10-05T00:00:00Z",
            "source": "user",
            "domain": "work",
            "sensitivity": "personal",
            "extra_field": "extra_value"
        }
        try:
            jsonschema.validate(valid_queue_item, self.schema)
        except jsonschema.ValidationError as e:
            self.fail(f"Queue item with additional properties failed validation: {e}")


if __name__ == "__main__":
    unittest.main()
