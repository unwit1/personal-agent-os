from __future__ import annotations

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
)
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


if __name__ == "__main__":
    unittest.main()
