import json
import unittest
from pathlib import Path


class TestProjectStateSchemaExec1(unittest.TestCase):
    def setUp(self):
        schema_path = Path(__file__).parent.parent / "schemas" / "project-state.schema.json"
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

    def test_new_properties_exist_in_schema(self):
        """Verify each new property exists in the schema with the stated type."""
        properties = self.schema.get("properties", {})

        # String properties
        string_props = ["goal", "current_state", "next_action", "updated_at"]
        for prop in string_props:
            self.assertIn(prop, properties, f"Property '{prop}' not found in schema")
            self.assertEqual(
                properties[prop].get("type"),
                "string",
                f"Property '{prop}' should have type 'string'",
            )

        # Array of string properties
        array_props = [
            "current_priorities",
            "blockers",
            "waiting_on",
            "decisions_needed",
            "delegable_work",
        ]
        for prop in array_props:
            self.assertIn(prop, properties, f"Property '{prop}' not found in schema")
            self.assertEqual(
                properties[prop].get("type"),
                "array",
                f"Property '{prop}' should have type 'array'",
            )
            self.assertEqual(
                properties[prop].get("items", {}).get("type"),
                "string",
                f"Property '{prop}' items should have type 'string'",
            )

    def test_required_fields_unchanged(self):
        """Verify 'required' contains exactly the expected fields."""
        expected_required = [
            "schema_version",
            "project",
            "status",
            "summary",
            "context_files",
            "validation_commands",
        ]
        self.assertEqual(
            self.schema.get("required", []),
            expected_required,
            "Required fields should not include the new optional properties",
        )

    def test_additional_properties_true(self):
        """Verify additionalProperties is still true."""
        self.assertTrue(
            self.schema.get("additionalProperties", False),
            "additionalProperties should be true",
        )

    def test_project_state_files_valid_types(self):
        """Load all projects/*/state.json and verify new keys have correct types."""
        projects_dir = Path(__file__).parent.parent / "projects"
        state_files = list(projects_dir.glob("*/state.json"))

        self.assertGreater(
            len(state_files), 0, "No project state files found in projects/ directory"
        )

        for state_file in state_files:
            with self.subTest(state_file=state_file.relative_to(projects_dir.parent)):
                with open(state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)

                # Check string properties
                for key in ["goal", "current_state", "next_action", "updated_at"]:
                    if key in state:
                        self.assertIsInstance(
                            state[key],
                            str,
                            f"Key '{key}' in {state_file.name} should be a string",
                        )

                # Check array of string properties
                for key in [
                    "current_priorities",
                    "blockers",
                    "waiting_on",
                    "decisions_needed",
                    "delegable_work",
                ]:
                    if key in state:
                        self.assertIsInstance(
                            state[key],
                            list,
                            f"Key '{key}' in {state_file.name} should be a list",
                        )
                        for item in state[key]:
                            self.assertIsInstance(
                                item,
                                str,
                                f"Items in '{key}' in {state_file.name} should be strings",
                            )


if __name__ == "__main__":
    unittest.main()
