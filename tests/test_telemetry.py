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


if __name__ == "__main__":
    unittest.main()
