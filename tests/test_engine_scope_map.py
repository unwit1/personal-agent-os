"""Worker scope maps are added to prompts only when enabled."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_orchestrator import OrchestratorFixture  # noqa: E402


class WorkerScopeMapTests(OrchestratorFixture):
    def _start_implementer(self, **policy: bool) -> tuple[str, str]:
        run_id = self.create([self.task("impl", scope=["impl/.keep"])], **policy)
        self.engine.start(run_id)
        self.engine.step(run_id)
        prompt = (self.engine.store.run_dir(run_id) / "workers" / "impl-1" / "prompt.md").read_text(encoding="utf-8")
        return run_id, prompt

    def test_engine_builds_scope_map_for_implementer_when_enabled(self) -> None:
        run_id, prompt = self._start_implementer(worker_scope_map=True)
        self.assertIn("Map of the files in your scope", prompt)
        self.assertIn("impl/.keep", prompt)
        events = [event for event in self.engine.ledger.read(run_id)[0]
                  if event["type"] == "context_selected" and event["node"] == "impl"]
        self.assertTrue(any("scope map" in event["data"].get("method", "") for event in events))

    def test_scope_map_is_absent_by_default(self) -> None:
        _, prompt = self._start_implementer()
        self.assertNotIn("Map of the files in your scope", prompt)

