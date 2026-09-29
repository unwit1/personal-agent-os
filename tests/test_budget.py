"""IMP-0015: operator budget, spend ledger and the quote budget gate."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import budget, quote  # noqa: E402
from agent_os.orchestrator.workload import normalize_workload  # noqa: E402

GPU = {"kind": "gpu_pod", "id": "pod", "gpu_hourly_usd": 1.0, "gen_tokens_per_second": 1000, "startup_minutes": 0, "idle_minutes": 0, "failure_rate": 0.0}


def workload(hours: float, **extra) -> dict:
    # tokens so that expected runtime is `hours` at 1000 tok/s; high band = 1.5x
    return normalize_workload({"type": "batch_inference", "size": {"output_tokens": hours * 3600 * 1000}, **extra})


class BudgetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_unset_budget_blocks_paid_options(self) -> None:
        state = budget.effective(None, self.home)
        self.assertEqual((state["approved"], state["source"]), (False, "none configured"))
        gate = quote.quote(workload(1), [GPU], state)["recommended_gate"]
        self.assertEqual((gate["allowed"], gate["requires_approval"]), (False, True))
        self.assertIn("budget set", budget.show(self.home)["note"])

    def test_operator_budget_allows_within_cap_and_blocks_above(self) -> None:
        budget.set_budget(10, 5, note="operator approval 2026-09-29", home=self.home)
        within = quote.quote(workload(2), [GPU], budget.effective(None, self.home))["recommended_gate"]  # high = 3.0 h * $1
        self.assertTrue(within["allowed"], within)
        over = quote.quote(workload(4), [GPU], budget.effective(None, self.home))["recommended_gate"]  # high = $6 > $5 cap
        self.assertIn("exceeds job hard cap $5.00", over["reason"])

    def test_spend_reduces_remaining_and_gates_the_project(self) -> None:
        budget.set_budget(10, 5, home=self.home)
        budget.record_spend(4.0, job_id="j1", home=self.home)
        budget.record_spend(3.0, job_id="j2", kind="reserved", home=self.home)
        self.assertEqual((budget.spent(self.home), budget.remaining(self.home)), (7.0, 3.0))
        gate = quote.quote(workload(2.5), [GPU], budget.effective(None, self.home))["recommended_gate"]  # high $3.75 > $3 left
        self.assertIn("exceeds project budget $3.00", gate["reason"])
        budget.record_spend(3.0, job_id="j2", kind="release", home=self.home)
        self.assertEqual(budget.remaining(self.home), 6.0)

    def test_workload_limits_only_tighten(self) -> None:
        budget.set_budget(10, 5, home=self.home)
        tighter = budget.effective({"job_hard_cap_usd": 1, "approved": False}, self.home)
        self.assertEqual((tighter["job_hard_cap_usd"], tighter["approved"]), (1, True))
        looser = budget.effective({"job_hard_cap_usd": 50, "project_usd": 500}, self.home)
        self.assertEqual((looser["job_hard_cap_usd"], looser["project_usd"]), (5, 10))

    def test_changes_are_validated_and_kept_in_history(self) -> None:
        with self.assertRaises(ValueError):
            budget.set_budget(10, 20, home=self.home)
        with self.assertRaises(ValueError):
            budget.set_budget(-1, 0, home=self.home)
        budget.set_budget(10, 5, home=self.home)
        budget.set_budget(25, 8, home=self.home)
        history = [json.loads(line) for line in (self.home / "budget-history.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([entry["current"]["project_usd"] for entry in history], [10, 25])
        self.assertEqual(history[1]["previous"]["job_hard_cap_usd"], 5)
        with self.assertRaises(ValueError):
            budget.record_spend(1, job_id="x", kind="refund", home=self.home)


if __name__ == "__main__":
    unittest.main()
