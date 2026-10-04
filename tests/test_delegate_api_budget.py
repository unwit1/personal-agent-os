"""P1.3: delegate() gates and meters per-token API providers."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

    def test_precall_estimate_blocks_per_call_cap(self) -> None:
        """Test (a): budget 1.0, cap 0.5, estimate 0.9 -> status budget_blocked."""
        api_budget.set_api_budget(1.0, 0.5, home=self.budget)
        with mock.patch.object(delegate_module, "estimate_cost", return_value=0.9):
            outcome = self._run("api")
        self.assertEqual(outcome["status"], "budget_blocked")
        self.assertEqual(self.calls, 0)
        self.assertIn("per-call cap", outcome["errors"][0])
        self.assertEqual(api_budget.api_spent(self.budget), 0.0)

    def test_precall_estimate_recorded_when_allowed(self) -> None:
        """Test (b): estimate 0.1 -> status passed, outcome['api_estimated_cost_usd'] == 0.1."""
        api_budget.set_api_budget(1.0, 0.5, home=self.budget)
        with mock.patch.object(delegate_module, "estimate_cost", return_value=0.1):
            outcome = self._run("api")
        self.assertEqual(outcome["status"], "passed")
        self.assertEqual(outcome["api_estimated_cost_usd"], 0.1)
        self.assertEqual(self.calls, 1)

    def test_precall_estimate_none_allows_call(self) -> None:
        """Test (c): estimate None -> passed."""
        api_budget.set_api_budget(1.0, 0.5, home=self.budget)
        with mock.patch.object(delegate_module, "estimate_cost", return_value=None):
            outcome = self._run("api")
        self.assertEqual(outcome["status"], "passed")
        self.assertIsNone(outcome["api_estimated_cost_usd"])
        self.assertEqual(self.calls, 1)

    def test_monthly_budget_previous_month_not_counted(self) -> None:
        """Test: Monthly budget excludes spend from previous UTC month.

        With a monthly API budget and an api-spend.jsonl entry dated in the previous
        UTC month whose amount exceeds the total, delegate() is not budget_blocked.
        """
        from datetime import datetime, timezone, timedelta
        import json

        # Set a monthly budget: $1.00 total, $0.50 per-call cap
        api_budget.set_api_budget(1.0, 0.5, period="monthly", home=self.budget)

        # Create a ledger entry from the previous UTC month with amount exceeding budget
        now = datetime.now(timezone.utc)
        prev_month = now - timedelta(days=now.day)  # First day of previous month
        prev_month_iso = prev_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

        ledger_path = self.budget / "api-spend.jsonl"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "at": prev_month_iso,
            "call_id": "OLD-123",
            "provider": "anthropic",
            "model": "claude-3-sonnet",
            "amount_usd": 2.0,
            "accuracy": "exact",
            "note": "previous month"
        }
        with ledger_path.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")

        # Delegate should succeed despite the previous month's overspend
        outcome = self._run("api")
        self.assertEqual(outcome["status"], "passed")
        self.assertEqual(self.calls, 1)

    def test_monthly_budget_today_entry_is_counted(self) -> None:
        """Test: Monthly budget includes spend from today.

        With a monthly API budget and an api-spend.jsonl entry dated today
        whose amount equals the total, delegate() returns status 'budget_blocked'.
        """
        from datetime import datetime, timezone
        import json

        # Set a monthly budget: $1.00 total, $0.50 per-call cap
        api_budget.set_api_budget(1.0, 0.5, period="monthly", home=self.budget)

        # Create a ledger entry from today that exhausts the budget
        now = datetime.now(timezone.utc)
        today_iso = now.isoformat()

        ledger_path = self.budget / "api-spend.jsonl"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "at": today_iso,
            "call_id": "TODAY-456",
            "provider": "anthropic",
            "model": "claude-3-sonnet",
            "amount_usd": 1.0,
            "accuracy": "exact",
            "note": "today"
        }
        with ledger_path.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")

        # Delegate should be blocked because today's spend exhausts the monthly budget
        outcome = self._run("api")
        self.assertEqual(outcome["status"], "budget_blocked")
        self.assertEqual(self.calls, 0)
        self.assertIn("exhausted", outcome["errors"][0].lower())


if __name__ == "__main__":
    unittest.main()
