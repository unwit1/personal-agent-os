"""P1.3: delegate() gates and meters per-token API providers."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import api_budget  # noqa: E402
from agent_os.orchestrator import delegate as delegate_module  # noqa: E402
from agent_os.orchestrator.adapters import synthetic  # noqa: E402
from agent_os.orchestrator.router import ProviderRegistry  # noqa: E402


def _registry(deployment: str) -> ProviderRegistry:
    return ProviderRegistry(providers=[{
        "id": "syn", "adapter": "synthetic", "options": {"script": "syn"}, "models": {"fast": "syn-fast"},
        "profile": {"deployment": deployment},
    }])


class DelegateApiBudgetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        self.budget = Path(self.tmp.name) / "budget"
        self.calls = 0
        self.cost: float | None = 0.02

        def script(request, call):
            self.calls += 1
            return {"structured": {"ok": True}, "usage": {"input_tokens": 10, "output_tokens": 5, "cost_usd": self.cost}}

        synthetic.SCRIPTS["syn"] = script

    def tearDown(self) -> None:
        synthetic.reset()
        self.tmp.cleanup()

    def _run(self, deployment: str) -> dict:
        return delegate_module.delegate("x", task_family="t", registry=_registry(deployment), home=self.home,
                                        cwd=self.tmp.name, record=False, budget_home=self.budget)

    def test_blocked_without_budget(self) -> None:
        outcome = self._run("api")
        self.assertEqual(outcome["status"], "budget_blocked")
        self.assertEqual(outcome["billing"], "api")
        self.assertFalse(outcome["budget"]["allowed"])
        self.assertEqual(self.calls, 0)
        self.assertEqual(api_budget.api_spent(self.budget), 0.0)

    def test_spend_recorded_when_approved(self) -> None:
        api_budget.set_api_budget(1.0, 0.5, home=self.budget)
        outcome = self._run("api")
        self.assertEqual(outcome["status"], "passed")
        self.assertEqual(self.calls, 1)
        self.assertEqual(outcome["api_spend_usd"], 0.02)
        self.assertEqual(api_budget.api_spent(self.budget), 0.02)
        self.assertNotIn("api_call_cap_exceeded", outcome)

    def test_call_cap_exceeded_flag(self) -> None:
        api_budget.set_api_budget(1.0, 0.01, home=self.budget)
        self.assertTrue(self._run("api")["api_call_cap_exceeded"])

    def test_unknown_cost_recorded_as_zero(self) -> None:
        api_budget.set_api_budget(1.0, 0.5, home=self.budget)
        self.cost = None
        outcome = self._run("api")
        self.assertIsNone(outcome["api_spend_usd"])
        self.assertEqual(api_budget.api_spent(self.budget), 0.0)
        ledger = (self.budget / "api-spend.jsonl").read_text(encoding="utf-8")
        self.assertIn('"accuracy": "unknown"', ledger)

    def test_subscription_never_touches_ledger(self) -> None:
        outcome = self._run("subscription")
        self.assertEqual(outcome["status"], "passed")
        self.assertEqual(outcome["billing"], "host_plan")
        self.assertFalse((self.budget / "api-spend.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
