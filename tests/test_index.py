from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.index import rebuild_documents  # noqa: E402


DOCUMENTS = [
    ("fixture/a.md", "fixture", "note", "alpha source"),
    ("fixture/b.md", "fixture", "note", "bravo source"),
]


class IncrementalIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.index_path = root / "index.sqlite"
        self.ledger_path = root / "ingestion.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _contents(self) -> list[str]:
        connection = sqlite3.connect(self.index_path)
        try:
            return [row[0] for row in connection.execute("SELECT content FROM documents ORDER BY path")]
        finally:
            connection.close()

    def test_rebuild_is_incremental_and_idempotent(self) -> None:
        first = rebuild_documents(DOCUMENTS, index_path=self.index_path, ledger_path=self.ledger_path)
        second = rebuild_documents(DOCUMENTS, index_path=self.index_path, ledger_path=self.ledger_path)

        self.assertEqual(first["queued"], 2)
        self.assertEqual(second["skipped"], 2)
        self.assertEqual(second["queued"], 0)
        self.assertEqual(self._contents(), ["alpha source", "bravo source"])

    def test_changed_content_reprocesses_the_same_logical_document(self) -> None:
        rebuild_documents(DOCUMENTS, index_path=self.index_path, ledger_path=self.ledger_path)
        changed = [DOCUMENTS[0][:3] + ("alpha revised",), DOCUMENTS[1]]
        result = rebuild_documents(changed, index_path=self.index_path, ledger_path=self.ledger_path)

        self.assertEqual(result["reprocessed"], 1)
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(self._contents(), ["alpha revised", "bravo source"])
        ledger = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        item = next(value for value in ledger["items"].values() if value["source_key"].endswith("fixture/a.md"))
        self.assertEqual(item["revision"], 2)
        self.assertEqual(item["status"], "processed")

    def test_interrupted_rebuild_recovers_the_claimed_document(self) -> None:
        def interrupt(path: str, scope: str, kind: str, content: str) -> None:
            if path == "fixture/b.md":
                raise KeyboardInterrupt()

        with self.assertRaises(KeyboardInterrupt):
            rebuild_documents(DOCUMENTS, index_path=self.index_path, ledger_path=self.ledger_path, before_write=interrupt)

        interrupted = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        self.assertEqual(sorted(item["status"] for item in interrupted["items"].values()), ["processed", "processing"])
        resumed = rebuild_documents(DOCUMENTS, index_path=self.index_path, ledger_path=self.ledger_path)
        self.assertEqual(resumed["skipped"], 1)
        self.assertEqual(resumed["resumed"], 1)
        self.assertEqual(self._contents(), ["alpha source", "bravo source"])

    def test_checkpoint_continues_after_interruption(self) -> None:
        def interrupt(path: str, scope: str, kind: str, content: str) -> None:
            if path == "fixture/b.md":
                raise KeyboardInterrupt()

        with self.assertRaises(KeyboardInterrupt):
            rebuild_documents(DOCUMENTS, index_path=self.index_path, ledger_path=self.ledger_path, before_write=interrupt)
        interrupted = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        self.assertEqual(interrupted["checkpoint"]["cursor"], "fixture:fixture/a.md")

        rebuild_documents(DOCUMENTS, index_path=self.index_path, ledger_path=self.ledger_path)
        resumed = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        self.assertEqual(resumed["checkpoint"]["cursor"], "fixture:fixture/b.md")
        self.assertGreater(resumed["checkpoint"]["sequence"], interrupted["checkpoint"]["sequence"])

    def test_deleted_derived_index_is_repaired_from_source(self) -> None:
        rebuild_documents(DOCUMENTS, index_path=self.index_path, ledger_path=self.ledger_path)
        self.index_path.unlink()
        repaired = rebuild_documents(DOCUMENTS, index_path=self.index_path, ledger_path=self.ledger_path)

        self.assertEqual(repaired["repaired"], 2)
        self.assertEqual(repaired["errors"], 0)
        self.assertEqual(self._contents(), ["alpha source", "bravo source"])


if __name__ == "__main__":
    unittest.main()
