from __future__ import annotations

import json
import unittest
from pathlib import Path


class ExecutiveSchemasExistTest(unittest.TestCase):
    """Test that required executive schemas exist and are valid JSON."""

    def setUp(self) -> None:
        self.schemas_dir = Path(__file__).parent.parent / "schemas"

    def test_executive_entity_schema_exists_and_is_valid_json(self) -> None:
        schema_file = self.schemas_dir / "executive-entity-v1.schema.json"
        self.assertTrue(schema_file.exists(), f"Schema file not found: {schema_file}")
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["title"], "Agent OS Executive Entity")

    def test_executive_event_schema_exists_and_is_valid_json(self) -> None:
        schema_file = self.schemas_dir / "executive-event-v1.schema.json"
        self.assertTrue(schema_file.exists(), f"Schema file not found: {schema_file}")
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["title"], "Agent OS Executive Event")

    def test_executive_queue_item_schema_exists_and_is_valid_json(self) -> None:
        schema_file = self.schemas_dir / "executive-queue-item-v1.schema.json"
        self.assertTrue(schema_file.exists(), f"Schema file not found: {schema_file}")
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["title"], "Agent OS Executive Queue Item")


class ExecutiveEntityValidTest(unittest.TestCase):
    """Test executive entity schema structure and required fields."""

    def setUp(self) -> None:
        schema_file = Path(__file__).parent.parent / "schemas" / "executive-entity-v1.schema.json"
        self.schema = json.loads(schema_file.read_text(encoding="utf-8"))

    def test_required_fields_are_present(self) -> None:
        required = self.schema["required"]
        expected_required = ["schema", "id", "kind", "title", "status", "created_at", "updated_at", "source", "domain", "sensitivity", "provenance"]
        self.assertEqual(set(required), set(expected_required))

    def test_schema_constant_is_correct(self) -> None:
        schema_prop = self.schema["properties"]["schema"]
        self.assertEqual(schema_prop["const"], "personal-agent/executive-entity/v1")

    def test_id_pattern_is_defined(self) -> None:
        id_prop = self.schema["properties"]["id"]
        self.assertIn("pattern", id_prop)
        self.assertEqual(id_prop["pattern"], "^ex-[a-z_]+-[0-9a-f]{16}$")

    def test_kind_enum_values(self) -> None:
        kind_prop = self.schema["properties"]["kind"]
        expected_kinds = {"task", "commitment", "project", "next_action", "blocker", "waiting_on", "decision_request", "question", "idea", "appointment", "communication", "attention_state", "outcome"}
        self.assertEqual(set(kind_prop["enum"]), expected_kinds)

    def test_status_enum_values(self) -> None:
        status_prop = self.schema["properties"]["status"]
        expected_statuses = {"open", "active", "waiting", "deferred", "done", "cancelled", "superseded"}
        self.assertEqual(set(status_prop["enum"]), expected_statuses)

    def test_sensitivity_enum_values(self) -> None:
        sensitivity_prop = self.schema["properties"]["sensitivity"]
        expected_sensitivities = {"public", "personal", "sensitive", "secret"}
        self.assertEqual(set(sensitivity_prop["enum"]), expected_sensitivities)

    def test_title_has_minlength(self) -> None:
        title_prop = self.schema["properties"]["title"]
        self.assertEqual(title_prop["minLength"], 1)

    def test_provenance_is_array_with_minlength(self) -> None:
        prov_prop = self.schema["properties"]["provenance"]
        self.assertEqual(prov_prop["type"], "array")
        self.assertEqual(prov_prop["minItems"], 1)

    def test_confidence_is_number_between_0_and_1(self) -> None:
        conf_prop = self.schema["properties"]["confidence"]
        self.assertIn("number", conf_prop["type"])
        self.assertEqual(conf_prop["minimum"], 0)
        self.assertEqual(conf_prop["maximum"], 1)


