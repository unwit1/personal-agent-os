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

    def test_status_requires_job_id(self) -> None:
        code, result = self.cli("orchestrate", "compute", "status")
        self.assertEqual(code, 2)
        self.assertIn("error", result)
        self.assertIn("job-id", result["error"])

    def test_stop_requires_job_id(self) -> None:
        code, result = self.cli("orchestrate", "compute", "stop")
        self.assertEqual(code, 2)
        self.assertIn("error", result)
        self.assertIn("job-id", result["error"])

    def test_destroy_requires_job_id(self) -> None:
        code, result = self.cli("orchestrate", "compute", "destroy")
        self.assertEqual(code, 2)
        self.assertIn("error", result)
        self.assertIn("job-id", result["error"])

    def test_reconcile_requires_job_id(self) -> None:
        code, result = self.cli("orchestrate", "compute", "reconcile")
        self.assertEqual(code, 2)
        self.assertIn("error", result)
        self.assertIn("job-id", result["error"])

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

    def test_inventory_still_works(self) -> None:
        code, stock = self.cli(
            "orchestrate", "compute", "inventory",
            "--provider", "runpod",
        )
        self.assertIn(code, {0, 2})  # 0 if network available, 2 if offline (test has no network)
        self.assertIsInstance(stock, dict)


if __name__ == "__main__":
    unittest.main()
