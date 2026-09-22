from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.improvements import load_improvements_incremental


class IncrementalImprovementImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.source_dir = root / "improvements"
        self.source_dir.mkdir()
        self.ledger = root / "ingestion.json"
        self._write("IMP-0001.json", "Keep fixture improvements searchable.")
        self._write("IMP-0002.json", "Resume improvement imports from checkpoints.")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write(self, name: str, observation: str) -> None:
        (self.source_dir / name).write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "id": name.removesuffix(".json"),
                    "project": "fixture-project",
                    "title": name,
                    "category": "workflow",
                    "status": "candidate",
                    "priority": "medium",
                    "observation": observation,
                    "evidence": ["fixture evidence"],
                    "suggested_direction": "Use a resumable local reader.",
                    "acceptance": ["The fixture import resumes safely."],
                    "created_at": "2026-09-22T00:00:00+00:00",
                    "updated_at": "2026-09-22T00:00:00+00:00",
                }
            ),
            encoding="utf-8",
        )

    def _run(self, **kwargs: object) -> dict[str, object]:
        return load_improvements_incremental(
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
        self.assertNotIn("Keep fixture improvements searchable", ledger_blob)
        self.assertNotIn("Resume improvement imports from checkpoints", ledger_blob)

    def test_changed_content_requeues_only_the_changed_record(self) -> None:
        self._run()
        self._write("IMP-0001.json", "Changed fixture improvement.")

        result = self._run()
        observations = {record["observation"] for record in result["records"]}
        self.assertEqual(result["stats"]["reprocessed"], 1)
        self.assertEqual(result["stats"]["skipped"], 1)
        self.assertIn("Changed fixture improvement.", observations)
        self.assertNotIn("Keep fixture improvements searchable", observations)

    def test_interruption_recovers_the_processing_record(self) -> None:
        def interrupt(path: Path) -> None:
            if path.name == "IMP-0002.json":
                raise KeyboardInterrupt("fixture interruption")

        with self.assertRaises(KeyboardInterrupt):
            self._run(before_parse=interrupt)

        interrupted = json.loads(self.ledger.read_text(encoding="utf-8"))
        statuses = {item["source_key"]: item["status"] for item in interrupted["items"].values()}
        self.assertEqual(statuses["IMP-0001.json"], "processed")
        self.assertEqual(statuses["IMP-0002.json"], "processing")
        self.assertEqual(interrupted["checkpoint"]["cursor"], "IMP-0001.json")

        resumed = self._run()
        self.assertEqual(resumed["stats"]["resumed"], 1)
        self.assertEqual(resumed["stats"]["skipped"], 1)
        self.assertEqual(resumed["checkpoint"]["cursor"], "IMP-0002.json")

    def test_checkpoint_continues_after_completed_records(self) -> None:
        first = self._run()
        first_checkpoint = first["checkpoint"]
        second = self._run()
        second_checkpoint = second["checkpoint"]

        self.assertEqual(first_checkpoint["cursor"], "IMP-0002.json")
        self.assertGreater(second_checkpoint["sequence"], first_checkpoint["sequence"])
        self.assertEqual(second_checkpoint["cursor"], "IMP-0002.json")
        self.assertEqual(second["stats"]["skipped"], 2)


if __name__ == "__main__":
    unittest.main()