class ExecutiveEventValidTest(unittest.TestCase):
    """Test executive event schema structure and required fields."""

    def setUp(self) -> None:
        schema_file = Path(__file__).parent.parent / "schemas" / "executive-event-v1.schema.json"
        self.schema = json.loads(schema_file.read_text(encoding="utf-8"))

    def test_required_fields_are_present(self) -> None:
        required = self.schema["required"]
        expected_required = ["schema", "id", "type", "occurred_at", "source", "domain", "sensitivity", "dedup_key", "payload"]
        self.assertEqual(set(required), set(expected_required))

    def test_schema_constant_is_correct(self) -> None:
        schema_prop = self.schema["properties"]["schema"]
        self.assertEqual(schema_prop["const"], "personal-agent/executive-event/v1")

    def test_id_pattern_is_defined(self) -> None:
        id_prop = self.schema["properties"]["id"]
        self.assertIn("pattern", id_prop)
        self.assertEqual(id_prop["pattern"], "^evt-[0-9a-f]{16}$")

    def test_event_type_enum_values(self) -> None:
        type_prop = self.schema["properties"]["type"]
        expected_types = {
            "conversation.completed", "idea.captured", "task.created", "task.completed", "task.deferred",
            "project.modified", "project.stalled", "decision.required", "decision.made", "agent.blocked",
            "agent.completed", "appointment.created", "appointment.approaching", "communication.received",
            "communication.needs_response", "preference.observed", "skill.used", "skill.failed", "outcome.recorded",
            "context.changed"
        }
        self.assertEqual(set(type_prop["enum"]), expected_types)

    def test_sensitivity_enum_values(self) -> None:
        sensitivity_prop = self.schema["properties"]["sensitivity"]
        expected_sensitivities = {"public", "personal", "sensitive", "secret"}
        self.assertEqual(set(sensitivity_prop["enum"]), expected_sensitivities)

    def test_payload_is_object(self) -> None:
        payload_prop = self.schema["properties"]["payload"]
        self.assertEqual(payload_prop["type"], "object")


class ExecutiveQueueItemValidTest(unittest.TestCase):
    """Test executive queue item schema structure and required fields."""

    def setUp(self) -> None:
        schema_file = Path(__file__).parent.parent / "schemas" / "executive-queue-item-v1.schema.json"
        self.schema = json.loads(schema_file.read_text(encoding="utf-8"))

    def test_required_fields_are_present(self) -> None:
        required = self.schema["required"]
        expected_required = ["schema", "id", "entity_id", "queued_at", "source", "domain", "sensitivity"]
        self.assertEqual(set(required), set(expected_required))

    def test_schema_constant_is_correct(self) -> None:
        schema_prop = self.schema["properties"]["schema"]
        self.assertEqual(schema_prop["const"], "personal-agent/executive-queue-item/v1")

    def test_id_pattern_is_defined(self) -> None:
        id_prop = self.schema["properties"]["id"]
        self.assertIn("pattern", id_prop)
        self.assertEqual(id_prop["pattern"], "^qi-[0-9a-f]{16}$")

    def test_entity_id_pattern_matches_executive_entity(self) -> None:
        entity_id_prop = self.schema["properties"]["entity_id"]
        self.assertEqual(entity_id_prop["pattern"], "^ex-[a-z_]+-[0-9a-f]{16}$")

    def test_sensitivity_enum_values(self) -> None:
        sensitivity_prop = self.schema["properties"]["sensitivity"]
        expected_sensitivities = {"public", "personal", "sensitive", "secret"}
        self.assertEqual(set(sensitivity_prop["enum"]), expected_sensitivities)

    def test_urgency_enum_values(self) -> None:
        urgency_prop = self.schema["properties"]["urgency"]
        expected_urgencies = {"critical", "high", "normal", "low", None}
        self.assertEqual(set(urgency_prop["enum"]), expected_urgencies)

    def test_status_enum_values(self) -> None:
        status_prop = self.schema["properties"]["status"]
        expected_statuses = {"queued", "presented", "accepted", "rejected", "deferred", "completed", "cancelled"}
        self.assertEqual(set(status_prop["enum"]), expected_statuses)

    def test_confidence_fields_are_numeric(self) -> None:
        importance_prop = self.schema["properties"]["importance"]
        self.assertIn("number", importance_prop["type"])
        self.assertEqual(importance_prop["minimum"], 0)
        self.assertEqual(importance_prop["maximum"], 1)

        blocking_impact_prop = self.schema["properties"]["blocking_impact"]
        self.assertIn("number", blocking_impact_prop["type"])
        self.assertEqual(blocking_impact_prop["minimum"], 0)
        self.assertEqual(blocking_impact_prop["maximum"], 1)

    def test_repeated_deferrals_is_non_negative_integer(self) -> None:
        deferrals_prop = self.schema["properties"]["repeated_deferrals"]
        self.assertIn("integer", deferrals_prop["type"])
        self.assertEqual(deferrals_prop["minimum"], 0)


if __name__ == "__main__":
    unittest.main()
