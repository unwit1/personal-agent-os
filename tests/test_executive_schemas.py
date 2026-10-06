from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


class ExecutiveEntitySchemaTest(unittest.TestCase):
    """Test executive entity schema structure."""

    def setUp(self) -> None:
        schema_file = Path(__file__).parent.parent / "schemas" / "executive-entity-v1.schema.json"
        self.schema = json.loads(schema_file.read_text(encoding="utf-8"))

    def test_schema_const_value(self) -> None:
        """Test that schema property has the correct const value."""
        self.assertEqual(
            self.schema["properties"]["schema"]["const"],
            "personal-agent/executive-entity/v1"
        )

    def test_required_fields(self) -> None:
        """Test that all required fields are present."""
        expected_required = [
            "schema", "id", "kind", "title", "status",
            "created_at", "updated_at", "source", "domain",
            "sensitivity", "provenance"
        ]
        self.assertEqual(self.schema["required"], expected_required)

    def test_kind_enum_values(self) -> None:
        """Test that kind enum contains all expected values."""
        expected_kinds = [
            "task", "commitment", "project", "next_action", "blocker",
            "waiting_on", "decision_request", "question", "idea",
            "appointment", "communication", "attention_state", "outcome"
        ]
        self.assertEqual(self.schema["properties"]["kind"]["enum"], expected_kinds)

    def test_status_enum_values(self) -> None:
        """Test that status enum contains all expected values."""
        expected_statuses = ["open", "active", "waiting", "deferred", "done", "cancelled", "superseded"]
        self.assertEqual(self.schema["properties"]["status"]["enum"], expected_statuses)

    def test_sensitivity_enum_values(self) -> None:
        """Test that sensitivity enum contains all expected values."""
        expected_sensitivities = ["public", "personal", "sensitive", "secret"]
        self.assertEqual(self.schema["properties"]["sensitivity"]["enum"], expected_sensitivities)

    def test_id_pattern_valid_samples(self) -> None:
        """Test that id pattern matches valid entity IDs."""
        pattern = self.schema["properties"]["id"]["pattern"]
        valid_ids = [
            "ex-task-0123456789abcdef",
            "ex-project-fedcba9876543210",
            "ex-next_action-aaaaaaaaaaaaaaaa",
            "ex-decision_request-0000000000000000",
        ]
        for valid_id in valid_ids:
            self.assertIsNotNone(
                re.fullmatch(pattern, valid_id),
                f"Pattern should match valid id: {valid_id}"
            )

    def test_id_pattern_invalid_samples(self) -> None:
        """Test that id pattern rejects invalid entity IDs."""
        pattern = self.schema["properties"]["id"]["pattern"]
        invalid_ids = [
            "task-0123456789abcdef",  # Missing 'ex-' prefix
            "ex-task-0123456789abcdefg",  # Too many hex chars
            "ex-task-0123456789abcde",  # Too few hex chars
            "ex-TASK-0123456789abcdef",  # Invalid uppercase
            "ex-task--0123456789abcdef",  # Double dash
            "ex-0123456789abcdef",  # Missing type part
        ]
        for invalid_id in invalid_ids:
            self.assertIsNone(
                re.fullmatch(pattern, invalid_id),
                f"Pattern should reject invalid id: {invalid_id}"
            )

    def test_additional_properties_allowed(self) -> None:
        """Test that additionalProperties is True."""
        self.assertTrue(self.schema["additionalProperties"])

    def test_provenance_min_items(self) -> None:
        """Test that provenance array has minItems constraint."""
        self.assertEqual(self.schema["properties"]["provenance"]["minItems"], 1)


class ExecutiveEventSchemaTest(unittest.TestCase):
    """Test executive event schema structure."""

    def setUp(self) -> None:
        schema_file = Path(__file__).parent.parent / "schemas" / "executive-event-v1.schema.json"
        self.schema = json.loads(schema_file.read_text(encoding="utf-8"))

    def test_schema_const_value(self) -> None:
        """Test that schema property has the correct const value."""
        self.assertEqual(
            self.schema["properties"]["schema"]["const"],
            "personal-agent/executive-event/v1"
        )

    def test_required_fields(self) -> None:
        """Test that all required fields are present."""
        expected_required = [
            "schema", "id", "type", "occurred_at", "source",
            "domain", "sensitivity", "dedup_key", "payload"
        ]
        self.assertEqual(self.schema["required"], expected_required)

    def test_type_enum_values(self) -> None:
        """Test that type enum contains exactly the expected event types."""
        expected_types = [
            "conversation.completed", "idea.captured", "task.created",
            "task.completed", "task.cancelled", "task.deferred", "project.modified",
            "project.stalled", "decision.required", "decision.made",
            "agent.blocked", "agent.completed", "appointment.created",
            "appointment.approaching", "communication.received",
            "communication.needs_response", "preference.observed",
            "skill.used", "skill.failed", "outcome.recorded",
            "context.changed"
        ]
        self.assertEqual(sorted(self.schema["properties"]["type"]["enum"]), sorted(expected_types))

    def test_sensitivity_enum_values(self) -> None:
        """Test that sensitivity enum contains all expected values."""
        expected_sensitivities = ["public", "personal", "sensitive", "secret"]
        self.assertEqual(self.schema["properties"]["sensitivity"]["enum"], expected_sensitivities)

    def test_id_pattern_valid_samples(self) -> None:
        """Test that id pattern matches valid event IDs."""
        pattern = self.schema["properties"]["id"]["pattern"]
        valid_ids = [
            "evt-0123456789abcdef",
            "evt-fedcba9876543210",
            "evt-aaaaaaaaaaaaaaaa",
            "evt-0000000000000000",
        ]
        for valid_id in valid_ids:
            self.assertIsNotNone(
                re.fullmatch(pattern, valid_id),
                f"Pattern should match valid id: {valid_id}"
            )

    def test_id_pattern_invalid_samples(self) -> None:
        """Test that id pattern rejects invalid event IDs."""
        pattern = self.schema["properties"]["id"]["pattern"]
        invalid_ids = [
            "0123456789abcdef",  # Missing 'evt-' prefix
            "evt-0123456789abcdefg",  # Too many hex chars
            "evt-0123456789abcde",  # Too few hex chars
            "evt-0123456789ABCDEF",  # Invalid uppercase
            "event-0123456789abcdef",  # Wrong prefix
        ]
        for invalid_id in invalid_ids:
            self.assertIsNone(
                re.fullmatch(pattern, invalid_id),
                f"Pattern should reject invalid id: {invalid_id}"
            )

    def test_additional_properties_allowed(self) -> None:
        """Test that additionalProperties is True."""
        self.assertTrue(self.schema["additionalProperties"])


