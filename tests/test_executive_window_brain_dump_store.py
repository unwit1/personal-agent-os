import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import json
import tempfile
import unittest

from agent_os.executive.window.brain_dump_store import BrainDumpStore


class BrainDumpStoreTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name)
        self.store = BrainDumpStore(self.home)

    def tearDown(self):
        self._tmp.cleanup()

    def test_add_persists_and_attaches_clarification(self):
        result = {
            "records": [{"id": "a", "type": "task", "text": "Do thing", "project": None, "confidence": 0.5}],
            "clarifications": [{"record_id": "a", "reason": "Which project?", "candidates": ["X"]}],
        }
        self.assertEqual(self.store.add(result, tab="personal"), ["a"])
        self.assertEqual(BrainDumpStore(self.home).get("a")["clarification"], {
            "reason": "Which project?", "candidates": ["X"]
        })
        data = json.loads((self.home / "brain-dump.json").read_text(encoding="utf-8"))
        self.assertEqual(set(data), {"records"})
        self.assertEqual(data["records"]["a"]["tab"], "personal")

    def test_existing_ids_are_not_added_again(self):
        item = {"id": "a", "type": "task", "text": "Do thing", "project": None, "confidence": 0.5}
        self.assertEqual(self.store.add({"records": [item]}, tab="work"), ["a"])
        self.assertEqual(self.store.add({"records": [item]}, tab="personal"), [])
        self.assertEqual(self.store.existing_ids(), {"a"})

    def test_records_filter_sort_and_get_missing(self):
        self.store.add({"records": [
            {"id": "b", "type": "task", "text": "B", "project": None, "confidence": 1},
            {"id": "a", "type": "task", "text": "A", "project": None, "confidence": 1},
        ]}, tab="invalid")
        data = self.store._load()
        data["records"]["a"]["captured_at"] = "2025-01-01T00:00:00+00:00"
        data["records"]["b"]["captured_at"] = "2026-01-01T00:00:00+00:00"
        self.store._save(data)
        self.store.mark_staged("a", {"created": [], "duplicates": []})
        self.assertEqual([r["id"] for r in self.store.records()], ["b"])
        self.assertEqual([r["id"] for r in self.store.records(None)], ["a", "b"])
        self.assertEqual(self.store.get("b")["tab"], "work")
        with self.assertRaisesRegex(KeyError, "unknown brain-dump record: missing"):
            self.store.get("missing")

    def test_set_project_clears_clarification(self):
        self.store.add({"records": [{"id": "a", "type": "task", "text": "A", "project": None, "confidence": 0.5}],
                        "clarifications": [{"record_id": "a", "reason": "Which?", "candidates": []}]}, tab="work")
        record = self.store.set_project("a", "Project")
        self.assertEqual(record["project"], "Project")
        self.assertIsNone(record["clarification"])
        self.assertEqual(record["confidence"], 0.9)

    def test_mark_staged_hides_record_and_collects_candidate_ids(self):
        self.store.add({"records": [{"id": "a", "type": "task", "text": "A", "project": None, "confidence": 1}]}, tab="work")
        record = self.store.mark_staged("a", {"created": [{"id": "c1"}], "duplicates": [{"id": "c2"}]})
        self.assertEqual(record["candidate_ids"], ["c1", "c2"])
        self.assertEqual(self.store.records(), [])
        self.assertEqual(self.store.existing_ids(), {"a"})


if __name__ == '__main__':
    unittest.main()
