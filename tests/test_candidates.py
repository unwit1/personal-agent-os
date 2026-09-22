from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_os.candidates import load_candidates_incremental


class IncrementalCandidateImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.source_dir = root / "candidates"
        self.source_dir.mkdir()
        self.ledger = root / "ingestion.json"
        self._write("candidate-a.json", "Keep candidate records reviewable.")
        self._write("candidate-b.json", "Resume candidate imports from checkpoints.")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write(self, name: str, statement: str) -> None:
        (self.source_dir / name).write_text(
            json.dumps(
                {
                    "id": name.removesuffix(".json"),
                    "kind": "lesson_candidate",
                    "statement": statement,
                    "evidence": ["fixture evidence"],
                }
            ),
            encoding="utf-8",
        )

    def _run(self, **kwargs: object) -> dict[str, object]:
        return load_candidates_incremental(
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
        self.assertNotIn("Keep candidate records reviewable", ledger_blob)
        self.assertNotIn("Resume candidate imports from checkpoints", ledger_blob)

    def test_changed_content_requeues_only_the_changed_record(self) -> None:
        self._run()
        self._write("candidate-a.json", "Changed candidate record.")

        result = self._run()
        statements = {record["statement"] for record in result["records"]}
        self.assertEqual(result["stats"]["reprocessed"], 1)
        self.assertEqual(result["stats"]["skipped"], 1)
        self.assertIn("Changed candidate record.", statements)
        self.assertNotIn("Keep candidate records reviewable", statements)

    def test_interruption_recovers_the_processing_record(self) -> None:
        def interrupt(path: Path) -> None:
            if path.name == "candidate-b.json":
                raise KeyboardInterrupt("fixture interruption")

        with self.assertRaises(KeyboardInterrupt):
            self._run(before_parse=interrupt)

        interrupted = json.loads(self.ledger.read_text(encoding="utf-8"))
        statuses = {item["source_key"]: item["status"] for item in interrupted["items"].values()}
        self.assertEqual(statuses["candidate-a.json"], "processed")
        self.assertEqual(statuses["candidate-b.json"], "processing")
        self.assertEqual(interrupted["checkpoint"]["cursor"], "candidate-a.json")

        resumed = self._run()
        self.assertEqual(resumed["stats"]["resumed"], 1)
        self.assertEqual(resumed["stats"]["skipped"], 1)
        self.assertEqual(resumed["checkpoint"]["cursor"], "candidate-b.json")

    def test_checkpoint_continues_after_completed_records(self) -> None:
        first = self._run()
        first_checkpoint = first["checkpoint"]
        second = self._run()
        second_checkpoint = second["checkpoint"]

        self.assertEqual(first_checkpoint["cursor"], "candidate-b.json")
        self.assertGreater(second_checkpoint["sequence"], first_checkpoint["sequence"])
        self.assertEqual(second_checkpoint["cursor"], "candidate-b.json")
        self.assertEqual(second["stats"]["skipped"], 2)


if __name__ == "__main__":
    unittest.main()
