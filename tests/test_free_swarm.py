import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import free_swarm

FREE = {"prompt": "0", "completion": "0"}
TRAINS_FALSE = {"trains_on_prompts": False, "source": "policy:test", "verified_at": "2026-10-01T00:00:00Z"}
NOW = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)


def model(slug):
    return {"slug": slug, "revision": f"{slug}-r1", "context_length": 65536, "supports_tools": True,
            "supports_structured_output": True, "pricing": dict(FREE), "data_policy": dict(TRAINS_FALSE)}


CATALOG = {"snapshot_id": "FCS-test", "models": [model("org/a:free"), model("org/b:free")]}
SPECS = [{"task_family": "unit_test_generation", "model": s, "revision": f"{s}-r1", "n": 30,
          "wilson95": [0.7, 0.9], "status": "proven"} for s in ("org/a:free", "org/b:free")]


class Gov:
    def __init__(self, daily=40, minute=10, expiring=None):
        self.daily, self.minute = daily, minute
        self.expiring = daily if expiring is None else expiring

    def remaining(self, now=None):
        return {"daily_left": self.daily, "minute_left": self.minute, "reset_at": "2026-10-02T00:00:00Z"}

    def can_spend(self, model, retry=0):
        return True, "ok"

    def expiring_capacity(self, now=None):
        return self.expiring


def task(**extra):
    base = {"id": "t1", "task_family": "unit_test_generation", "role": "test_author", "effort": "low",
            "validators": ["python -m unittest tests.test_x"], "scope": ["tests/test_x.py"],
            "sensitivity": "internal", "capability_class": "fast", "estimated_validator_cost": 0.01}
    base.update(extra)
    return base


def fanout(item=None, *, n=5, gov=None, conc=3):
    return free_swarm.plan_fanout(item or task(), n=n, governor=gov or Gov(), max_concurrency=conc,
                                  catalog=CATALOG, specializations=SPECS)


class FanoutTest(unittest.TestCase):
    def test_no_fanout_for_expensive_validation(self):
        plan = fanout(task(estimated_validator_cost=5.0))
        self.assertEqual(list(plan), [])
        self.assertIn("expensive", plan.reason)

    def test_no_fanout_for_unplain_or_unknown_validation(self):
        self.assertEqual(list(fanout(task(validators=["make deploy"]))), [])
        item = task()
        del item["estimated_validator_cost"]
        self.assertIn("unknown", fanout(item).reason)

    def test_ineligible_task_has_no_fanout(self):
        plan = fanout(task(sensitivity="private"))
        self.assertEqual(list(plan), [])
        self.assertIn("not free-eligible", plan.reason)

    def test_capped_by_concurrency(self):
        plan = fanout(n=5, conc=2)
        self.assertEqual(len(plan), 2)
        self.assertTrue(all(w["disposable"] and w["scope"] == ["tests/test_x.py"] for w in plan))

    def test_capped_by_quota(self):
        self.assertEqual(len(fanout(n=5, conc=4, gov=Gov(daily=1))), 1)
        plan = fanout(n=5, gov=Gov(daily=0))
        self.assertEqual(list(plan), [])
        self.assertIn("no capacity", plan.reason)


class AggregateTest(unittest.TestCase):
    def test_picks_first_validator_passing_result(self):
        results = [{"id": 1, "ok": False}, {"id": 2, "ok": True}, {"id": 3, "ok": True}]
        out = free_swarm.aggregate(results, lambda r: {"passed": r["ok"]})
        self.assertTrue(out["accepted"])
        self.assertEqual(out["result"]["id"], 2)

    def test_no_passing_result(self):
        out = free_swarm.aggregate([{"ok": False}], lambda r: r["ok"])
        self.assertFalse(out["accepted"])
        self.assertIsNone(out["result"])


class BackfillTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def queue(self, count, kind="tests"):
        return [{"id": f"{kind}-{i}", "kind": kind} for i in range(count)]

    def test_limited_to_expiring_capacity(self):
        plan = free_swarm.plan_backfill(self.queue(20), Gov(daily=40, expiring=2), NOW, home=self.home, batch_size=1)
        self.assertEqual(plan["requests"], 2)
        self.assertEqual(len(plan["batches"]), 2)

    def test_batches_compatible_microtasks_and_skips_useless_kinds(self):
        queue = self.queue(5) + [{"id": "x", "kind": "filler"}]
        plan = free_swarm.plan_backfill(queue, Gov(expiring=10), NOW, home=self.home, batch_size=4)
        self.assertEqual([len(b["item_ids"]) for b in plan["batches"]], [4, 1])
        self.assertNotIn("x", [i for b in plan["batches"] for i in b["item_ids"]])

    def test_zero_expiring_capacity_plans_nothing(self):
        plan = free_swarm.plan_backfill(self.queue(3), Gov(expiring=0), NOW, home=self.home)
        self.assertEqual(plan["requests"], 0)

    def test_resume_skips_done_items(self):
        queue = self.queue(4)
        free_swarm.plan_backfill(queue, Gov(expiring=10), NOW, home=self.home, batch_size=1)
        free_swarm.record_done(["tests-0", "tests-1"], home=self.home)
        self.assertEqual(free_swarm.load_checkpoint(self.home)["done"], ["tests-0", "tests-1"])
        plan = free_swarm.plan_backfill(queue, Gov(expiring=10), NOW, home=self.home, batch_size=1)
        ids = [i for b in plan["batches"] for i in b["item_ids"]]
        self.assertEqual(ids, ["tests-2", "tests-3"])
        self.assertEqual(plan["skipped"], ["tests-0", "tests-1"])

    def test_empty_queue_makes_no_calls(self):
        plan = free_swarm.plan_backfill([], Gov(expiring=10), NOW, home=self.home)
        self.assertEqual((plan["batches"], plan["requests"]), ([], 0))
        self.assertFalse(free_swarm.checkpoint_path(self.home).exists())


if __name__ == "__main__":
    unittest.main()
