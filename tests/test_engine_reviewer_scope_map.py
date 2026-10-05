"""Reviewer scope maps are added only when enabled."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_os.orchestrator.adapters import synthetic  # noqa: E402
from test_orchestrator import OrchestratorFixture  # noqa: E402


class ReviewerScopeMapTests(OrchestratorFixture):
    def reviewer_script(self, rounds: list[dict]):
        state = {"round": 0}

        def script(request, call):
            if request.role == "reviewer":
                result = rounds[min(state["round"], len(rounds) - 1)]
                state["round"] += 1
                return {"structured": result}
            if request.role == "repairer":
                return {"edits": {"a/fixed.txt": "fixed\n"}, "structured": {"status": "done", "dispositions": []}}
            return {"edits": {"a/impl.txt": "impl\n"}, "structured": {"status": "done"}}

        return script

    def test_reviewer_prompt_includes_subject_scope_map_when_enabled(self) -> None:
        script = self.reviewer_script([{"status": "done", "verdict": "approved", "findings": []}])
        synthetic.SCRIPTS["alpha"] = script
        synthetic.SCRIPTS["beta"] = script
        run_id = self.create([self.task("a")], reviewer_scope_map=True)
        self.engine.run_loop(run_id, max_ticks=60)

        record = self.engine.load(run_id)
        reviewer = next(node for node in record["nodes"].values() if node["role"] == "reviewer")
        prompts = list((self.engine.store.run_dir(run_id) / "workers").glob(f"{reviewer['id']}-*/prompt.md"))
        self.assertTrue(prompts, f"missing prompt for reviewer {reviewer['id']}")
        prompt = prompts[0].read_text(encoding="utf-8")
        self.assertIn("Map of the reviewed task's scope files", prompt)
        self.assertIn("Files in your scope (local map; lines, top-level names):", prompt)
        events = [event for event in self.engine.ledger.read(run_id)[0]
                  if event["type"] == "context_selected" and event["node"] == reviewer["id"]]
        self.assertTrue(any("scope map for the reviewer" in event["data"].get("method", "") for event in events))
