from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from tests.test_orchestrator import OrchestratorFixture, synthetic
from agent_os.orchestrator.engine import _node_view


class ReviewIndependenceTests(OrchestratorFixture):
    def script(self, verdict="approved", severity=None):
        def run(request, call):
            if request.role == "reviewer":
                findings = [] if severity is None else [{"id": "finding", "severity": severity, "summary": "finding", "path": "a/file.txt"}]
                return {"structured": {"status": "done", "verdict": verdict, "findings": findings}}
            return {"edits": {"a/file.txt": "change\n"}, "structured": {"status": "done"}}
        return run

    def cool_beta(self, seconds):
        from agent_os.orchestrator import engine as engine_mod
        until = (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat(timespec="seconds")
        engine_mod._write_cooldown(self.engine.store.home, "beta", until, "quota: test")
        self.engine._availability = {"alpha": True, "beta": True}

    def test_waits_for_soon_independent_provider(self):
        self.cool_beta(60)
        synthetic.SCRIPTS["alpha"] = self.script()
        run_id = self.create([self.task("a")], wait_for_reset_seconds=300)
        self.engine.start(run_id)
        for _ in range(200):  # validation runs in the background: tick until review is requested
            self.engine.step(run_id)
            # Validation runs on a background thread; without waiting for it the
            # node reached review only when the thread happened to win the race
            # (failed about half the time, and blocked two fix runs on 2026-10-17).
            self.engine._sleep(0)
            node = self.node(run_id, "a")
            if node["state"] == "WAITING_FOR_REVIEW":
                break
            time.sleep(0.02)
        reviewer = next(n for n in self.engine.load(run_id)["nodes"].values() if n["role"] == "reviewer")
        self.engine.step(run_id)
        reviewer = self.engine.load(run_id)["nodes"][reviewer["id"]]
        self.assertEqual(reviewer["state"], "RUNNABLE")
        self.assertIn("independent reviewer", reviewer["wait_reason"])
        self.assertNotEqual((reviewer.get("selection") or {}).get("provider"), "alpha")

    def test_far_reset_allows_same_provider_review(self):
        self.cool_beta(7200)
        synthetic.SCRIPTS["alpha"] = self.script()
        run_id = self.create([self.task("a")], wait_for_reset_seconds=300)
        final = self.engine.run_loop(run_id, max_ticks=60)
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])
        review = self.engine.load(run_id)["nodes"]["a"]["review"]["reviewers"]
        self.assertFalse(review[0]["independent_provider"])

    def test_same_provider_low_finding_becomes_follow_up_at_cap(self):
        self.cool_beta(7200)
        synthetic.SCRIPTS["alpha"] = self.script("changes_requested", "low")
        run_id = self.create([self.task("a")], max_same_provider_review_rounds=1, wait_for_reset_seconds=300)
        final = self.engine.run_loop(run_id, max_ticks=60)
        node = self.engine.load(run_id)["nodes"]["a"]
        self.assertEqual(node["state"], "PASSED")
        self.assertEqual(len(node["review"]["follow_ups"]), 1)
        self.assertFalse(any(n["role"] == "repairer" for n in self.engine.load(run_id)["nodes"].values()))
        self.assertFalse(any(g["kind"] == "unresolved_review_findings" for g in final["gates"]))

    def test_medium_same_provider_finding_still_repairs(self):
        self.cool_beta(7200)
        synthetic.SCRIPTS["alpha"] = self.script("changes_requested", "medium")
        run_id = self.create([self.task("a")], max_same_provider_review_rounds=1, wait_for_reset_seconds=300)
        self.engine.run_loop(run_id, max_ticks=20)
        record = self.engine.load(run_id)
        self.assertNotEqual(record["nodes"]["a"]["state"], "PASSED")
        self.assertTrue(any(n["role"] == "repairer" for n in record["nodes"].values()))

    def test_independent_low_finding_behaviour_is_unchanged(self):
        synthetic.SCRIPTS["alpha"] = self.script("approved")
        synthetic.SCRIPTS["beta"] = self.script("blocked", "low")
        run_id = self.create([self.task("a")], max_same_provider_review_rounds=1)
        self.engine.run_loop(run_id, max_ticks=20)
        record = self.engine.load(run_id)
        self.assertTrue(record["nodes"]["a"]["review"]["reviewers"][0]["independent_provider"])
        self.assertEqual(record["nodes"]["a"]["review"].get("follow_ups", []), [])
        self.assertTrue(any(n["role"] == "repairer" for n in record["nodes"].values()))

    def test_status_summary_reports_independent_review(self):
        synthetic.SCRIPTS["alpha"] = self.script()
        synthetic.SCRIPTS["beta"] = self.script()
        run_id = self.create([self.task("a")])
        final = self.engine.run_loop(run_id, max_ticks=60)
        self.assertEqual(final["state"], "COMPLETE", final["state_reason"])
        task_view = next(node for node in self.engine.summary(self.engine.load(run_id))["nodes"] if node["id"] == "a")
        self.assertEqual(task_view["review_summary"]["rounds"], 1)
        self.assertEqual(len(task_view["review_summary"]["reviews"]), 1)
        self.assertTrue(task_view["review_summary"]["reviews"][0]["independent"])

    def test_node_view_accepts_old_review_shape(self):
        synthetic.SCRIPTS["alpha"] = self.script()
        run_id = self.create([self.task("a")])
        node = self.engine.load(run_id)["nodes"]["a"]
        node["review"] = {"rounds": 0, "findings": [], "reviewers": []}
        view = _node_view(node)
        self.assertEqual(view["review_summary"], {
            "rounds": 0, "reviews": [], "same_provider_rounds": 0, "follow_ups": 0,
        })