class ExecutiveQueueItemSchemaTest(unittest.TestCase):
    """Test executive queue item schema structure."""

    def setUp(self) -> None:
        schema_file = Path(__file__).parent.parent / "schemas" / "executive-queue-item-v1.schema.json"
        self.schema = json.loads(schema_file.read_text(encoding="utf-8"))

    def test_schema_const_value(self) -> None:
        """Test that schema property has the correct const value."""
        self.assertEqual(
            self.schema["properties"]["schema"]["const"],
            "personal-agent/executive-queue-item/v1"
        )

    def test_required_fields(self) -> None:
        """Test that all required fields are present."""
        expected_required = [
            "schema", "id", "entity_id", "queued_at", "source",
            "domain", "sensitivity"
        ]
        self.assertEqual(self.schema["required"], expected_required)

    def test_sensitivity_enum_values(self) -> None:
        """Test that sensitivity enum contains all expected values."""
        expected_sensitivities = ["public", "personal", "sensitive", "secret"]
        self.assertEqual(self.schema["properties"]["sensitivity"]["enum"], expected_sensitivities)

    def test_id_pattern_valid_samples(self) -> None:
        """Test that id pattern matches valid queue item IDs."""
        pattern = self.schema["properties"]["id"]["pattern"]
        valid_ids = [
            "qi-0123456789abcdef",
            "qi-fedcba9876543210",
            "qi-aaaaaaaaaaaaaaaa",
            "qi-0000000000000000",
        ]
        for valid_id in valid_ids:
            self.assertIsNotNone(
                re.fullmatch(pattern, valid_id),
                f"Pattern should match valid id: {valid_id}"
            )

    def test_id_pattern_invalid_samples(self) -> None:
        """Test that id pattern rejects invalid queue item IDs."""
        pattern = self.schema["properties"]["id"]["pattern"]
        invalid_ids = [
            "0123456789abcdef",  # Missing 'qi-' prefix
            "qi-0123456789abcdefg",  # Too many hex chars
            "qi-0123456789abcde",  # Too few hex chars
            "qi-0123456789ABCDEF",  # Invalid uppercase
            "queue-0123456789abcdef",  # Wrong prefix
        ]
        for invalid_id in invalid_ids:
            self.assertIsNone(
                re.fullmatch(pattern, invalid_id),
                f"Pattern should reject invalid id: {invalid_id}"
            )

    def test_entity_id_pattern_valid_samples(self) -> None:
        """Test that entity_id pattern matches valid entity IDs."""
        pattern = self.schema["properties"]["entity_id"]["pattern"]
        valid_ids = [
            "ex-task-0123456789abcdef",
            "ex-project-fedcba9876543210",
            "ex-next_action-aaaaaaaaaaaaaaaa",
            "ex-decision_request-0000000000000000",
        ]
        for valid_id in valid_ids:
            self.assertIsNotNone(
                re.fullmatch(pattern, valid_id),
                f"Pattern should match valid entity_id: {valid_id}"
            )

    def test_entity_id_pattern_invalid_samples(self) -> None:
        """Test that entity_id pattern rejects invalid entity IDs."""
        pattern = self.schema["properties"]["entity_id"]["pattern"]
        invalid_ids = [
            "task-0123456789abcdef",  # Missing 'ex-' prefix
            "ex-TASK-0123456789abcdef",  # Invalid uppercase in type
            "ex-task-0123456789abcdefg",  # Too many hex chars
            "ex-task-0123456789abcde",  # Too few hex chars
        ]
        for invalid_id in invalid_ids:
            self.assertIsNone(
                re.fullmatch(pattern, invalid_id),
                f"Pattern should reject invalid entity_id: {invalid_id}"
            )

    def test_additional_properties_allowed(self) -> None:
        """Test that additionalProperties is True."""
        self.assertTrue(self.schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
