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

    def test_launch_returns_instance_id(self) -> None:
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0, "max_runtime_seconds": 3600}
        result = self.provider.launch(spec)
        self.assertIn("instance_id", result)
        self.assertEqual(result["instance_id"], "fake-1")
        self.assertEqual(self.provider.launches, 1)

    def test_launch_idempotent_by_name(self) -> None:
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0}
        result1 = self.provider.launch(spec)
        result2 = self.provider.launch(spec)
        self.assertEqual(result1["instance_id"], result2["instance_id"])
        self.assertEqual(self.provider.launches, 1)

    def test_launch_increments_counter(self) -> None:
        spec1 = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0}
        spec2 = {"name": "job-2", "gpu": "A100", "hourly_usd": 1.0}
        self.provider.launch(spec1)
        self.provider.launch(spec2)
        self.assertEqual(self.provider.launches, 2)

    def test_launch_raises_when_fail_launch_set(self) -> None:
        provider = FakeProvider(hourly_usd=1.0, clock=self.clock, fail_launch=True)
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0}
        with self.assertRaises(RuntimeError) as cm:
            provider.launch(spec)
        self.assertIn("launch failure", str(cm.exception))

    def test_launch_creates_instance_even_on_fail(self) -> None:
        provider = FakeProvider(hourly_usd=1.0, clock=self.clock, fail_launch=True)
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0}
        with self.assertRaises(RuntimeError):
            provider.launch(spec)
        self.assertEqual(provider.launches, 1)

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

    def test_double_stop_after_terminate(self) -> None:
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0}
        result = self.provider.launch(spec)
        instance_id = result["instance_id"]

        self.clock.advance(1000.0)
        self.provider.terminate(instance_id)
        status = self.provider.poll(instance_id)
        self.assertEqual(status["state"], "terminated")

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

    def test_state_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "fake.json"
            provider = FakeProvider(hourly_usd=2.0, clock=self.clock, state_path=state_path)

            spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 2.0}
            result = provider.launch(spec)
            instance_id = result["instance_id"]
            self.clock.advance(1000.0)
            provider.poll(instance_id)

            self.assertTrue(state_path.exists())
            data = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertIn(instance_id, data["instances"])
            self.assertEqual(data["launches"], 1)

    def test_state_reload_after_launch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "fake.json"
            clock1 = ManualClock(start=1000.0)
            provider1 = FakeProvider(hourly_usd=1.0, clock=clock1, state_path=state_path)

            spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0}
            result1 = provider1.launch(spec)
            instance_id = result1["instance_id"]

            clock2 = ManualClock(start=1000.0)
            provider2 = FakeProvider(hourly_usd=1.0, clock=clock2, state_path=state_path)
            result2 = provider2.launch(spec)

            self.assertEqual(result1["instance_id"], result2["instance_id"])
            self.assertEqual(provider2.launches, 1)


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

    def test_fail_launch_then_recover(self) -> None:
        provider = FakeProvider(hourly_usd=1.0, clock=self.clock, fail_launch=True)
        spec = {"name": "job-1", "gpu": "A100", "hourly_usd": 1.0}

        with self.assertRaises(RuntimeError):
            provider.launch(spec)

        self.assertEqual(provider.launches, 1)
        provider.fail_launch = False
        result = provider.launch(spec)
        self.assertEqual(result["instance_id"], "fake-1")
        self.assertEqual(provider.launches, 1)

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


if __name__ == "__main__":
    unittest.main()
