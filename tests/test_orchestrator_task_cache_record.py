"""Task cache record side: an approved, integrated model-written node stores
exactly one scoped patch; nothing is stored when the flag is off or the review
is not an approval. Synthetic providers only."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_orchestrator import OrchestratorFixture  # noqa: E402


class TaskCacheRecordTests(OrchestratorFixture):
    def cache_files(self) -> list[Path]:
        return sorted((self.tmp / "home" / "task-cache").glob("*.json"))

    def run_task(self, enabled: bool, **policy) -> str:
        run_id = self.create([self.task("a")], **policy)
        record = self.engine.load(run_id)
        record["policy"]["task_cache_enabled"] = enabled
        self.engine.store.save(record)
        final = self.engine.run_loop(run_id, max_ticks=60)
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])
        return run_id

    def test_approved_node_records_one_scoped_patch(self) -> None:
        run_id = self.run_task(True)
        files = self.cache_files()
        self.assertEqual(len(files), 1)
        entry = json.loads(files[0].read_text(encoding="utf-8"))
        self.assertEqual(entry["metadata"]["node_id"], "a")
        self.assertEqual(entry["metadata"]["run_id"], run_id)
        self.assertTrue(entry["patch"])
        touched = [line.split(" b/", 1)[1] for line in entry["patch"].splitlines() if line.startswith("diff --git")]
        self.assertTrue(touched and all(path.startswith("a/") for path in touched), touched)
        self.assertTrue(entry["validator_evidence"])
        self.assertEqual(self.node(run_id, "a")["base"], self.engine.load(run_id)["nodes"]["a"]["base"])

    def test_flag_off_writes_nothing(self) -> None:
        self.run_task(False)
        self.assertEqual(self.cache_files(), [])

    def test_non_approved_review_writes_nothing(self) -> None:
        run_id = self.run_task(True, cleanup_worktrees=False)
        for path in self.cache_files():
            path.unlink()
        record = self.engine.load(run_id)
        record["nodes"]["a"]["review"]["reviewers"][-1]["verdict"] = "changes_requested"
        self.engine._record_task_cache(record, record["nodes"]["a"])
        self.assertEqual(self.cache_files(), [])

    def test_recording_failure_is_logged_not_raised(self) -> None:
        run_id = self.run_task(True, cleanup_worktrees=False)
        record = self.engine.load(run_id)
        self.engine._task_cache_key = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom"))
        self.engine._record_task_cache(record, record["nodes"]["a"])
        events = (self.tmp / "home" / "runs" / run_id / "events.jsonl")
        self.assertIn("task_cache.record_failed", events.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
