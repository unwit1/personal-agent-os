from __future__ import annotations

from tests.test_orchestrator import OrchestratorFixture, synthetic


class SpendCapTests(OrchestratorFixture):
    def script(self, request, call):
        if request.role == "reviewer":
            return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
        return {"edits": {f"{request.node_id}/out.txt": "done\n"}, "structured": {"status": "done"},
                "usage": {"input_tokens": 100, "output_tokens": 20, "cost_usd": 1.0}}

    def setUp(self):
        super().setUp()
        for name in self.providers:
            synthetic.SCRIPTS[name] = self.script

    def gated(self, **policy):
        run_id = self.create([self.task("a"), self.task("b", depends_on=["a"])],
                             require_independent_review_for_model_edits=False, **policy)
        final = self.engine.run_loop(run_id, max_ticks=60)
        self.assertEqual(final["state"], "APPROVAL_REQUIRED")
        gate = final["gates"][-1]
        self.assertEqual(gate["kind"], "budget_exhausted")
        return run_id, gate

    def test_usd_cap_gates_before_next_launch_and_approval_raises_cap(self):
        run_id, gate = self.gated(max_usd=1.5)
        record = self.engine.load(run_id)
        self.assertEqual(gate["cap"], "usd")
        self.assertEqual(record["launches"], 1)
        budget = record["launch_budget"]
        self.engine.decide(run_id, gate["id"], approve=True)
        record = self.engine.load(run_id)
        self.assertEqual(record["usd_cap"], 2.25)
        self.assertEqual(record["launch_budget"], budget)
        self.engine.run_loop(run_id, max_ticks=60)
        self.assertEqual(self.engine.load(run_id)["launches"], 2)

    def test_token_cap_and_decline(self):
        run_id, gate = self.gated(max_tokens=150)
        record = self.engine.load(run_id)
        self.assertEqual(gate["cap"], "tokens")
        old = record["token_cap"]
        self.engine.decide(run_id, gate["id"], approve=False)
        record = self.engine.load(run_id)
        self.assertEqual(record["token_cap"], old)
        self.assertEqual(record["state_reason"], "token cap reached; user declined more")

    def test_usd_decline_keeps_cap_and_records_reason(self):
        run_id, gate = self.gated(max_usd=1.5)
        old = self.engine.load(run_id)["usd_cap"]
        self.engine.decide(run_id, gate["id"], approve=False)
        record = self.engine.load(run_id)
        self.assertEqual(record["usd_cap"], old)
        self.assertEqual(record["state_reason"], "money cap reached; user declined more")

    def test_no_caps_completes(self):
        run_id = self.create([self.task("a"), self.task("b", depends_on=["a"])],
                             require_independent_review_for_model_edits=False)
        self.assertEqual(self.engine.run_loop(run_id, max_ticks=60)["state"], "COMPLETE")
