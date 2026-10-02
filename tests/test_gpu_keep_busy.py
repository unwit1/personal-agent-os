import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from agent_os.orchestrator import free_swarm, gpu_keep_busy as kb


def node(nid, role, state="READY", cls="fast"):
    return {"id": nid, "role": role, "state": state, "capability_class": cls}


ALL_ROLES = {"reviewer", "implementer", "test_author", "repairer"}


class UsefulWorkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.queue = [{"id": "b1", "kind": "docs"}, {"id": "b2", "kind": "tests"}, {"id": "b3", "kind": "bogus"}]

    def run_work(self, records, **kw):
        kw.setdefault("roles", ALL_ROLES)
        return kb.useful_work(records, self.queue, home=self.home, **kw)

    def test_priority_review_then_worker_then_backfill(self):
        rec = {"run_id": "r", "nodes": [node("w", "implementer"), node("v", "reviewer", "PENDING")]}
        self.assertEqual(self.run_work([rec])["kind"], "review")
        rec = {"run_id": "r", "nodes": [node("w", "implementer"), node("v", "reviewer", "PASSED")]}
        out = self.run_work([rec])
        self.assertEqual((out["kind"], out["items"][0]["node_id"]), ("worker", "w"))
        rec = {"run_id": "r", "nodes": [node("v", "reviewer", "RUNNING")]}
        out = self.run_work([rec])
        self.assertEqual((out["kind"], [i["id"] for i in out["items"]]), ("backfill", ["b1", "b2"]))

    def test_role_and_class_filtering(self):
        rec = {"run_id": "r", "nodes": [node("v", "reviewer"), node("w", "implementer", cls="frontier")]}
        self.assertEqual(self.run_work([rec], roles={"implementer"})["kind"], "backfill")
        self.assertEqual(self.run_work([rec], roles={"implementer"}, classes={"frontier"})["kind"], "worker")
        self.assertEqual(self.run_work([rec], roles={"planner"})["kind"], "backfill")

    def test_terminal_run_ignored(self):
        rec = {"run_id": "r", "state": "COMPLETE", "nodes": [node("v", "reviewer")]}
        self.assertEqual(self.run_work([rec])["kind"], "backfill")

    def test_non_dispatching_run_states_ignored(self):
        for st in ("FAILED", "PAUSED", "BLOCKED", "APPROVAL_REQUIRED"):
            rec = {"run_id": "r", "state": st, "nodes": [node("v", "reviewer")]}
            self.assertEqual(self.run_work([rec])["kind"], "backfill", st)
        rec = {"run_id": "r", "state": "RUNNING", "nodes": [node("v", "reviewer")]}
        self.assertEqual(self.run_work([rec])["kind"], "review")

    def test_dispatchable_node_states(self):
        for st in ("RUNNABLE", "FAILED_RETRYABLE"):
            rec = {"run_id": "r", "nodes": [node("w", "implementer", st)]}
            self.assertEqual(self.run_work([rec])["kind"], "worker", st)
        rec = {"run_id": "r", "nodes": [node("v", "reviewer", "WAITING_FOR_REVIEW")]}
        self.assertEqual(self.run_work([rec])["kind"], "review")
        rec = {"run_id": "r", "nodes": [node("w", "implementer", "WAITING_FOR_REVIEW")]}
        self.assertEqual(self.run_work([rec])["kind"], "backfill")

    def test_done_backfill_skipped_and_empty(self):
        free_swarm.record_done(["b1"], self.home)
        self.assertEqual([i["id"] for i in self.run_work([])["items"]], ["b2"])
        free_swarm.record_done(["b2"], self.home)
        out = self.run_work([])
        self.assertEqual((out["kind"], out["items"], out["reason"]), (None, [], "nothing useful queued"))


class PaidIdleTests(unittest.TestCase):
    def test_arithmetic(self):
        p = kb.PaidIdle()
        self.assertEqual(p.share(), 0.0)
        p.tick(True, True, 80)
        p.tick(False, True, 10)
        p.tick(False, False, 10)
        self.assertEqual((p.paid_seconds, p.idle_seconds, p.idle_with_work_seconds), (100, 20, 10))
        self.assertAlmostEqual(p.share(), 0.2)
        self.assertFalse(p.meets_target())
        self.assertTrue(p.meets_target(0.25))
        self.assertEqual(kb.DEFAULT_IDLE_TARGET, 0.15)

    def test_round_trip(self):
        p = kb.PaidIdle()
        p.tick(False, True, 7)
        q = kb.PaidIdle.from_dict(p.to_dict())
        self.assertEqual(q.to_dict(), p.to_dict())
        self.assertEqual(kb.PaidIdle.from_dict(None).to_dict()["paid_seconds"], 0.0)


if __name__ == "__main__":
    unittest.main()
