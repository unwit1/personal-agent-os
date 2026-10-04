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


if __name__ == "__main__":
    unittest.main()
