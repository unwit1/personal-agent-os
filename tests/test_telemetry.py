from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.telemetry import (  # noqa: E402
    DEFAULT_PATH,
    LocalTelemetryStore,
    TelemetryEvent,
    TelemetryPrivacyError,
    aggregate_report,
)
from agent_os.cli import main  # noqa: E402
from agent_os.paths import ROOT  # noqa: E402


class TelemetryStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.store = LocalTelemetryStore(Path(self.tempdir.name) / "events.jsonl")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_synthetic_metadata_round_trips_without_raw_content(self) -> None:
        event = TelemetryEvent(
            project_id="fixture-project",
            task_category="workflow-stage",
            event_id="event-synthetic-1",
            occurred_at="2026-09-22T16:30:00+00:00",
            capability_class="deterministic",
            execution_path="cache",
            input_tokens=12,
            cached_tokens=8,
            duration_ms=4,
            items_processed=2,
            validator_passed=True,
        )

        self.store.record(event)
        loaded = self.store.read_events()

        self.assertEqual(loaded, [event])
        raw = self.store.path.read_text(encoding="utf-8")
        self.assertIn('"execution_path":"cache"', raw)
        self.assertNotIn("prompt", raw)
        self.assertNotIn("document", raw)
        self.assertNotIn("fixture source text", raw)

    def test_mapping_rejects_raw_private_fields(self) -> None:
        with self.assertRaises(TelemetryPrivacyError):
            self.store.record(
                {
                    "project_id": "fixture-project",
                    "task_category": "workflow-stage",
                    "prompt": "private source text",
                }
            )

        with self.assertRaises(TelemetryPrivacyError):
            self.store.record(
                {
                    "project_id": "fixture-project",
                    "task_category": "workflow-stage",
                    "api_key": "sk-synthetic-not-a-secret",
                }
            )

    def test_free_form_labels_are_rejected_instead_of_redacted(self) -> None:
        with self.assertRaises(TelemetryPrivacyError):
            TelemetryEvent(
                project_id="fixture-project",
                task_category="employee name from submitted document",
            )

    def test_store_rejects_canonical_paths_outside_local_runtime(self) -> None:
        with self.assertRaises(TelemetryPrivacyError):
            LocalTelemetryStore(ROOT / "projects" / "personal-agent-os" / "telemetry.jsonl")

    def test_default_store_is_gitignored_local_runtime(self) -> None:
        self.assertIn(".agent-local", str(DEFAULT_PATH))
        self.assertIn(".agent-local/", (ROOT / ".gitignore").read_text(encoding="utf-8"))

    def test_aggregate_report_counts_paths_and_validator_outcomes_only(self) -> None:
        events = [
            TelemetryEvent(
                project_id="fixture-project",
                task_category="stage",
                event_id="event-a",
                execution_path="deterministic",
                validator_passed=True,
            ),
            TelemetryEvent(
                project_id="fixture-project",
                task_category="stage",
                event_id="event-b",
                execution_path="cache",
                validator_passed=False,
            ),
            TelemetryEvent(
                project_id="other-fixture",
                task_category="stage",
                event_id="event-c",
            ),
            TelemetryEvent(
                project_id="other-fixture",
                task_category="stage",
                event_id="event-d",
                execution_path="cache",
                validator_passed=True,
            ),
        ]

        report = aggregate_report(events)

        self.assertEqual(report["event_count"], 4)
        self.assertEqual(
            report["execution_path_counts"],
            {"cache": 2, "deterministic": 1, "unknown": 1},
        )
        self.assertEqual(
            report["validator_outcome_counts"],
            {"failed": 1, "passed": 2, "unknown": 1},
        )
        serialized = str(report)
        self.assertNotIn("event-a", serialized)
        self.assertNotIn("fixture-project", serialized)
        self.assertNotIn("other-fixture", serialized)

    def test_store_aggregate_report_never_returns_raw_events(self) -> None:
        self.store.record(
            TelemetryEvent(
                project_id="fixture-project",
                task_category="stage",
                event_id="event-local",
                execution_path="skill",
                validator_passed=None,
            )
        )

        report = self.store.aggregate_report()

        self.assertEqual(report["event_count"], 1)
        self.assertEqual(report["execution_path_counts"], {"skill": 1})
        self.assertEqual(report["validator_outcome_counts"], {"unknown": 1})
        self.assertNotIn("event-local", str(report))

    def test_aggregate_report_applies_the_privacy_gate_to_mappings(self) -> None:
        with self.assertRaises(TelemetryPrivacyError):
            aggregate_report(
                [
                    {
                        "project_id": "fixture-project",
                        "task_category": "stage",
                        "document_text": "private source text",
                    }
                ]
            )

    def test_cli_reports_counts_without_emitting_persisted_events(self) -> None:
        self.store.record(
            TelemetryEvent(
                project_id="fixture-project",
                task_category="stage",
                event_id="event-cli",
                execution_path="deterministic",
                validator_passed=True,
            )
        )
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["telemetry-report", "--path", str(self.store.path)])

        self.assertEqual(exit_code, 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["event_count"], 1)
        self.assertEqual(report["execution_path_counts"], {"deterministic": 1})
        self.assertEqual(report["validator_outcome_counts"], {"passed": 1})
        self.assertNotIn("event-cli", output.getvalue())
        self.assertNotIn("fixture-project", output.getvalue())

    def test_cli_telemetry_report_with_group_by_project(self) -> None:
        self.store.record(
            TelemetryEvent(
                project_id="project-a",
                task_category="stage",
                event_id="event-a",
                input_tokens=10,
            )
        )
        self.store.record(
            TelemetryEvent(
                project_id="project-b",
                task_category="stage",
                event_id="event-b",
                input_tokens=5,
            )
        )
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["telemetry-report", "--path", str(self.store.path), "--group-by", "project"])

        self.assertEqual(exit_code, 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["group_by"], "project")
        self.assertIn("groups", report)
        self.assertIn("project-a", report["groups"])
        self.assertIn("project-b", report["groups"])
        self.assertEqual(report["groups"]["project-a"]["event_count"], 1)
        self.assertEqual(report["groups"]["project-b"]["event_count"], 1)
        self.assertNotIn("event-a", output.getvalue())
        self.assertNotIn("event-b", output.getvalue())

    def test_cli_telemetry_report_without_group_by(self) -> None:
        self.store.record(
            TelemetryEvent(
                project_id="project-a",
                task_category="stage",
                event_id="event-a",
            )
        )
        self.store.record(
            TelemetryEvent(
                project_id="project-b",
                task_category="stage",
                event_id="event-b",
            )
        )
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["telemetry-report", "--path", str(self.store.path)])

        self.assertEqual(exit_code, 0)
        report = json.loads(output.getvalue())
        self.assertNotIn("groups", report)
        self.assertNotIn("group_by", report)

    def test_aggregate_report_includes_new_retry_and_escalation_counts(self) -> None:
        events = [
            TelemetryEvent(
                project_id="fixture-project",
                task_category="stage",
                event_id="event-a",
                capability_class="reasoning",
                execution_path="deterministic",
                retries=0,
                escalations=0,
                validator_passed=True,
            ),
            TelemetryEvent(
                project_id="fixture-project",
                task_category="stage",
                event_id="event-b",
                capability_class="deterministic",
                execution_path="cache",
                retries=2,
                escalations=1,
                validator_passed=True,
            ),
            TelemetryEvent(
                project_id="fixture-project",
                task_category="stage",
                event_id="event-c",
                capability_class="reasoning",
                execution_path="skill",
                retries=None,
                escalations=None,
                validator_passed=False,
            ),
            TelemetryEvent(
                project_id="fixture-project",
                task_category="stage",
                event_id="event-d",
                capability_class="planning",
                execution_path="cache",
                retries=1,
                escalations=None,
                validator_passed=True,
            ),
        ]

        report = aggregate_report(events)

        self.assertEqual(report["event_count"], 4)
        self.assertEqual(
            report["capability_class_counts"],
            {"deterministic": 1, "planning": 1, "reasoning": 2},
        )
        self.assertEqual(report["retry_total"], 3)
        self.assertEqual(report["escalation_total"], 1)
        self.assertEqual(report["events_with_retries"], 2)
        self.assertEqual(report["events_with_escalations"], 1)
        self.assertEqual(report["retry_unknown_count"], 1)
        self.assertEqual(report["escalation_unknown_count"], 2)
        self.assertEqual(
            report["deterministic_path_model_class_counts"],
            {"planning": 1, "reasoning": 1},
        )
        serialized = str(report)
        self.assertNotIn("event-a", serialized)
        self.assertNotIn("event-b", serialized)
        self.assertNotIn("event-c", serialized)
        self.assertNotIn("event-d", serialized)
        self.assertNotIn("fixture-project", serialized)

    def test_aggregate_report_includes_token_totals_and_unknown_counts(self) -> None:
        events = [
            TelemetryEvent(
                project_id="fixture-project",
                task_category="stage",
                event_id="event-a",
                input_tokens=10,
                cached_tokens=5,
                reasoning_tokens=2,
                output_tokens=1,
            ),
            TelemetryEvent(
                project_id="fixture-project",
                task_category="stage",
                event_id="event-b",
                input_tokens=5,
                cached_tokens=3,
                reasoning_tokens=None,
                output_tokens=2,
            ),
            TelemetryEvent(
                project_id="fixture-project",
                task_category="stage",
                event_id="event-c",
            ),
        ]

        report = aggregate_report(events)

        self.assertEqual(report["event_count"], 3)
        self.assertEqual(report["token_totals"]["input_tokens"], 15)
        self.assertEqual(report["token_totals"]["cached_tokens"], 8)
        self.assertEqual(report["token_totals"]["reasoning_tokens"], 2)
        self.assertEqual(report["token_totals"]["output_tokens"], 3)
        self.assertEqual(report["token_unknown_counts"]["input_tokens"], 1)
        self.assertEqual(report["token_unknown_counts"]["cached_tokens"], 1)
        self.assertEqual(report["token_unknown_counts"]["reasoning_tokens"], 2)
        self.assertEqual(report["token_unknown_counts"]["output_tokens"], 1)

    def test_aggregate_report_empty_list_gives_zero_token_totals(self) -> None:
        report = aggregate_report([])

        self.assertEqual(report["event_count"], 0)
        self.assertEqual(report["token_totals"]["input_tokens"], 0)
        self.assertEqual(report["token_totals"]["cached_tokens"], 0)
        self.assertEqual(report["token_totals"]["reasoning_tokens"], 0)
        self.assertEqual(report["token_totals"]["output_tokens"], 0)
        self.assertEqual(report["token_unknown_counts"]["input_tokens"], 0)
        self.assertEqual(report["token_unknown_counts"]["cached_tokens"], 0)
        self.assertEqual(report["token_unknown_counts"]["reasoning_tokens"], 0)
        self.assertEqual(report["token_unknown_counts"]["output_tokens"], 0)

    def test_aggregate_report_excludes_sensitive_fields_from_json(self) -> None:
        events = [
            TelemetryEvent(
                project_id="fixture-project",
                task_category="stage",
                event_id="event-sensitive",
                model="gpt-4",
                input_tokens=10,
            ),
        ]

        report = aggregate_report(events)
        serialized = json.dumps(report)

        self.assertNotIn("event-sensitive", serialized)
        self.assertNotIn("fixture-project", serialized)
        self.assertNotIn("gpt-4", serialized)

    def test_aggregate_report_group_by_none_is_default(self) -> None:
        events = [
            TelemetryEvent(
                project_id="project-a",
                task_category="stage",
                execution_path="deterministic",
                input_tokens=10,
            ),
            TelemetryEvent(
                project_id="project-b",
                task_category="stage",
                execution_path="cache",
                input_tokens=5,
            ),
        ]

        report_default = aggregate_report(events)
        report_explicit_none = aggregate_report(events, group_by=None)

        self.assertEqual(report_default, report_explicit_none)
        self.assertNotIn("group_by", report_default)
        self.assertNotIn("groups", report_default)
        self.assertEqual(report_default["event_count"], 2)
        self.assertEqual(report_default["token_totals"]["input_tokens"], 15)

    def test_aggregate_report_group_by_project(self) -> None:
        events = [
            TelemetryEvent(
                project_id="project-a",
                task_category="stage",
                input_tokens=10,
            ),
            TelemetryEvent(
                project_id="project-a",
                task_category="other",
                input_tokens=5,
            ),
            TelemetryEvent(
                project_id="project-b",
                task_category="stage",
                input_tokens=3,
            ),
        ]

        report = aggregate_report(events, group_by="project")

        self.assertEqual(report["group_by"], "project")
        self.assertEqual(report["event_count"], 3)
        self.assertEqual(report["token_totals"]["input_tokens"], 18)
        self.assertIn("groups", report)
        self.assertIn("project-a", report["groups"])
        self.assertIn("project-b", report["groups"])
        self.assertEqual(report["groups"]["project-a"]["event_count"], 2)
        self.assertEqual(report["groups"]["project-a"]["token_totals"]["input_tokens"], 15)
        self.assertEqual(report["groups"]["project-b"]["event_count"], 1)
        self.assertEqual(report["groups"]["project-b"]["token_totals"]["input_tokens"], 3)
        self.assertNotIn("schema", report["groups"]["project-a"])

    def test_aggregate_report_group_by_category(self) -> None:
        events = [
            TelemetryEvent(
                project_id="project-a",
                task_category="workflow",
                input_tokens=10,
            ),
            TelemetryEvent(
                project_id="project-a",
                task_category="validation",
                input_tokens=5,
            ),
            TelemetryEvent(
                project_id="project-b",
                task_category="workflow",
                input_tokens=3,
            ),
        ]

        report = aggregate_report(events, group_by="category")

        self.assertEqual(report["group_by"], "category")
        self.assertEqual(report["event_count"], 3)
        self.assertIn("groups", report)
        self.assertIn("workflow", report["groups"])
        self.assertIn("validation", report["groups"])
        self.assertEqual(report["groups"]["workflow"]["event_count"], 2)
        self.assertEqual(report["groups"]["workflow"]["token_totals"]["input_tokens"], 13)
        self.assertEqual(report["groups"]["validation"]["event_count"], 1)
        self.assertEqual(report["groups"]["validation"]["token_totals"]["input_tokens"], 5)

    def test_aggregate_report_group_by_invalid_raises_error(self) -> None:
        events = [
            TelemetryEvent(
                project_id="project-a",
                task_category="stage",
            ),
        ]

        with self.assertRaises(ValueError) as ctx:
            aggregate_report(events, group_by="invalid-field")

        self.assertIn("unsupported telemetry report grouping", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
