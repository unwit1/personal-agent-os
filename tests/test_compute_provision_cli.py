"""CLI tests for gated compute provisioning (IMP-0015 slice 2)."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.cli import main  # noqa: E402
from agent_os.orchestrator import budget  # noqa: E402


class CliFixture(unittest.TestCase):
    _shared_instances = {}

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tmpdir = Path(self.tmp.name)
        self.orch_home = self.tmpdir / "orch"
        self.budget_home = self.tmpdir / "budget"
        self.budget_home.mkdir()
        CliFixture._shared_instances.clear()

    def cli(self, *argv: str) -> tuple[int, object]:
        from agent_os.orchestrator import compute_fake, budget, provision

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            # Create a wrapper for FakeProvider that uses shared instances
            original_init = compute_fake.FakeProvider.__init__

            def patched_init(provider_self, hourly_usd=1.0, clock=None, fail_launch=False):
                original_init(provider_self, hourly_usd, clock, fail_launch)
                # Share instances across all FakeProvider instances by using class variable
                provider_self.instances = CliFixture._shared_instances

            # Patch budget._home to use test budget directory
            def mock_budget_home(home=None):
                return self.budget_home if home is None else Path(home)

            # Patch orchestrator_home to use test directory
            def mock_orchestrator_home():
                return str(self.orch_home)

            with mock.patch("agent_os.orchestrator.provision.orchestrator_home", side_effect=mock_orchestrator_home):
                with mock.patch("agent_os.orchestrator.budget._home", side_effect=mock_budget_home):
                    with mock.patch.object(compute_fake.FakeProvider, "__init__", patched_init):
                        code = main(list(argv))
        return code, json.loads(buffer.getvalue())


class ComputeProvisionCliTests(CliFixture):
    def test_provision_fake_succeeds_with_budget(self) -> None:
        budget.set_budget(100, 5, home=self.budget_home)
        code, job = self.cli(
            "orchestrate", "compute", "provision",
            "--provider", "fake",
            "--gpu", "A100",
            "--hourly-usd", "2.0",
            "--low-usd", "0.5",
            "--expected-usd", "1.0",
            "--high-usd", "2.0",
        )
        self.assertEqual(code, 0, job)
        self.assertEqual(job["state"], "running")
        self.assertIn("instance_id", job)
        self.assertEqual(job["provider"], "fake")
        self.assertEqual(job["gpu"], "A100")

    def test_provision_with_budget_set_at_machine_level(self) -> None:
        """Test that provision works when budget is set before CLI call."""
        # This tests that the CLI correctly passes budget info to provision()
        budget.set_budget(100, 5, home=self.budget_home)
        code, job = self.cli(
            "orchestrate", "compute", "provision",
            "--provider", "fake",
            "--gpu", "A100",
            "--hourly-usd", "2.0",
            "--low-usd", "0.5",
            "--expected-usd", "1.0",
            "--high-usd", "2.0",
        )
        self.assertEqual(code, 0, job)
        self.assertEqual(job["state"], "running")
        self.assertEqual(job["provider"], "fake")

    def test_provision_runpod_requires_approval(self) -> None:
        budget.set_budget(100, 5, home=self.budget_home)
        code, job = self.cli(
            "orchestrate", "compute", "provision",
            "--provider", "runpod",
            "--gpu", "A100",
            "--hourly-usd", "2.0",
            "--low-usd", "0.5",
            "--expected-usd", "1.0",
            "--high-usd", "2.0",
        )
        self.assertEqual(code, 0, job)
        self.assertEqual(job["state"], "blocked")
        self.assertIn("approval_required", job["reason"])
        self.assertEqual(job["gate"], "approval_required")

    def test_provision_missing_arguments(self) -> None:
        budget.set_budget(100, 5, home=self.budget_home)
        code, result = self.cli(
            "orchestrate", "compute", "provision",
            "--provider", "fake",
            "--gpu", "A100",
        )
        self.assertEqual(code, 2)
        self.assertIn("error", result)
        self.assertIn("hourly-usd", result["error"])

    def test_job_actions_require_job_id(self) -> None:
        """Test that status/stop/destroy/reconcile all require --job-id."""
        actions = ["status", "stop", "destroy", "reconcile"]
        for action in actions:
            with self.subTest(action=action):
                code, result = self.cli("orchestrate", "compute", action)
                self.assertEqual(code, 2, f"Expected code 2 for {action}")
                self.assertIn("error", result)
                self.assertIn("job-id", result["error"], f"Missing job-id error for {action}")

    def test_jobs_lists_all_jobs(self) -> None:
        budget.set_budget(100, 5, home=self.budget_home)
        code, job1 = self.cli(
            "orchestrate", "compute", "provision",
            "--provider", "fake",
            "--gpu", "A100",
            "--hourly-usd", "2.0",
            "--low-usd", "0.5",
            "--expected-usd", "1.0",
            "--high-usd", "2.0",
        )
        code, job2 = self.cli(
            "orchestrate", "compute", "provision",
            "--provider", "fake",
            "--gpu", "H100",
            "--hourly-usd", "3.0",
            "--low-usd", "1.0",
            "--expected-usd", "1.5",
            "--high-usd", "3.0",
        )
        code, jobs = self.cli("orchestrate", "compute", "jobs")
        self.assertEqual(code, 0)
        self.assertIsInstance(jobs, list)
        self.assertEqual(len(jobs), 2)
        job_ids = {j["job_id"] for j in jobs}
        self.assertIn(job1["job_id"], job_ids)
        self.assertIn(job2["job_id"], job_ids)

    def test_jobs_empty_list_when_no_jobs(self) -> None:
        code, jobs = self.cli("orchestrate", "compute", "jobs")
        self.assertEqual(code, 0)
        self.assertEqual(jobs, [])

    def test_provision_without_budget_is_blocked(self) -> None:
        """Test that provision without a budget is blocked."""
        code, result = self.cli(
            "orchestrate", "compute", "provision",
            "--provider", "fake",
            "--gpu", "A100",
            "--hourly-usd", "2.0",
            "--low-usd", "0.5",
            "--expected-usd", "1.0",
            "--high-usd", "2.0",
        )
        self.assertEqual(code, 0, result)
        self.assertEqual(result["state"], "blocked", f"Expected blocked state, got {result}")
        self.assertIn("reason", result)

    def test_provision_requires_provider(self) -> None:
        """Test that --provider is required for provision."""
        budget.set_budget(100, 5, home=self.budget_home)
        code, result = self.cli(
            "orchestrate", "compute", "provision",
            "--gpu", "A100",
            "--hourly-usd", "2.0",
            "--low-usd", "0.5",
            "--expected-usd", "1.0",
            "--high-usd", "2.0",
        )
        self.assertEqual(code, 2)
        self.assertIn("error", result)
        self.assertIn("provider", result["error"].lower())

    def test_roundtrip_provision_status_stop_reconcile_destroy(self) -> None:
        """Test round-trip: provision -> status -> stop -> reconcile -> destroy."""
        budget.set_budget(100, 5, home=self.budget_home)

        # Provision
        code, job = self.cli(
            "orchestrate", "compute", "provision",
            "--provider", "fake",
            "--gpu", "A100",
            "--hourly-usd", "2.0",
            "--low-usd", "0.5",
            "--expected-usd", "1.0",
            "--high-usd", "2.0",
        )
        self.assertEqual(code, 0, job)
        self.assertEqual(job["state"], "running")
        job_id = job["job_id"]

        # Status
        code, status_result = self.cli("orchestrate", "compute", "status", "--job-id", job_id)
        self.assertEqual(code, 0, status_result)
        self.assertEqual(status_result["state"], "running")
        self.assertEqual(status_result["job_id"], job_id)

        # Stop
        code, stop_result = self.cli("orchestrate", "compute", "stop", "--job-id", job_id)
        self.assertEqual(code, 0, stop_result)
        # After stop, job should be in stopping or stopped state
        self.assertIn(stop_result["state"], {"stopping", "stopped"})

        # Reconcile with actual_usd
        code, reconcile_result = self.cli(
            "orchestrate", "compute", "reconcile", "--job-id", job_id, "--actual-usd", "0.8"
        )
        self.assertEqual(code, 0, reconcile_result)
        # After reconcile, job should be in reconciled state or preparing to be
        self.assertIn(reconcile_result["state"], {"stopped", "destroyed", "reconciled"})

        # Destroy
        code, destroy_result = self.cli("orchestrate", "compute", "destroy", "--job-id", job_id)
        self.assertEqual(code, 0, destroy_result)
        # After destroy, job should be in destroyed or reconciled state
        self.assertIn(destroy_result["state"], {"destroyed", "reconciled"})

    def test_inventory_with_mocked_provider(self) -> None:
        """Test inventory with a mocked provider to avoid real API calls."""
        from agent_os.orchestrator import compute

        mock_inventory_result = {
            "provider": "runpod",
            "offers": [
                {"name": "A100", "vram_gb": 40, "hourly_usd": 1.99},
                {"name": "H100", "vram_gb": 80, "hourly_usd": 3.99},
            ],
        }

        with mock.patch.object(compute, "inventory", return_value=mock_inventory_result):
            code, stock = self.cli(
                "orchestrate", "compute", "inventory",
                "--provider", "runpod",
            )

        self.assertEqual(code, 0, stock)
        self.assertEqual(stock["provider"], "runpod")
        self.assertEqual(len(stock["offers"]), 2)


if __name__ == "__main__":
    unittest.main()
