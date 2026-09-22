from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.compiler import load_handoffs_incremental


class IncrementalHandoffImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.source_dir = root / "handoffs"
        self.source_dir.mkdir()
        self.ledger = root / "ingestion.json"
        self._write("20260922T100000Z.json", "Keep fixture handoffs compact.")
        self._write("20260922T110000Z.json", "Resume handoff imports from checkpoints.")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write(self, name: str, remaining: str) -> None:
        (self.source_dir / name).write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "project": "fixture-project",
                    "created_at": name.removesuffix(".json"),
                    "completed": ["fixture work"],
                    "decisions": [],
                    "remaining": [remaining],
                    "validation": ["fixture tests passed"],
                    "candidate_memories": [],
                    "candidate_skills": [],
                }
            ),
            encoding="utf-8",
        )

    def _run(self, **kwargs: object) -> dict[str, object]:
        return load_handoffs_incremental(
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
        self.assertNotIn("Keep fixture handoffs compact", ledger_blob)
        self.assertNotIn("Resume handoff imports from checkpoints", ledger_blob)

    def test_changed_content_requeues_only_the_changed_record(self) -> None:
        self._run()
        self._write("20260922T110000Z.json", "Changed fixture handoff.")

        result = self._run()
        remaining = {record["remaining"][0] for record in result["records"]}
        self.assertEqual(result["stats"]["reprocessed"], 1)
        self.assertEqual(result["stats"]["skipped"], 1)
        self.assertIn("Changed fixture handoff.", remaining)
        self.assertNotIn("Resume handoff imports from checkpoints.", remaining)

    def test_interruption_recovers_the_processing_record(self) -> None:
        def interrupt(path: Path) -> None:
            if path.name == "20260922T100000Z.json":
                raise KeyboardInterrupt("fixture interruption")

        with self.assertRaises(KeyboardInterrupt):
            self._run(before_parse=interrupt)

        interrupted = json.loads(self.ledger.read_text(encoding="utf-8"))
        statuses = {item["source_key"]: item["status"] for item in interrupted["items"].values()}
        self.assertEqual(statuses["20260922T110000Z.json"], "processed")
        self.assertEqual(statuses["20260922T100000Z.json"], "processing")
        self.assertEqual(interrupted["checkpoint"]["cursor"], "20260922T110000Z.json")

        resumed = self._run()
        self.assertEqual(resumed["stats"]["resumed"], 1)
        self.assertEqual(resumed["stats"]["skipped"], 1)
        self.assertEqual(resumed["checkpoint"]["cursor"], "20260922T100000Z.json")

    def test_checkpoint_continues_after_completed_records(self) -> None:
        first = self._run()
        first_checkpoint = first["checkpoint"]
        second = self._run()
        second_checkpoint = second["checkpoint"]

        self.assertEqual(first_checkpoint["cursor"], "20260922T100000Z.json")
        self.assertGreater(second_checkpoint["sequence"], first_checkpoint["sequence"])
        self.assertEqual(second_checkpoint["cursor"], "20260922T100000Z.json")
        self.assertEqual(second["stats"]["skipped"], 2)


if __name__ == "__main__":
    unittest.main()
