from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.cli import main  # noqa: E402
from agent_os.telemetry import LocalTelemetryStore, TelemetryEvent  # noqa: E402


class TelemetryRecordCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store_path = Path(self.tmp.name) / "events.jsonl"

    def _run(self, *args: str) -> tuple[int, dict]:
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                code = main(list(args))
        except SystemExit as e:
            # argparse calls sys.exit() on parse errors
            code = e.code or 2
        try:
            result = json.loads(output.getvalue())
        except json.JSONDecodeError:
            result = None
        return code, result

    def test_basic_record_with_required_args(self) -> None:
        code, result = self._run(
            "telemetry-record",
            "--path", str(self.store_path),
            "--project", "test-project",
            "--category", "workflow-stage"
        )
        self.assertEqual(code, 0)
        self.assertEqual(result["project_id"], "test-project")
        self.assertEqual(result["task_category"], "workflow-stage")
        self.assertIn("event_id", result)
        self.assertIn("occurred_at", result)

        # Verify event was recorded
        store = LocalTelemetryStore(self.store_path)
        events = store.read_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].project_id, "test-project")

    def test_record_with_all_token_flags(self) -> None:
        code, result = self._run(
            "telemetry-record",
            "--path", str(self.store_path),
            "--project", "test-project",
            "--category", "workflow-stage",
            "--input-tokens", "100",
            "--cached-tokens", "50",
            "--reasoning-tokens", "25",
            "--output-tokens", "75"
        )
        self.assertEqual(code, 0)
        self.assertEqual(result["input_tokens"], 100)
        self.assertEqual(result["cached_tokens"], 50)
        self.assertEqual(result["reasoning_tokens"], 25)
        self.assertEqual(result["output_tokens"], 75)

        store = LocalTelemetryStore(self.store_path)
        events = store.read_events()
        self.assertEqual(events[0].input_tokens, 100)

    def test_record_with_provider_and_model(self) -> None:
        code, result = self._run(
            "telemetry-record",
            "--path", str(self.store_path),
            "--project", "test-project",
            "--category", "workflow-stage",
            "--provider", "openai",
            "--model", "gpt-4o"
        )
        self.assertEqual(code, 0)
        self.assertEqual(result["provider"], "openai")
        self.assertEqual(result["model"], "gpt-4o")

    def test_record_with_capability_and_execution_path(self) -> None:
        code, result = self._run(
            "telemetry-record",
            "--path", str(self.store_path),
            "--project", "test-project",
            "--category", "workflow-stage",
            "--capability", "deterministic",
            "--execution-path", "cache"
        )
        self.assertEqual(code, 0)
        self.assertEqual(result["capability_class"], "deterministic")
        self.assertEqual(result["execution_path"], "cache")

    def test_record_with_duration_items_retries_escalations(self) -> None:
        code, result = self._run(
            "telemetry-record",
            "--path", str(self.store_path),
            "--project", "test-project",
            "--category", "workflow-stage",
            "--duration-ms", "1000",
            "--items-processed", "42",
            "--retries", "3",
            "--escalations", "1"
        )
        self.assertEqual(code, 0)
        self.assertEqual(result["duration_ms"], 1000)
        self.assertEqual(result["items_processed"], 42)
        self.assertEqual(result["retries"], 3)
        self.assertEqual(result["escalations"], 1)

    def test_record_with_validator_passed(self) -> None:
        code, result = self._run(
            "telemetry-record",
            "--path", str(self.store_path),
            "--project", "test-project",
            "--category", "workflow-stage",
            "--validator-passed"
        )
        self.assertEqual(code, 0)
        self.assertIs(result["validator_passed"], True)

    def test_record_with_validator_failed(self) -> None:
        code, result = self._run(
            "telemetry-record",
            "--path", str(self.store_path),
            "--project", "test-project",
            "--category", "workflow-stage",
            "--validator-failed"
        )
        self.assertEqual(code, 0)
        self.assertIs(result["validator_passed"], False)

    def test_record_with_override(self) -> None:
        code, result = self._run(
            "telemetry-record",
            "--path", str(self.store_path),
            "--project", "test-project",
            "--category", "workflow-stage",
            "--override"
        )
        self.assertEqual(code, 0)
        self.assertIs(result["correction_or_override"], True)

    def test_record_without_override_flag(self) -> None:
        code, result = self._run(
            "telemetry-record",
            "--path", str(self.store_path),
            "--project", "test-project",
            "--category", "workflow-stage"
        )
        self.assertEqual(code, 0)
        # When not provided, the field should not be in the dict
        self.assertNotIn("correction_or_override", result)

    def test_validator_passed_and_failed_mutually_exclusive(self) -> None:
        code, result = self._run(
            "telemetry-record",
            "--path", str(self.store_path),
            "--project", "test-project",
            "--category", "workflow-stage",
            "--validator-passed",
            "--validator-failed"
        )
        self.assertNotEqual(code, 0)

    def test_usage_file_with_format_anthropic(self) -> None:
        usage_file = Path(self.tmp.name) / "usage.json"
        usage_file.write_text(json.dumps({
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_read_input_tokens": 20,
        }))

        code, result = self._run(
            "telemetry-record",
            "--path", str(self.store_path),
            "--project", "test-project",
            "--category", "workflow-stage",
            "--usage-file", str(usage_file),
            "--usage-format", "anthropic"
        )
        self.assertEqual(code, 0)
        # anthropic format: input = base + cache_read + cache_creation
        # So input_tokens = 100 + 20 + 0 = 120
        self.assertEqual(result["input_tokens"], 120)
        self.assertEqual(result["output_tokens"], 50)
        self.assertEqual(result["cached_tokens"], 20)

    def test_usage_file_with_format_openai_chat(self) -> None:
        usage_file = Path(self.tmp.name) / "usage.json"
        usage_file.write_text(json.dumps({
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "prompt_tokens_details": {
                "cached_tokens": 20
            },
            "completion_tokens_details": {
                "reasoning_tokens": 10
            }
        }))

        code, result = self._run(
            "telemetry-record",
            "--path", str(self.store_path),
            "--project", "test-project",
            "--category", "workflow-stage",
            "--usage-file", str(usage_file),
            "--usage-format", "openai-chat"
        )
        self.assertEqual(code, 0)
        self.assertEqual(result["input_tokens"], 100)
        self.assertEqual(result["cached_tokens"], 20)
        self.assertEqual(result["output_tokens"], 50)
        self.assertEqual(result["reasoning_tokens"], 10)

    def test_usage_file_without_format_fails(self) -> None:
        usage_file = Path(self.tmp.name) / "usage.json"
        usage_file.write_text(json.dumps({"input_tokens": 100}))

        code, result = self._run(
            "telemetry-record",
            "--path", str(self.store_path),
            "--project", "test-project",
            "--category", "workflow-stage",
            "--usage-file", str(usage_file)
        )
        self.assertNotEqual(code, 0)
        self.assertIn("must be provided together", str(result.get("error", "")))

    def test_format_without_usage_file_fails(self) -> None:
        code, result = self._run(
            "telemetry-record",
            "--path", str(self.store_path),
            "--project", "test-project",
            "--category", "workflow-stage",
            "--usage-format", "anthropic"
        )
        self.assertNotEqual(code, 0)
        self.assertIn("must be provided together", str(result.get("error", "")))

    def test_usage_file_and_explicit_tokens_fails(self) -> None:
        usage_file = Path(self.tmp.name) / "usage.json"
        usage_file.write_text(json.dumps({"input_tokens": 100}))

        code, result = self._run(
            "telemetry-record",
            "--path", str(self.store_path),
            "--project", "test-project",
            "--category", "workflow-stage",
            "--usage-file", str(usage_file),
            "--usage-format", "anthropic",
            "--input-tokens", "50"
        )
        self.assertNotEqual(code, 0)
        self.assertIn("either", str(result.get("error", "")))

    def test_uses_default_path_when_path_not_specified(self) -> None:
        # Record to default location (will be under .agent-local)
        code, result = self._run(
            "telemetry-record",
            "--project", "test-project",
            "--category", "workflow-stage"
        )
        self.assertEqual(code, 0)
        self.assertEqual(result["project_id"], "test-project")

    def test_multiple_records_to_same_store(self) -> None:
        for i in range(3):
            code, result = self._run(
                "telemetry-record",
                "--path", str(self.store_path),
                "--project", f"project-{i}",
                "--category", "workflow-stage"
            )
            self.assertEqual(code, 0)

        store = LocalTelemetryStore(self.store_path)
        events = store.read_events()
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0].project_id, "project-0")
        self.assertEqual(events[1].project_id, "project-1")
        self.assertEqual(events[2].project_id, "project-2")

    def test_record_with_empty_optional_fields_leaves_unknown(self) -> None:
        code, result = self._run(
            "telemetry-record",
            "--path", str(self.store_path),
            "--project", "test-project",
            "--category", "workflow-stage"
        )
        self.assertEqual(code, 0)
        # Optional fields that were not provided should not be in the output
        self.assertNotIn("capability_class", result)
        self.assertNotIn("execution_path", result)
        self.assertNotIn("provider", result)
        self.assertNotIn("model", result)
        self.assertNotIn("input_tokens", result)
        self.assertNotIn("cached_tokens", result)
        self.assertNotIn("reasoning_tokens", result)
        self.assertNotIn("output_tokens", result)
        self.assertNotIn("duration_ms", result)
        self.assertNotIn("items_processed", result)
        self.assertNotIn("retries", result)
        self.assertNotIn("escalations", result)
        self.assertNotIn("validator_passed", result)
        self.assertNotIn("correction_or_override", result)

    def test_invalid_project_label_fails(self) -> None:
        code, result = self._run(
            "telemetry-record",
            "--path", str(self.store_path),
            "--project", "invalid project with spaces",
            "--category", "workflow-stage"
        )
        self.assertNotEqual(code, 0)

    def test_invalid_category_label_fails(self) -> None:
        code, result = self._run(
            "telemetry-record",
            "--path", str(self.store_path),
            "--project", "test-project",
            "--category", "invalid category with spaces"
        )
        self.assertNotEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
