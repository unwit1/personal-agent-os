"""Reviewers that contradict each other stop the repair loop early.

Measured 2026-10-17 (run selfcheck-on, gui-start-error): one reviewer called an
added catch redundant, the repair removed it, the next reviewer said the
assignment was unimplemented, the repair added it back, and so on: the file
flipped between two exact versions over five reviews and three repairs before
a person was asked anyway.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_os.orchestrator.adapters import synthetic  # noqa: E402
from agent_os.orchestrator.prompts import _REVIEWER_RULES  # noqa: E402
from test_orchestrator import OrchestratorFixture  # noqa: E402

WITH, WITHOUT = "try { start() } catch (e) { show(e) }\n", "try { start() } finally { done() }\n"


class OscillationTests(OrchestratorFixture):
    def test_a_repair_that_restores_a_reviewed_version_goes_to_the_stronger_reviewer_then_a_person(self) -> None:
        calls = {"reviewer": 0, "repairer": 0}

        def script(request, call):
            if request.role == "reviewer":
                calls["reviewer"] += 1
                ask_remove = calls["reviewer"] % 2 == 1
                finding = {"id": str(calls["reviewer"]), "severity": "medium", "path": "a/handler.js",
                           "summary": "the catch is redundant; remove it" if ask_remove else "the handler has no catch; add one",
                           "evidence": "handler.js line 1", "recommended_action": "remove the catch" if ask_remove else "add a catch"}
                return {"structured": {"status": "done", "verdict": "changes_requested", "findings": [finding]}}
            if request.role == "repairer":
                calls["repairer"] += 1
                return {"edits": {"a/handler.js": WITHOUT if calls["repairer"] % 2 == 1 else WITH}, "structured": {"status": "done"}}
            return {"edits": {"a/handler.js": WITH}, "structured": {"status": "done"}}

        synthetic.SCRIPTS["alpha"] = synthetic.SCRIPTS["beta"] = script
        run_id = self.create([self.task("a")], max_review_rounds=3)
        final = self.engine.run_loop(run_id, max_ticks=120)
        self.assertEqual(final["state"], "APPROVAL_REQUIRED")
        record = self.engine.load(run_id)
        events = (self.engine.store.run_dir(run_id) / "events.jsonl").read_text(encoding="utf-8")
        self.assertIn("review.oscillation", events)
        self.assertTrue(record["nodes"]["a"]["review"].get("escalated"))
        # Two cheap repairs, then the flip is detected: no final or extra repair.
        self.assertEqual(calls["repairer"], 2)
        self.assertEqual(calls["reviewer"], 3)

    def test_reviewers_may_not_demand_removing_a_requested_change(self) -> None:
        text = " ".join(_REVIEWER_RULES)
        self.assertIn("A change the assignment explicitly asks for is never a finding above low", text)
