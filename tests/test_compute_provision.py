import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import budget, provision  # noqa: E402
from agent_os.orchestrator.compute_fake import FakeProvider  # noqa: E402


class Clock:
    def __init__(self, now=1_000_000.0):
        self.now = now

    def __call__(self):
        return self.now


class HookProvider(FakeProvider):
    def __init__(self, *args, on_launch=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_launch = on_launch

    def launch(self, spec):
        if self.on_launch:
            self.on_launch()
        return super().launch(spec)


def request(**over):
    base = {"provider": "fake", "gpu": "A100", "hourly_usd": 2.0, "estimate": {"low": 0.5, "expected": 1.0, "high": 2.0}}
    base.update(over)
    return base


class ProvisionTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name) / "orch"
        self.bhome = Path(tmp.name) / "budget"
        self.bhome.mkdir()
        self.clock = Clock()
        self.provider = FakeProvider(hourly_usd=2.0, clock=self.clock)

    def kw(self, **over):
        return {"provider": self.provider, "home": self.home, "budget_home": self.bhome, "clock": self.clock, **over}

    def ledger(self):
        path = self.bhome / "spend.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def test_blocked_without_budget(self):
        job = provision.provision(request(), **self.kw())
        self.assertEqual(job["state"], "blocked")
        self.assertTrue(job["reason"])
        self.assertEqual(self.ledger(), [])
        self.assertEqual(self.provider.launches, 0)

    def test_blocked_when_high_exceeds_cap(self):
        budget.set_budget(100, 1.5, home=self.bhome)
        job = provision.provision(request(), **self.kw())
        self.assertEqual(job["state"], "blocked")
        self.assertIn("job_hard_cap", job["reason"])
        self.assertEqual(self.ledger(), [])
        self.assertEqual(self.provider.launches, 0)

    def test_reservation_written_before_launch(self):
        budget.set_budget(10, 5, home=self.bhome)
        seen = []
        self.provider = HookProvider(hourly_usd=2.0, clock=self.clock,
                                     on_launch=lambda: seen.append([e["kind"] for e in self.ledger()]))
        job = provision.provision(request(), **self.kw())
        self.assertEqual(seen, [["reserved"]])
        self.assertEqual(job["state"], "running")
        states = [h["to"] for h in job["history"]]
        self.assertEqual(states, ["requested", "reserved", "launching", "running"])

    def test_auto_stop_derived_from_cap(self):
        budget.set_budget(10, 5, home=self.bhome)
        job = provision.provision(request(), **self.kw())
        self.assertEqual(job["max_runtime_seconds"], 3600)  # 2.0 usd / 2.0 per hour
        self.assertEqual(self.provider.instances[job["instance_id"]]["max_runtime_seconds"], 3600)
        self.clock.now += 3601
        job = provision.status(job["job_id"], **self.kw())
        self.assertEqual(job["state"], "stopped")
        self.assertEqual(job["history"][-1]["reason"], "auto_stop")
        self.assertAlmostEqual(job["cost_usd"], 2.0)

    def test_max_runtime_request_tightens(self):
        budget.set_budget(10, 5, home=self.bhome)
        job = provision.provision(request(max_runtime_seconds=600), **self.kw())
        self.assertEqual(job["max_runtime_seconds"], 600)

    def test_idempotent_reprovision(self):
        budget.set_budget(10, 5, home=self.bhome)
        first = provision.provision(request(), **self.kw())
        second = provision.provision(request(), **self.kw())
        self.assertEqual(first["job_id"], second["job_id"])
        self.assertEqual(self.provider.launches, 1)
        self.assertEqual([e["kind"] for e in self.ledger()], ["reserved"])
        self.assertEqual(second["state"], "running")

    def test_explicit_job_id_conflict(self):
        budget.set_budget(10, 5, home=self.bhome)
        provision.provision(request(job_id="job-one"), **self.kw())
        with self.assertRaises(ValueError):
            provision.provision(request(job_id="job-one", gpu="H100"), **self.kw())
        self.assertEqual(self.provider.launches, 1)

    def test_resume_from_reserved(self):
        budget.set_budget(10, 5, home=self.bhome)
        job = provision.provision(request(job_id="job-resume"), **self.kw(provider=HookProvider(hourly_usd=2.0, clock=self.clock)))
        # rewind the persisted record to a crash right after the reservation
        path = self.home / "compute-jobs" / "job-resume.json"
        record = json.loads(path.read_text())
        record.update({"state": "reserved", "instance_id": None, "auto_stop_at": None, "auto_stop_epoch": None})
        path.write_text(json.dumps(record))
        fresh = FakeProvider(hourly_usd=2.0, clock=self.clock)
        resumed = provision.provision(request(job_id="job-resume"), **self.kw(provider=fresh))
        self.assertEqual(resumed["state"], "running")
        self.assertEqual(fresh.launches, 1)
        self.assertEqual([e["kind"] for e in self.ledger()], ["reserved"])
        self.assertEqual(job["state"], "running")

    def test_launch_failure_stays_launching_then_resumes_on_same_instance(self):
        budget.set_budget(10, 5, home=self.bhome)
        self.provider.fail_launch = True
        job = provision.provision(request(), **self.kw())
        self.assertEqual(job["state"], "launching")
        self.assertEqual([e["kind"] for e in self.ledger()], ["reserved"])
        self.provider.fail_launch = False
        job = provision.provision(request(), **self.kw())
        self.assertEqual(job["state"], "running")
        self.assertEqual(self.provider.launches, 1)

    def test_raw_key_rejected(self):
        budget.set_budget(10, 5, home=self.bhome)
        with self.assertRaises(ValueError):
            provision.provision(request(api_key="sk-live-123"), **self.kw())
        with self.assertRaises(ValueError):
            provision.provision(request(secret_ref="sk-live-123"), **self.kw())
        self.assertFalse((self.home / "compute-jobs").exists())
        self.assertEqual(self.provider.launches, 0)

    def test_secret_ref_stored_as_reference(self):
        budget.set_budget(10, 5, home=self.bhome)
        job = provision.provision(request(secret_ref="secrets://fake/default"), **self.kw())
        self.assertEqual(job["secret_ref"], "secrets://fake/default")

    def test_non_fake_provider_blocked(self):
        budget.set_budget(10, 5, home=self.bhome)
        job = provision.provision(request(provider="runpod"), **self.kw())
        self.assertEqual(job["state"], "blocked")
        self.assertEqual(job["gate"], "approval_required")
        self.assertEqual(self.provider.launches, 0)
        self.assertEqual(self.ledger(), [])

    def test_blocked_retry_after_approval(self):
        job = provision.provision(request(), **self.kw())
        self.assertEqual(job["state"], "blocked")
        budget.set_budget(10, 5, home=self.bhome)
        job = provision.provision(request(), **self.kw())
        self.assertEqual(job["state"], "running")
        self.assertIn(("blocked", "requested", "retry"), [(h["from"], h["to"], h["reason"]) for h in job["history"]])

    def test_full_lifecycle_reconcile(self):
        budget.set_budget(10, 5, home=self.bhome)
        job = provision.provision(request(), **self.kw())
        self.clock.now += 1800
        job = provision.status(job["job_id"], **self.kw())
        self.assertAlmostEqual(job["cost_usd"], 1.0)
        job = provision.destroy(job["job_id"], **self.kw())
        self.assertEqual(job["state"], "destroyed")
        job = provision.reconcile(job["job_id"], **self.kw())
        self.assertEqual(job["state"], "reconciled")
        self.assertTrue(job["reconcile"]["within_band"])
        self.assertAlmostEqual(budget.spent(self.bhome), 1.0)
        again = provision.reconcile(job["job_id"], **self.kw())
        self.assertEqual(again["state"], "reconciled")
        self.assertAlmostEqual(budget.spent(self.bhome), 1.0)

    def test_destroy_reserved_releases_on_reconcile(self):
        budget.set_budget(10, 5, home=self.bhome)
        before = budget.remaining(self.bhome)
        provision.provision(request(job_id="job-cancel"), **self.kw())
        path = self.home / "compute-jobs" / "job-cancel.json"
        record = json.loads(path.read_text())
        record.update({"state": "reserved", "instance_id": None})
        path.write_text(json.dumps(record))
        self.assertEqual(provision.stop("job-cancel", **self.kw())["state"], "failed")
        job = provision.reconcile("job-cancel", **self.kw())
        self.assertEqual(job["reconcile"]["actual_usd"], 0.0)
        self.assertEqual(budget.remaining(self.bhome), before)

    def test_stop_destroy_reconcile_lifecycle_and_idempotence(self):
        budget.set_budget(10, 5, home=self.bhome)
        job = provision.provision(request(), **self.kw())
        jid = job["job_id"]
        self.clock.now += 1800
        self.assertEqual(provision.status(jid, **self.kw())["state"], "running")
        job = provision.stop(jid, **self.kw())
        self.assertEqual(job["state"], "stopped")
        self.assertEqual(provision.stop(jid, **self.kw())["history"], job["history"])
        job = provision.destroy(jid, **self.kw())
        self.assertEqual(job["state"], "destroyed")
        self.assertEqual(provision.destroy(jid, **self.kw())["history"], job["history"])
        job = provision.reconcile(jid, **self.kw())
        self.assertEqual(job["state"], "reconciled")
        self.assertAlmostEqual(budget.spent(self.bhome), 1.0)
        self.assertEqual(job["reconcile"]["estimate_high"], 2.0)
        self.assertAlmostEqual(job["reconcile"]["delta_usd"], -1.0)
        lines = len(self.ledger())
        again = provision.reconcile(jid, **self.kw())
        self.assertEqual(again["state"], "reconciled")
        self.assertEqual(len(self.ledger()), lines)
        self.assertEqual(budget.open_reservation(jid, self.bhome), 0)
        self.assertEqual([j["job_id"] for j in provision.list_jobs(self.home)], [jid])
        self.assertEqual(provision.stop(jid, **self.kw())["state"], "reconciled")

    def test_reconcile_before_stop_raises(self):
        budget.set_budget(10, 5, home=self.bhome)
        job = provision.provision(request(), **self.kw())
        with self.assertRaises(ValueError):
            provision.reconcile(job["job_id"], **self.kw())

    def test_auto_stop_then_reconcile(self):
        budget.set_budget(10, 5, home=self.bhome)
        job = provision.provision(request(), **self.kw())
        self.clock.now += 3601
        job = provision.status(job["job_id"], **self.kw())
        self.assertEqual(job["state"], "stopped")
        job = provision.reconcile(job["job_id"], **self.kw())
        self.assertEqual(job["state"], "reconciled")
        self.assertAlmostEqual(budget.spent(self.bhome), 2.0)
        self.assertEqual(budget.open_reservation(job["job_id"], self.bhome), 0)

    def test_list_jobs_empty(self):
        self.assertEqual(provision.list_jobs(self.home), [])

    def test_illegal_transition(self):
        with self.assertRaises(ValueError):
            provision._transition({"state": "requested", "history": []}, "running")

    def test_unknown_job(self):
        with self.assertRaises(KeyError):
            provision.status("nope-123", **self.kw())


if __name__ == "__main__":
    unittest.main()
