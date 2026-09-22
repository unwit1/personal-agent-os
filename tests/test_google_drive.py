from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from agent_os import google_drive
from agent_os.ingestion import content_fingerprint


FIXTURE = Path(__file__).parent / "fixtures" / "google_drive" / "synthetic_files.json"


class GoogleDriveAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.scope = fixture["drive_scope"]
        self.records = [google_drive.GoogleDriveFile.from_mapping(self.scope, value) for value in fixture["files"]]

    def test_reimport_is_idempotent_and_rename_move_preserves_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = Path(directory) / "ingestion.json"
            first = google_drive.sync_records(self.records, drive_scope=self.scope, ledger_path=ledger_path)
            renamed = replace(self.records[0], name="Renamed Alpha.txt", parents=("folder-archive",))
            second = google_drive.sync_records([renamed, self.records[1]], drive_scope=self.scope, ledger_path=ledger_path)

            self.assertEqual(first["indexed_new"], 2)
            self.assertEqual(second["skipped"], 2)
            self.assertEqual(google_drive.drive_source_key(self.scope, self.records[0].file_id), renamed.source_key)
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            item = ledger["items"][next(iter(ledger["items"]))]
            self.assertEqual(item["revision"], 1)
            self.assertNotIn("Synthetic Drive alpha content", ledger_path.read_text(encoding="utf-8"))
            self.assertNotIn("Renamed Alpha", ledger_path.read_text(encoding="utf-8"))

    def test_changed_content_requeues_the_same_file_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = Path(directory) / "ingestion.json"
            google_drive.sync_records([self.records[0]], drive_scope=self.scope, ledger_path=ledger_path)
            changed = replace(self.records[0], content=b"Synthetic Drive alpha content v2.")
            result = google_drive.sync_records([changed], drive_scope=self.scope, ledger_path=ledger_path)

            self.assertEqual(result["reprocessed"], 1)
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            self.assertEqual(len(ledger["items"]), 1)
            item = next(iter(ledger["items"].values()))
            self.assertEqual(item["source_key"], self.records[0].source_key)
            self.assertEqual(item["revision"], 2)
            self.assertEqual(item["status"], "processed")
            self.assertEqual(item["content_hash"], content_fingerprint(changed.content))
            self.assertNotEqual(item["content_hash"], content_fingerprint(self.records[0].content))

    def test_interrupted_processing_is_recovered_on_reimport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = Path(directory) / "ingestion.json"
            calls = 0

            def interrupt_first(_record: google_drive.GoogleDriveFile) -> list[str]:
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise KeyboardInterrupt()
                return ["synthetic:completed"]

            with self.assertRaises(KeyboardInterrupt):
                google_drive.sync_records([self.records[0]], drive_scope=self.scope, ledger_path=ledger_path, processor=interrupt_first)

            interrupted = json.loads(ledger_path.read_text(encoding="utf-8"))
            self.assertEqual(next(iter(interrupted["items"].values()))["status"], "processing")
            resumed = google_drive.sync_records([self.records[0]], drive_scope=self.scope, ledger_path=ledger_path)
            self.assertEqual(resumed["resumed"], 1)
            self.assertEqual(next(iter(json.loads(ledger_path.read_text(encoding="utf-8"))["items"].values()))["status"], "processed")

    def test_checkpoint_continues_after_interruption(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = Path(directory) / "ingestion.json"

            def interrupt_second(record: google_drive.GoogleDriveFile) -> list[str]:
                if record.file_id == self.records[1].file_id:
                    raise KeyboardInterrupt()
                return [f"synthetic:{record.file_id}"]

            with self.assertRaises(KeyboardInterrupt):
                google_drive.sync_records(self.records, drive_scope=self.scope, ledger_path=ledger_path, processor=interrupt_second)
            interrupted = json.loads(ledger_path.read_text(encoding="utf-8"))
            first_checkpoint = interrupted["checkpoint"]
            self.assertEqual(first_checkpoint["cursor"], self.records[0].source_key)

            resumed = google_drive.sync_records(self.records, drive_scope=self.scope, ledger_path=ledger_path)
            final = json.loads(ledger_path.read_text(encoding="utf-8"))
            self.assertEqual(resumed["checkpoint"]["cursor"], self.records[1].source_key)
            self.assertEqual(final["checkpoint"]["cursor"], self.records[1].source_key)
            self.assertGreater(final["checkpoint"]["sequence"], first_checkpoint["sequence"])


if __name__ == "__main__":
    unittest.main()
