from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

from agent_os.cli import main  # noqa: E402
from agent_os.telemetry import LocalTelemetryStore, TelemetryEvent  # noqa: E402
from test_workflows import MANIFEST, WorkflowFixture  # noqa: E402


class TelemetryReportCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = LocalTelemetryStore(Path(self.tmp.name) / "events.jsonl")

    def _run(self, *args: str) -> dict:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["telemetry-report", "--path", str(self.store.path), *args])
        self.assertEqual(code, 0)
        return json.loads(output.getvalue())

    def test_group_by_project_reports_groups_and_token_totals(self) -> None:
        for event_id, project, tokens in (("e1", "proj-a", 10), ("e2", "proj-b", None)):
            self.store.record(
                TelemetryEvent(
                    project_id=project,
                    task_category="stage",
                    event_id=event_id,
                    execution_path="deterministic",
                    input_tokens=tokens,
                )
            )
        report = self._run("--group-by", "project")
        self.assertEqual(report["group_by"], "project")
        self.assertEqual(sorted(report["groups"]), ["proj-a", "proj-b"])
        self.assertEqual(report["token_totals"]["input_tokens"], 10)
        self.assertEqual(report["token_unknown_counts"]["input_tokens"], 1)

    def test_ungrouped_report_has_no_groups(self) -> None:
        report = self._run()
        self.assertNotIn("groups", report)
        self.assertEqual(report["event_count"], 0)


