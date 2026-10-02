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
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tmpdir = Path(self.tmp.name)
        self.orch_home = self.tmpdir / "orch"
        self.budget_home = self.tmpdir / "budget"
        self.budget_home.mkdir()

    def cli(self, *argv: str) -> tuple[int, object]:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            with mock.patch.dict(
                "os.environ",
                {
                    "AGENT_OS_ORCHESTRATOR_HOME": str(self.orch_home),
                    "AGENT_OS_PROVIDERS": str(self.budget_home / "providers.json"),
                },
            ):
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
        self.assertIsNone(job["instance_id"])

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
        """Each of status/stop/destroy/reconcile without --job-id returns 2 with the shared error."""
        for action in ("status", "stop", "destroy", "reconcile"):
            with self.subTest(action=action):
                code, result = self.cli("orchestrate", "compute", action)
                self.assertEqual(code, 2, result)
                self.assertEqual(result, {"error": f"{action} needs --job-id"})

    def test_budget_home_resolves_next_to_provider_registry(self) -> None:
        """AGENT_OS_BUDGET_HOME is not consulted; the budget lives beside AGENT_OS_PROVIDERS."""
        budget.set_budget(100, 5, home=self.budget_home)
        decoy = self.tmpdir / "decoy-budget"
        decoy.mkdir()
        with mock.patch.dict("os.environ", {"AGENT_OS_BUDGET_HOME": str(decoy)}):
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
        self.assertEqual(job["state"], "running", job)

    def test_unknown_job_id_returns_error(self) -> None:
        """Test that status with unknown --job-id returns error code 2."""
        code, result = self.cli("orchestrate", "compute", "status", "--job-id", "nope-123")
        self.assertEqual(code, 2)
        self.assertIn("error", result)
        self.assertIn("unknown", result["error"].lower())

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
        self.assertEqual(code, 0, job1)
        code, job2 = self.cli(
            "orchestrate", "compute", "provision",
            "--provider", "fake",
            "--gpu", "H100",
            "--hourly-usd", "3.0",
            "--low-usd", "1.0",
            "--expected-usd", "1.5",
            "--high-usd", "3.0",
        )
        self.assertEqual(code, 0, job2)
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
        self.assertIn("budget", result["reason"].lower())

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

    def test_roundtrip_provision_status_stop_destroy_reconcile(self) -> None:
        """Round-trip through separate CLI calls; each builds a fresh provider from fake.json."""
        budget.set_budget(100, 5, home=self.budget_home)
        fake_state = self.orch_home / "compute-providers" / "fake.json"

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
        instance_id = job["instance_id"]

        code, status_result = self.cli("orchestrate", "compute", "status", "--job-id", job_id)
        self.assertEqual(code, 0, status_result)
        self.assertEqual(status_result["state"], "running")
        self.assertEqual(status_result["job_id"], job_id)

        code, stop_result = self.cli("orchestrate", "compute", "stop", "--job-id", job_id)
        self.assertEqual(code, 0, stop_result)
        self.assertEqual(stop_result["state"], "stopped")

        code, destroy_result = self.cli("orchestrate", "compute", "destroy", "--job-id", job_id)
        self.assertEqual(code, 0, destroy_result)
        self.assertEqual(destroy_result["state"], "destroyed")
        instances = json.loads(fake_state.read_text(encoding="utf-8"))["instances"]
        self.assertEqual(instances[instance_id]["state"], "terminated")

        code, reconcile_result = self.cli(
            "orchestrate", "compute", "reconcile", "--job-id", job_id, "--actual-usd", "0.8"
        )
        self.assertEqual(code, 0, reconcile_result)
        self.assertEqual(reconcile_result["state"], "reconciled")
        self.assertEqual(reconcile_result["reconcile"]["actual_usd"], 0.8)

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
