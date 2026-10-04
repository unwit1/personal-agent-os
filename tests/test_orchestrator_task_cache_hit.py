"""Task cache read side: an identical node in a later run is satisfied by the
cached patch (no worker, no review); misses fall through to the model."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_orchestrator import OrchestratorFixture, edit_script  # noqa: E402

from agent_os.orchestrator.adapters import synthetic  # noqa: E402


class TaskCacheHitTests(OrchestratorFixture):
    def run_once(self) -> dict:
        run_id = self.create([self.task("a")])
        record = self.engine.load(run_id)
        record["policy"]["task_cache_enabled"] = True
        self.engine.store.save(record)
        final = self.engine.run_loop(run_id, max_ticks=60)
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])
        return self.engine.load(run_id)

    def roles_called(self) -> list[str]:
        seen: list[str] = []
        base = edit_script()

        def script(request, call):
            seen.append(request.role)
            return base(request, call)

        synthetic.SCRIPTS["alpha"] = synthetic.SCRIPTS["beta"] = script
        return seen

    def test_second_identical_run_skips_worker_and_review(self) -> None:
        self.run_once()
        seen = self.roles_called()
        record = self.run_once()
        node = record["nodes"]["a"]
        self.assertNotIn("implementer", seen)
        self.assertNotIn("reviewer", seen)
        self.assertTrue(node["task_cache"]["hit"])
        self.assertTrue(node["integrated"])
        self.assertEqual(node["review"]["cached_from"]["node_id"], "a")

    def test_absent_entry_falls_through_to_the_model(self) -> None:
        seen = self.roles_called()
        record = self.run_once()
        self.assertIn("implementer", seen)
        self.assertEqual(record["nodes"]["a"]["task_cache"]["miss"], "absent")

    def test_unusable_entry_is_a_miss_not_a_failure(self) -> None:
        self.run_once()
        for path in (self.tmp / "home" / "task-cache").glob("*.json"):
            entry = json.loads(path.read_text(encoding="utf-8"))
            entry["patch"] = "not a patch\n"
            path.write_text(json.dumps(entry), encoding="utf-8")
        seen = self.roles_called()
        record = self.run_once()
        self.assertIn("implementer", seen)
        self.assertEqual(record["nodes"]["a"]["task_cache"]["miss"], "apply_failed")


if __name__ == "__main__":
    unittest.main()
