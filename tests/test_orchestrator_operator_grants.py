"""Operator decisions that change what a node may do take effect.

Approving a worker's request for another file widens the node's scope
(``approve --add-scope``), and retrying a repair that failed its subject
reopens the subject instead of leaving the run blocked."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_os.orchestrator.adapters import synthetic
from agent_os.orchestrator.engine import OrchestratorError, _scope_additions
from test_orchestrator import OrchestratorFixture


class AddScopeTests(OrchestratorFixture):
    def test_granted_file_is_added_to_the_scope(self) -> None:
        asked = []

        def script(request, call):
            if request.role == "reviewer":
                return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
            if not asked:
                asked.append(1)
                return {"structured": {"status": "needs_decision", "summary": "need b/extra.txt",
                                       "question": "May b/extra.txt be added to the editable scope?"}}
            return {"edits": {"a/x.txt": "x\n", "b/extra.txt": "y\n"}, "structured": {"status": "done"}}

        for name in self.providers:
            synthetic.SCRIPTS[name] = script
        run_id = self.create([self.task("impl", scope=["a"])])
        record = self.engine.run_loop(run_id, max_ticks=20)
        gate = next(g for g in record["gates"] if g["kind"] == "agent_needs_decision")
        self.engine.decide(run_id, gate["id"], True, "yes", add_scope=["b/extra.txt"])
        self.assertIn("b/extra.txt", self.engine.load(run_id)["nodes"]["impl"]["scope"])
        final = self.engine.run_loop(run_id, max_ticks=40)
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])

    def test_paths_are_validated(self) -> None:
        self.assertEqual(_scope_additions([r"b\c.txt", "b/c.txt"]), ["b/c.txt"])
        for bad in ("../x", "/abs", "C:/x", ""):
            with self.assertRaises(OrchestratorError):
                _scope_additions([bad])


class RetryRepairTests(OrchestratorFixture):
    def test_retrying_a_failed_repair_reopens_its_subject(self) -> None:
        run_id = self.create([self.task("impl", scope=["a"])])
        record = self.engine.load(run_id)
        parent = record["nodes"]["impl"]
        repair = {**parent, "id": "impl.repair1", "role": "repairer", "subject": "impl",
                  "state": "FAILED_FINAL", "wait_reason": "validator still failing"}
        record["nodes"]["impl.repair1"] = repair
        record["order"].append("impl.repair1")
        parent["state"] = "FAILED_FINAL"
        parent["wait_reason"] = "repair impl.repair1 could not pass validation"
        self.engine.store.save(record)
        self.engine.retry(run_id, "impl.repair1")
        after = self.engine.load(run_id)
        self.assertEqual(after["nodes"]["impl.repair1"]["state"], "FAILED_RETRYABLE")
        self.assertEqual(after["nodes"]["impl"]["state"], "NEEDS_REPAIR")
        self.assertNotEqual(after["state"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
