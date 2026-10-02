"""Compute provisioning MCP tools (IMP-0015 slice 2)."""

from __future__ import annotations

import json
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_orchestrator_surfaces import SurfaceFixture

from agent_os.mcp_server import TOOL_SCHEMAS, _handle_mcp, methods  # noqa: E402
from agent_os.orchestrator.compute_fake import FakeProvider  # noqa: E402
from agent_os.orchestrator import provision  # noqa: E402


class ComputeProvisionMcpTests(SurfaceFixture):
    COMPUTE_TOOLS = (
        "compute.provision",
        "compute.status",
        "compute.stop",
        "compute.destroy",
        "compute.reconcile",
    )

    def setUp(self) -> None:
        super().setUp()
        from agent_os.orchestrator import budget, service

        budget.set_budget(100.0, 50.0, set_by="test", home=self.engine.store.home.parent)

        # Initialize the FakeProvider in service._FAKE_PROVIDERS for the test home
        service._FAKE_PROVIDERS.clear()
        self.fake_provider = FakeProvider(hourly_usd=1.5, clock=time.time)
        service._FAKE_PROVIDERS[self.engine.store.home] = self.fake_provider

    def call(self, name: str, arguments: dict) -> dict:
        response = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments}}, methods())
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertFalse(response["result"]["isError"], payload)
        return payload

    def call_expect_error(self, name: str, arguments: dict) -> dict:
        response = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments}}, methods())
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertTrue(response["result"]["isError"], payload)
        return payload

    def test_compute_tools_are_advertised_and_dispatchable(self) -> None:
        available = methods()
        listed = {tool["name"] for tool in _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, available)["result"]["tools"]}
        for name in self.COMPUTE_TOOLS:
            self.assertIn(name, TOOL_SCHEMAS, f"{name} not in TOOL_SCHEMAS")
            self.assertIn(name, listed, f"{name} not in listed tools")
            self.assertIn(name, available, f"{name} not in available methods")

    def test_fake_provision_stop_destroy_reconcile_roundtrip(self) -> None:
        estimate = {"low": 0.5, "expected": 1.0, "high": 2.0}

        # Provision with fake provider
        provision = self.call("compute.provision", {
            "provider": "fake",
            "gpu": "a100",
            "hourly_usd": 1.50,
            "estimate": estimate,
            "max_runtime_seconds": 3600,
        })
        self.assertEqual(provision["state"], "running", f"expected running state, got {provision}")
        self.assertEqual(provision["provider"], "fake")
        self.assertIsNotNone(provision["instance_id"])
        self.assertIsNotNone(provision["job_id"])
        job_id = provision["job_id"]

        # Status check
        status = self.call("compute.status", {"job_id": job_id})
        self.assertEqual(status["state"], "running")
        self.assertEqual(status["job_id"], job_id)
        self.assertIsNotNone(status["cost_usd"])

        # Stop
        stopped = self.call("compute.stop", {"job_id": job_id})
        self.assertEqual(stopped["state"], "stopped")
        self.assertIsNotNone(stopped["cost_usd"])

        # Destroy
        destroyed = self.call("compute.destroy", {"job_id": job_id})
        self.assertEqual(destroyed["state"], "destroyed")

        # Reconcile
        reconciled = self.call("compute.reconcile", {"job_id": job_id})
        self.assertEqual(reconciled["state"], "reconciled")
        self.assertIsNotNone(reconciled["reconcile"])
        self.assertIn("actual_usd", reconciled["reconcile"])
        self.assertIn("variance_usd", reconciled["reconcile"])

    def test_non_fake_provider_is_blocked(self) -> None:
        estimate = {"low": 0.5, "expected": 1.0, "high": 2.0}

        # Non-fake provider should be blocked
        blocked = self.call("compute.provision", {
            "provider": "runpod",
            "gpu": "a100",
            "hourly_usd": 1.50,
            "estimate": estimate,
        })
        self.assertEqual(blocked["state"], "blocked", f"expected blocked state, got {blocked}")
        self.assertIn("gate", blocked)

    def test_raw_secret_without_protocol_is_rejected(self) -> None:
        estimate = {"low": 0.5, "expected": 1.0, "high": 2.0}

        # Raw secret (not secrets://) should be rejected
        error = self.call_expect_error("compute.provision", {
            "provider": "fake",
            "gpu": "a100",
            "hourly_usd": 1.50,
            "estimate": estimate,
            "secret_ref": "just-a-raw-string",
        })
        self.assertIn("error", error)
        self.assertIn("secrets://", str(error))

    def test_idempotent_provision_with_same_request(self) -> None:
        estimate = {"low": 0.5, "expected": 1.0, "high": 2.0}
        job_id = "test-job-123"

        # Provision once
        prov1 = self.call("compute.provision", {
            "provider": "fake",
            "gpu": "a100",
            "hourly_usd": 1.50,
            "estimate": estimate,
            "job_id": job_id,
        })

        # Provision again with same request should return same job
        prov2 = self.call("compute.provision", {
            "provider": "fake",
            "gpu": "a100",
            "hourly_usd": 1.50,
            "estimate": estimate,
            "job_id": job_id,
        })

        self.assertEqual(prov1["job_id"], prov2["job_id"])
        self.assertEqual(prov1["instance_id"], prov2["instance_id"])
        self.assertEqual(prov1["state"], prov2["state"])

    def test_compute_homes_returns_correct_values(self) -> None:
        """With embedded engine (set_engine called), budget_home should be home.parent."""
        from agent_os.orchestrator import service
        home, budget_home = service._compute_homes()
        self.assertIsNotNone(home)
        self.assertIsNotNone(budget_home)
        self.assertEqual(budget_home, home.parent)


if __name__ == "__main__":
    unittest.main()