class WorkflowCliTelemetryTests(WorkflowFixture):
    def setUp(self) -> None:
        super().setUp()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def _run_cli(self, *args: str) -> tuple[int, dict]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(list(args))
        try:
            result = json.loads(output.getvalue())
        except json.JSONDecodeError:
            result = None
        return code, result

    def test_workflow_run_with_telemetry_path_records_deterministic_event(self) -> None:
        telemetry_path = Path(self.tmp.name) / "events.jsonl"
        from agent_os import workflows
        workflows.start("fixture-sweep", run_id="cli-tel")

        code, result = self._run_cli(
            "workflow-run", "fixture-sweep", "--run-id", "cli-tel", "--stage", "cheap-check",
            "--telemetry-path", str(telemetry_path)
        )
        self.assertEqual(code, 0)

        store = LocalTelemetryStore(telemetry_path)
        events = store.read_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].execution_path, "deterministic")
        self.assertEqual(events[0].validator_passed, True)

    def test_workflow_run_without_telemetry_path_creates_no_file(self) -> None:
        from agent_os import workflows

        # First run with telemetry path
        telemetry_path = Path(self.tmp.name) / "events.jsonl"
        workflows.start("fixture-sweep", run_id="cli-tel-2")

        code, result = self._run_cli(
            "workflow-run", "fixture-sweep", "--run-id", "cli-tel-2", "--stage", "cheap-check",
            "--telemetry-path", str(telemetry_path)
        )
        self.assertEqual(code, 0)

        # Verify first file was created with 1 event
        store = LocalTelemetryStore(telemetry_path)
        events = store.read_events()
        self.assertEqual(len(events), 1)

        # Second run without telemetry path on the same deterministic stage with a new run id
        workflows.start("fixture-sweep", run_id="cli-tel-2b")

        code, result = self._run_cli(
            "workflow-run", "fixture-sweep", "--run-id", "cli-tel-2b", "--stage", "cheap-check"
        )
        self.assertEqual(code, 0)

        # Verify first file still has 1 event
        events_after = store.read_events()
        self.assertEqual(len(events_after), 1)

        # Verify no additional .jsonl files were created in the temp directory
        jsonl_files = sorted(p.name for p in Path(self.tmp.name).glob("*.jsonl"))
        self.assertEqual(jsonl_files, ["events.jsonl"])

    def test_workflow_complete_records_provider_and_tokens(self) -> None:
        from agent_os import workflows
        telemetry_path = Path(self.tmp.name) / "events.jsonl"

        workflows.start("fixture-sweep", run_id="cli-tel-3")
        workflows.run_stage("fixture-sweep", "cli-tel-3")

        code, result = self._run_cli(
            "workflow-complete", "fixture-sweep", "--run-id", "cli-tel-3", "--stage", "think",
            "--output", "recommendation",
            "--telemetry-path", str(telemetry_path),
            "--provider", "openai", "--model", "gpt-4o",
            "--input-tokens", "500", "--output-tokens", "200"
        )
        self.assertEqual(code, 0)

        store = LocalTelemetryStore(telemetry_path)
        report = store.aggregate_report()
        self.assertEqual(report["token_totals"]["input_tokens"], 500)
        self.assertEqual(report["token_totals"]["output_tokens"], 200)
        self.assertEqual(report["token_unknown_counts"]["cached_tokens"], 1)

    def test_workflow_complete_records_duration_items_and_override(self) -> None:
        from agent_os import workflows
        telemetry_path = Path(self.tmp.name) / "events.jsonl"

        workflows.start("fixture-sweep", run_id="cli-tel-5")
        workflows.run_stage("fixture-sweep", "cli-tel-5")

        code, result = self._run_cli(
            "workflow-complete", "fixture-sweep", "--run-id", "cli-tel-5", "--stage", "think",
            "--output", "recommendation",
            "--telemetry-path", str(telemetry_path),
            "--duration-ms", "5000", "--items-processed", "42", "--override"
        )
        self.assertEqual(code, 0)

        store = LocalTelemetryStore(telemetry_path)
        events = store.read_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].duration_ms, 5000)
        self.assertEqual(events[0].items_processed, 42)
        self.assertIs(events[0].correction_or_override, True)

    def test_workflow_complete_with_only_duration_ms_leaves_others_unknown(self) -> None:
        from agent_os import workflows
        telemetry_path = Path(self.tmp.name) / "events.jsonl"

        workflows.start("fixture-sweep", run_id="cli-tel-6")
        workflows.run_stage("fixture-sweep", "cli-tel-6")

        code, result = self._run_cli(
            "workflow-complete", "fixture-sweep", "--run-id", "cli-tel-6", "--stage", "think",
            "--output", "recommendation",
            "--telemetry-path", str(telemetry_path),
            "--duration-ms", "10"
        )
        self.assertEqual(code, 0)

        store = LocalTelemetryStore(telemetry_path)
        events = store.read_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].duration_ms, 10)
        self.assertIsNone(events[0].items_processed)
        self.assertIsNone(events[0].correction_or_override)

    def test_workflow_complete_with_negative_items_processed_fails(self) -> None:
        from agent_os import workflows
        telemetry_path = Path(self.tmp.name) / "events.jsonl"

        workflows.start("fixture-sweep", run_id="cli-tel-7")
        workflows.run_stage("fixture-sweep", "cli-tel-7")

        code, result = self._run_cli(
            "workflow-complete", "fixture-sweep", "--run-id", "cli-tel-7", "--stage", "think",
            "--output", "recommendation",
            "--telemetry-path", str(telemetry_path),
            "--items-processed", "-1"
        )
        self.assertNotEqual(code, 0)

        store = LocalTelemetryStore(telemetry_path)
        events = store.read_events()
        self.assertEqual(len(events), 0)

    def test_telemetry_path_in_canonical_repo_fails_with_exit_code_2(self) -> None:
        from agent_os import workflows
        from agent_os.paths import ROOT

        telemetry_path = ROOT / "projects" / "telemetry-test.jsonl"
        workflows.start("fixture-sweep", run_id="cli-tel-4")

        code, result = self._run_cli(
            "workflow-run", "fixture-sweep", "--run-id", "cli-tel-4", "--stage", "cheap-check",
            "--telemetry-path", str(telemetry_path)
        )
        self.assertEqual(code, 2)
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertFalse(telemetry_path.exists())

    def test_workflow_complete_with_openai_chat_usage_file_records_counts(self) -> None:
        from agent_os import workflows
        telemetry_path = Path(self.tmp.name) / "events.jsonl"
        usage_file = Path(self.tmp.name) / "usage.json"

        usage_file.write_text(json.dumps({
            "prompt_tokens": 100,
            "prompt_tokens_details": {"cached_tokens": 40},
            "completion_tokens": 20,
            "completion_tokens_details": {"reasoning_tokens": 5},
        }), encoding="utf-8")

        workflows.start("fixture-sweep", run_id="cli-tel-8")
        workflows.run_stage("fixture-sweep", "cli-tel-8")

        code, result = self._run_cli(
            "workflow-complete", "fixture-sweep", "--run-id", "cli-tel-8", "--stage", "think",
            "--output", "recommendation",
            "--telemetry-path", str(telemetry_path),
            "--usage-file", str(usage_file),
            "--usage-format", "openai-chat"
        )
        self.assertEqual(code, 0)

        store = LocalTelemetryStore(telemetry_path)
        events = store.read_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].input_tokens, 100)
        self.assertEqual(events[0].cached_tokens, 40)
        self.assertEqual(events[0].reasoning_tokens, 5)
        self.assertEqual(events[0].output_tokens, 20)

    def test_workflow_complete_with_anthropic_usage_file_extracts_only_counts(self) -> None:
        from agent_os import workflows
        telemetry_path = Path(self.tmp.name) / "events.jsonl"
        usage_file = Path(self.tmp.name) / "usage.json"

        usage_file.write_text(json.dumps({
            "input_tokens": 150,
            "output_tokens": 75,
            "content": [{"type": "text", "text": "This is a response"}],
        }), encoding="utf-8")

        workflows.start("fixture-sweep", run_id="cli-tel-9")
        workflows.run_stage("fixture-sweep", "cli-tel-9")

        code, result = self._run_cli(
            "workflow-complete", "fixture-sweep", "--run-id", "cli-tel-9", "--stage", "think",
            "--output", "recommendation",
            "--telemetry-path", str(telemetry_path),
            "--usage-file", str(usage_file),
            "--usage-format", "anthropic"
        )
        self.assertEqual(code, 0)

        store = LocalTelemetryStore(telemetry_path)
        events = store.read_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].input_tokens, 150)
        self.assertEqual(events[0].output_tokens, 75)

        # Verify the content text is not in the recorded event
        event_jsonl = telemetry_path.read_text(encoding="utf-8")
        self.assertNotIn("This is a response", event_jsonl)

    def test_workflow_complete_with_usage_file_and_input_tokens_fails(self) -> None:
        from agent_os import workflows
        telemetry_path = Path(self.tmp.name) / "events.jsonl"
        usage_file = Path(self.tmp.name) / "usage.json"

        usage_file.write_text(json.dumps({
            "prompt_tokens": 100,
            "completion_tokens": 20,
        }), encoding="utf-8")

        workflows.start("fixture-sweep", run_id="cli-tel-10")
        workflows.run_stage("fixture-sweep", "cli-tel-10")

        code, result = self._run_cli(
            "workflow-complete", "fixture-sweep", "--run-id", "cli-tel-10", "--stage", "think",
            "--output", "recommendation",
            "--telemetry-path", str(telemetry_path),
            "--usage-file", str(usage_file),
            "--usage-format", "openai-chat",
            "--input-tokens", "500"
        )
        self.assertEqual(code, 2)

        store = LocalTelemetryStore(telemetry_path)
        events = store.read_events()
        self.assertEqual(len(events), 0)

    def test_workflow_complete_with_usage_file_without_format_fails(self) -> None:
        from agent_os import workflows
        telemetry_path = Path(self.tmp.name) / "events.jsonl"
        usage_file = Path(self.tmp.name) / "usage.json"

        usage_file.write_text(json.dumps({
            "prompt_tokens": 100,
            "completion_tokens": 20,
        }), encoding="utf-8")

        workflows.start("fixture-sweep", run_id="cli-tel-11")
        workflows.run_stage("fixture-sweep", "cli-tel-11")

        code, result = self._run_cli(
            "workflow-complete", "fixture-sweep", "--run-id", "cli-tel-11", "--stage", "think",
            "--output", "recommendation",
            "--telemetry-path", str(telemetry_path),
            "--usage-file", str(usage_file)
        )
        self.assertEqual(code, 2)

        store = LocalTelemetryStore(telemetry_path)
        events = store.read_events()
        self.assertEqual(len(events), 0)


if __name__ == "__main__":
    unittest.main()
