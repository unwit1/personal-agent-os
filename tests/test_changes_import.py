from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.changes import load_changes_incremental


class IncrementalChangeImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.source_dir = root / "changes"
        self.source_dir.mkdir()
        self.ledger = root / "ingestion.json"
        self._write("CR-0001.json", "Keep fixture change requests searchable.")
        self._write("CR-0002.json", "Resume change imports from checkpoints.")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write(self, name: str, request_summary: str) -> None:
        (self.source_dir / name).write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "change_id": name.removesuffix(".json"),
                    "created_at": "2026-09-22T00:00:00+00:00",
                    "updated_at": "2026-09-22T00:00:00+00:00",
                    "change_type": "workflow",
                    "status": "OPEN",
                    "title": name,
                    "request_summary": request_summary,
                    "routing": {"project_id": "fixture-project", "confidence": 1.0},
                    "privacy": {"contains_raw_private_source": False},
                }
            ),
            encoding="utf-8",
        )

    def _run(self, **kwargs: object) -> dict[str, object]:
        return load_changes_incremental(
            "fixture-project",
            source_dir=self.source_dir,
            ledger_path=self.ledger,
            **kwargs,
        )

    def test_reimport_is_idempotent_and_ledger_is_metadata_only(self) -> None:
        first = self._run()
        second = self._run()

        self.assertEqual(first["stats"]["queued"], 2)
        self.assertEqual(second["stats"]["skipped"], 2)
        self.assertEqual(first["records"], second["records"])
        ledger_blob = self.ledger.read_text(encoding="utf-8")
        self.assertNotIn("Keep fixture change requests searchable", ledger_blob)
        self.assertNotIn("Resume change imports from checkpoints", ledger_blob)

    def test_changed_content_requeues_only_the_changed_record(self) -> None:
        self._run()
        self._write("CR-0001.json", "Changed fixture change request.")

        result = self._run()
        summaries = {record["request_summary"] for record in result["records"]}
        self.assertEqual(result["stats"]["reprocessed"], 1)
        self.assertEqual(result["stats"]["skipped"], 1)
        self.assertIn("Changed fixture change request.", summaries)
        self.assertNotIn("Keep fixture change requests searchable", summaries)

    def test_interruption_recovers_the_processing_record(self) -> None:
        def interrupt(path: Path) -> None:
            if path.name == "CR-0002.json":
                raise KeyboardInterrupt("fixture interruption")

        with self.assertRaises(KeyboardInterrupt):
            self._run(before_parse=interrupt)

        interrupted = json.loads(self.ledger.read_text(encoding="utf-8"))
        statuses = {item["source_key"]: item["status"] for item in interrupted["items"].values()}
        self.assertEqual(statuses["CR-0001.json"], "processed")
        self.assertEqual(statuses["CR-0002.json"], "processing")
        self.assertEqual(interrupted["checkpoint"]["cursor"], "CR-0001.json")

        resumed = self._run()
        self.assertEqual(resumed["stats"]["resumed"], 1)
        self.assertEqual(resumed["stats"]["skipped"], 1)
        self.assertEqual(resumed["checkpoint"]["cursor"], "CR-0002.json")

    def test_checkpoint_continues_after_completed_records(self) -> None:
        first = self._run()
        first_checkpoint = first["checkpoint"]
        second = self._run()
        second_checkpoint = second["checkpoint"]

        self.assertEqual(first_checkpoint["cursor"], "CR-0002.json")
        self.assertGreater(second_checkpoint["sequence"], first_checkpoint["sequence"])
        self.assertEqual(second_checkpoint["cursor"], "CR-0002.json")
        self.assertEqual(second["stats"]["skipped"], 2)


if __name__ == "__main__":
    unittest.main()
