"""Tests for FakeProvider (IMP-0015 slice 2): cost accrual, autostop, state lifecycle."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator.compute_fake import FakeProvider


class ManualClock:
    """Manual clock for testing: advance time deterministically."""

    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class FakeProviderTests(unittest.TestCase):
    """Test FakeProvider in-memory lifecycle."""

    def setUp(self) -> None:
        self.clock = ManualClock(start=1000.0)
        self.provider = FakeProvider(hourly_usd=1.0, clock=self.clock, fail_launch=False)

    def test_class_name_attribute(self) -> None:
        self.assertEqual(FakeProvider.name, "fake")

    def test_launch_returns_instance_id(self) -> None:
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0, "max_runtime_seconds": 3600}
        result = self.provider.launch(spec)
        self.assertIn("instance_id", result)
        self.assertEqual(result["instance_id"], "fake-1")
        self.assertEqual(self.provider.launches, 1)

    def test_launch_same_name_returns_existing_instance(self) -> None:
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0}
        result1 = self.provider.launch(spec)
        result2 = self.provider.launch(spec)
        self.assertEqual(result1["instance_id"], result2["instance_id"])
        self.assertEqual(self.provider.launches, 1)
        self.assertEqual(len(self.provider.instances), 1)

    def test_launch_different_specs_creates_different_instances(self) -> None:
        spec1 = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0}
        spec2 = {"name": "job-2", "gpu": "A100", "hourly_usd": 1.0}
        self.provider.launch(spec1)
        self.provider.launch(spec2)
        self.assertEqual(self.provider.launches, 2)

    def test_fail_launch_creates_instance_then_raises(self) -> None:
        provider = FakeProvider(hourly_usd=1.0, clock=self.clock, fail_launch=True)
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0}
        with self.assertRaises(RuntimeError) as cm:
            provider.launch(spec)
        self.assertIn("launch failure", str(cm.exception))
        self.assertEqual(provider.launches, 1)
        self.assertEqual(provider.lookup("job-1"), "fake-1")

    def test_relaunch_after_raised_launch_returns_created_instance(self) -> None:
        provider = FakeProvider(hourly_usd=1.0, clock=self.clock, fail_launch=True)
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0}
        with self.assertRaises(RuntimeError):
            provider.launch(spec)
        result = provider.launch(spec)
        self.assertEqual(result["instance_id"], "fake-1")
        self.assertEqual(provider.launches, 1)
        self.assertEqual(len(provider.instances), 1)

    def test_lookup_unknown_name_returns_none(self) -> None:
        self.assertIsNone(self.provider.lookup("no-such-job"))
        self.provider.launch({"name": "job-1", "gpu": "A100", "hourly_usd": 1.0})
        self.assertIsNone(self.provider.lookup("no-such-job"))

    def test_cost_uses_per_instance_rate(self) -> None:
        cheap = self.provider.launch({"name": "cheap", "gpu": "A100", "hourly_usd": 1.0})["instance_id"]
        dear = self.provider.launch({"name": "dear", "gpu": "H100", "hourly_usd": 4.0})["instance_id"]
        self.provider.hourly_usd = 9.0
        self.clock.advance(1800.0)
        cheap_cost = self.provider.poll(cheap)["cost_usd"]
        dear_cost = self.provider.poll(dear)["cost_usd"]
        self.assertAlmostEqual(cheap_cost, 0.5)
        self.assertAlmostEqual(dear_cost, 4 * cheap_cost)

    def test_poll_unknown_instance_raises_key_error(self) -> None:
        with self.assertRaises(KeyError):
            self.provider.poll("fake-999")

    def test_poll_running_accrues_cost(self) -> None:
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0}
        result = self.provider.launch(spec)
        instance_id = result["instance_id"]

        self.clock.advance(3600.0)
        status = self.provider.poll(instance_id)

        self.assertEqual(status["state"], "running")
        self.assertAlmostEqual(status["runtime_seconds"], 3600.0)
        self.assertAlmostEqual(status["cost_usd"], 1.0)

    def test_cost_with_different_hourly_rate(self) -> None:
        provider = FakeProvider(hourly_usd=2.5, clock=self.clock)
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 2.5}
        result = provider.launch(spec)
        instance_id = result["instance_id"]

        self.clock.advance(1800.0)
        status = provider.poll(instance_id)

        self.assertAlmostEqual(status["runtime_seconds"], 1800.0)
        self.assertAlmostEqual(status["cost_usd"], 1.25)

    def test_stop_freezes_runtime(self) -> None:
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0}
        result = self.provider.launch(spec)
        instance_id = result["instance_id"]

        self.clock.advance(1800.0)
        self.provider.stop(instance_id)

        self.clock.advance(3600.0)
        status = self.provider.poll(instance_id)

        self.assertEqual(status["state"], "stopped")
        self.assertAlmostEqual(status["runtime_seconds"], 1800.0)
        self.assertAlmostEqual(status["cost_usd"], 0.5)

    def test_stop_idempotent(self) -> None:
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0}
        result = self.provider.launch(spec)
        instance_id = result["instance_id"]

        self.clock.advance(1000.0)
        self.provider.stop(instance_id)
        cost1 = self.provider.poll(instance_id)["cost_usd"]

        self.clock.advance(1000.0)
        self.provider.stop(instance_id)
        cost2 = self.provider.poll(instance_id)["cost_usd"]

        self.assertEqual(cost1, cost2)

    def test_stop_unknown_instance_raises_key_error(self) -> None:
        with self.assertRaises(KeyError):
            self.provider.stop("fake-999")

    def test_terminate_idempotent(self) -> None:
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0}
        result = self.provider.launch(spec)
        instance_id = result["instance_id"]

        self.clock.advance(1000.0)
        self.provider.terminate(instance_id)
        status1 = self.provider.poll(instance_id)

        self.clock.advance(1000.0)
        self.provider.terminate(instance_id)
        status2 = self.provider.poll(instance_id)

        self.assertEqual(status1["state"], "terminated")
        self.assertEqual(status2["state"], "terminated")
        self.assertEqual(status1["cost_usd"], status2["cost_usd"])

    def test_terminate_unknown_instance_raises_key_error(self) -> None:
        with self.assertRaises(KeyError):
            self.provider.terminate("fake-999")

    def test_max_runtime_seconds_autostop(self) -> None:
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0, "max_runtime_seconds": 3600}
        result = self.provider.launch(spec)
        instance_id = result["instance_id"]

        self.clock.advance(3600.0)
        status = self.provider.poll(instance_id)

        self.assertEqual(status["state"], "stopped")
        self.assertAlmostEqual(status["runtime_seconds"], 3600.0)

    def test_max_runtime_seconds_exceeding_cap(self) -> None:
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0, "max_runtime_seconds": 3600}
        result = self.provider.launch(spec)
        instance_id = result["instance_id"]

        self.clock.advance(5400.0)
        status = self.provider.poll(instance_id)

        self.assertEqual(status["state"], "stopped")
        self.assertAlmostEqual(status["runtime_seconds"], 3600.0)
        self.assertAlmostEqual(status["cost_usd"], 1.0)

    def test_stop_after_deadline_without_poll(self) -> None:
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0, "max_runtime_seconds": 3600}
        result = self.provider.launch(spec)
        instance_id = result["instance_id"]

        self.clock.advance(5400.0)
        self.provider.stop(instance_id)

        status = self.provider.poll(instance_id)
        self.assertEqual(status["state"], "stopped")
        self.assertAlmostEqual(status["runtime_seconds"], 3600.0)
        self.assertAlmostEqual(status["cost_usd"], 1.0)

    def test_terminate_after_deadline_without_poll(self) -> None:
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0, "max_runtime_seconds": 3600}
        result = self.provider.launch(spec)
        instance_id = result["instance_id"]

        self.clock.advance(5400.0)
        self.provider.terminate(instance_id)

        status = self.provider.poll(instance_id)
        self.assertEqual(status["state"], "terminated")
        self.assertAlmostEqual(status["runtime_seconds"], 3600.0)
        self.assertAlmostEqual(status["cost_usd"], 1.0)

class FakeProviderFullLifecycleTests(unittest.TestCase):
    """Test full lifecycle: launch, run, stop, terminate."""

    def setUp(self) -> None:
        self.clock = ManualClock(start=0.0)
        self.provider = FakeProvider(hourly_usd=1.0, clock=self.clock)

    def test_full_lifecycle_with_stop(self) -> None:
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0}
        result = self.provider.launch(spec)
        instance_id = result["instance_id"]
        self.assertEqual(self.provider.poll(instance_id)["state"], "running")

        self.clock.advance(1800.0)
        self.provider.stop(instance_id)
        status = self.provider.poll(instance_id)
        self.assertEqual(status["state"], "stopped")
        self.assertAlmostEqual(status["cost_usd"], 0.5)

    def test_full_lifecycle_with_terminate(self) -> None:
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0}
        result = self.provider.launch(spec)
        instance_id = result["instance_id"]

        self.clock.advance(1800.0)
        self.provider.terminate(instance_id)
        status = self.provider.poll(instance_id)
        self.assertEqual(status["state"], "terminated")
        self.assertAlmostEqual(status["cost_usd"], 0.5)

    def test_stop_then_terminate(self) -> None:
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0}
        result = self.provider.launch(spec)
        instance_id = result["instance_id"]

        self.clock.advance(1000.0)
        self.provider.stop(instance_id)
        self.assertEqual(self.provider.poll(instance_id)["state"], "stopped")
        self.assertAlmostEqual(self.provider.poll(instance_id)["cost_usd"], 1000.0 / 3600.0)

        self.clock.advance(500.0)
        self.provider.terminate(instance_id)
        status = self.provider.poll(instance_id)
        self.assertEqual(status["state"], "terminated")
        self.assertAlmostEqual(status["cost_usd"], 1000.0 / 3600.0)

    def test_multiple_jobs_independent(self) -> None:
        spec1 = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0}
        spec2 = {"name": "job-2", "gpu": "A100", "hourly_usd": 1.0}

        result1 = self.provider.launch(spec1)
        instance_id1 = result1["instance_id"]

        self.clock.advance(1000.0)

        result2 = self.provider.launch(spec2)
        instance_id2 = result2["instance_id"]

        self.clock.advance(1000.0)
        self.provider.stop(instance_id1)

        self.clock.advance(1000.0)
        status1 = self.provider.poll(instance_id1)
        status2 = self.provider.poll(instance_id2)

        self.assertAlmostEqual(status1["cost_usd"], 2000.0 / 3600.0)
        self.assertAlmostEqual(status2["cost_usd"], 2000.0 / 3600.0)

    def test_stop_at_clock_zero(self) -> None:
        clock = ManualClock(0.0)
        provider = FakeProvider(hourly_usd=1.0, clock=clock)
        spec = {"name": "job-zero", "gpu": "A100", "hourly_usd": 1.0}
        result = provider.launch(spec)
        instance_id = result["instance_id"]

        provider.stop(instance_id)
        status = provider.poll(instance_id)
        self.assertEqual(status["state"], "stopped")
        self.assertAlmostEqual(status["runtime_seconds"], 0.0)

        clock.advance(100.0)
        provider.terminate(instance_id)
        status = provider.poll(instance_id)
        self.assertEqual(status["state"], "terminated")
        self.assertAlmostEqual(status["runtime_seconds"], 0.0)


class FakeProviderPersistenceTests(unittest.TestCase):
    """Test state_path persistence across FakeProvider objects."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state_path = Path(self.tmp.name) / "compute-providers" / "fake.json"
        self.clock = ManualClock(start=1000.0)

    def test_new_provider_finds_persisted_instance_with_its_rate(self) -> None:
        first = FakeProvider(hourly_usd=1.0, clock=self.clock, state_path=self.state_path)
        instance_id = first.launch({"name": "job-1", "gpu": "H100", "hourly_usd": 4.0})["instance_id"]
        self.assertTrue(self.state_path.exists())

        second = FakeProvider(hourly_usd=9.0, clock=self.clock, state_path=self.state_path)
        self.assertEqual(second.lookup("job-1"), instance_id)
        self.clock.advance(1800.0)
        status = second.poll(instance_id)
        self.assertEqual(status["state"], "running")
        self.assertAlmostEqual(status["cost_usd"], 2.0)

    def test_raised_launch_persists_instance_for_new_provider(self) -> None:
        failing = FakeProvider(clock=self.clock, fail_launch=True, state_path=self.state_path)
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0}
        with self.assertRaises(RuntimeError):
            failing.launch(spec)
        self.assertTrue(self.state_path.exists())

        fresh = FakeProvider(clock=self.clock, state_path=self.state_path)
        self.assertEqual(fresh.lookup("job-1"), "fake-1")
        self.assertEqual(fresh.launch(spec)["instance_id"], "fake-1")
        self.assertEqual(fresh.launches, 1)
        self.assertEqual(len(fresh.instances), 1)

    def test_stop_persists_across_new_provider(self) -> None:
        first = FakeProvider(clock=self.clock, state_path=self.state_path)
        instance_id = first.launch({"name": "job-1", "gpu": "A100", "hourly_usd": 1.0})["instance_id"]
        self.clock.advance(1800.0)
        first.stop(instance_id)

        self.clock.advance(3600.0)
        second = FakeProvider(clock=self.clock, state_path=self.state_path)
        status = second.poll(instance_id)
        self.assertEqual(status["state"], "stopped")
        self.assertAlmostEqual(status["cost_usd"], 0.5)

    def test_poll_autostop_persists_across_new_provider(self) -> None:
        first = FakeProvider(clock=self.clock, state_path=self.state_path)
        instance_id = first.launch(
            {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0, "max_runtime_seconds": 3600}
        )["instance_id"]
        self.clock.advance(5400.0)
        self.assertEqual(first.poll(instance_id)["state"], "stopped")

        data = json.loads(self.state_path.read_text(encoding="utf-8"))
        self.assertEqual(data["instances"][instance_id]["state"], "stopped")
        self.assertEqual(data["instances"][instance_id]["stopped_at"], 4600.0)

    def test_no_file_written_without_state_path(self) -> None:
        provider = FakeProvider(clock=self.clock)
        instance_id = provider.launch({"name": "job-1", "gpu": "A100", "hourly_usd": 1.0})["instance_id"]
        provider.stop(instance_id)
        provider.terminate(instance_id)
        self.assertIsNone(provider.state_path)
        self.assertEqual(list(Path(self.tmp.name).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
