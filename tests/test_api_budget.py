"""Tests for API budget and spend ledger (api_budget module)."""

from __future__ import annotations

import datetime
import json
import sys
import tempfile
import unittest
from datetime import timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import api_budget  # noqa: E402


class ApibudgetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_unset_budget_blocks_api_calls(self) -> None:
        result = api_budget.check(self.home)
        self.assertFalse(result["allowed"])
        self.assertIn("no API budget set", result["reason"])
        self.assertIn("api-budget set --total-usd", result["reason"])

    def test_operator_can_set_api_budget(self) -> None:
        result = api_budget.set_api_budget(100.0, 10.0, home=self.home)
        self.assertTrue(result["approved"])
        self.assertEqual(result["set_by"], "operator")
        self.assertEqual(result["total_usd"], 100.0)
        self.assertEqual(result["call_cap_usd"], 10.0)
        self.assertEqual(result["kind"], "api")
        self.assertEqual(result["currency"], "USD")
        self.assertEqual(result["spent_usd"], 0.0)
        self.assertEqual(result["remaining_usd"], 100.0)

    def test_set_budget_validates_constraints(self) -> None:
        with self.assertRaises(ValueError):
            api_budget.set_api_budget(10.0, 20.0, home=self.home)
        with self.assertRaises(ValueError):
            api_budget.set_api_budget(-1.0, 0.0, home=self.home)
        with self.assertRaises(ValueError):
            api_budget.set_api_budget(10.0, -1.0, home=self.home)

    def test_budget_set_allows_api_calls(self) -> None:
        api_budget.set_api_budget(100.0, 10.0, home=self.home)
        result = api_budget.check(self.home)
        self.assertTrue(result["allowed"])
        self.assertEqual(result["reason"], "within API budget")
        self.assertEqual(result["remaining_usd"], 100.0)
        self.assertEqual(result["call_cap_usd"], 10.0)

    def test_record_api_spend_appends_to_ledger(self) -> None:
        api_budget.set_api_budget(100.0, 10.0, home=self.home)
        result = api_budget.record_api_spend(2.5, call_id="call1", provider="anthropic", model="claude-opus", home=self.home)
        self.assertEqual(result["call_id"], "call1")
        self.assertEqual(result["provider"], "anthropic")
        self.assertEqual(result["model"], "claude-opus")
        self.assertEqual(result["amount_usd"], 2.5)
        spend_path = self.home / "api-spend.jsonl"
        self.assertTrue(spend_path.exists())
        lines = spend_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        entry = json.loads(lines[0])
        self.assertEqual(entry["amount_usd"], 2.5)

    def test_api_spent_sums_all_spend(self) -> None:
        api_budget.set_api_budget(100.0, 10.0, home=self.home)
        api_budget.record_api_spend(2.5, call_id="call1", provider="anthropic", home=self.home)
        api_budget.record_api_spend(3.75, call_id="call2", provider="openai", home=self.home)
        total = api_budget.api_spent(self.home)
        self.assertAlmostEqual(total, 6.25, places=6)

    def test_api_spent_rounds_to_six_places(self) -> None:
        api_budget.set_api_budget(100.0, 10.0, home=self.home)
        api_budget.record_api_spend(0.1234567, call_id="call1", provider="anthropic", home=self.home)
        total = api_budget.api_spent(self.home)
        self.assertEqual(total, 0.123457)

    def test_api_spent_skips_malformed_lines(self) -> None:
        api_budget.set_api_budget(100.0, 10.0, home=self.home)
        api_budget.record_api_spend(2.5, call_id="call1", provider="anthropic", home=self.home)
        spend_path = self.home / "api-spend.jsonl"
        with spend_path.open("a", encoding="utf-8") as f:
            f.write("this is not valid json\n")
        api_budget.record_api_spend(3.75, call_id="call2", provider="openai", home=self.home)
        total = api_budget.api_spent(self.home)
        self.assertAlmostEqual(total, 6.25, places=6)

    def test_api_spent_skips_non_dict_entries(self) -> None:
        api_budget.set_api_budget(100.0, 10.0, home=self.home)
        api_budget.record_api_spend(2.5, call_id="call1", provider="anthropic", home=self.home)
        spend_path = self.home / "api-spend.jsonl"
        with spend_path.open("a", encoding="utf-8") as f:
            f.write("[]\n")
            f.write("null\n")
        api_budget.record_api_spend(3.75, call_id="call2", provider="openai", home=self.home)
        total = api_budget.api_spent(self.home)
        self.assertAlmostEqual(total, 6.25, places=6)

    def test_api_spent_skips_non_numeric_amount(self) -> None:
        api_budget.set_api_budget(100.0, 10.0, home=self.home)
        api_budget.record_api_spend(2.5, call_id="call1", provider="anthropic", home=self.home)
        spend_path = self.home / "api-spend.jsonl"
        with spend_path.open("a", encoding="utf-8") as f:
            f.write('{"amount_usd": "invalid"}\n')
            f.write('{"amount_usd": null}\n')
        api_budget.record_api_spend(3.75, call_id="call2", provider="openai", home=self.home)
        total = api_budget.api_spent(self.home)
        self.assertAlmostEqual(total, 6.25, places=6)

    def test_api_remaining_returns_none_when_no_budget(self) -> None:
        remaining = api_budget.api_remaining(self.home)
        self.assertIsNone(remaining)

    def test_api_remaining_decreases_with_spend(self) -> None:
        api_budget.set_api_budget(100.0, 10.0, home=self.home)
        self.assertEqual(api_budget.api_remaining(self.home), 100.0)
        api_budget.record_api_spend(25.5, call_id="call1", provider="anthropic", home=self.home)
        self.assertEqual(api_budget.api_remaining(self.home), 74.5)

    def test_api_remaining_cannot_go_negative(self) -> None:
        api_budget.set_api_budget(10.0, 10.0, home=self.home)
        api_budget.record_api_spend(15.0, call_id="call1", provider="anthropic", home=self.home)
        remaining = api_budget.api_remaining(self.home)
        self.assertEqual(remaining, 0.0)

    def test_exhausted_budget_blocks_api_calls(self) -> None:
        api_budget.set_api_budget(10.0, 5.0, home=self.home)
        api_budget.record_api_spend(10.0, call_id="call1", provider="anthropic", home=self.home)
        result = api_budget.check(self.home)
        self.assertFalse(result["allowed"])
        self.assertEqual(result["reason"], "API budget exhausted")
        self.assertEqual(result["remaining_usd"], 0.0)

    def test_budget_history_tracks_changes(self) -> None:
        api_budget.set_api_budget(100.0, 10.0, note="initial setup", home=self.home)
        api_budget.set_api_budget(200.0, 20.0, note="increased budget", home=self.home)
        history_path = self.home / "api-budget-history.jsonl"
        self.assertTrue(history_path.exists())
        lines = history_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        entry1 = json.loads(lines[0])
        entry2 = json.loads(lines[1])
        self.assertEqual(entry1["current"]["total_usd"], 100.0)
        self.assertEqual(entry2["current"]["total_usd"], 200.0)
        self.assertEqual(entry2["previous"]["total_usd"], 100.0)

    def test_record_api_spend_with_optional_fields(self) -> None:
        api_budget.set_api_budget(100.0, 10.0, home=self.home)
        result = api_budget.record_api_spend(
            1.5, call_id="call1", provider="anthropic", model="claude-3-opus", accuracy="estimated", note="test call", home=self.home
        )
        self.assertEqual(result["model"], "claude-3-opus")
        self.assertEqual(result["accuracy"], "estimated")
        self.assertEqual(result["note"], "test call")

    def test_record_api_spend_without_optional_fields(self) -> None:
        api_budget.set_api_budget(100.0, 10.0, home=self.home)
        result = api_budget.record_api_spend(1.5, call_id="call1", provider="openai", home=self.home)
        self.assertIsNone(result["model"])
        self.assertIsNone(result["accuracy"])
        self.assertIsNone(result["note"])

    def test_load_returns_empty_dict_when_missing(self) -> None:
        result = api_budget.load(self.home)
        self.assertEqual(result, {})

    def test_load_returns_empty_dict_when_invalid(self) -> None:
        budget_path = api_budget.api_budget_path(self.home)
        budget_path.parent.mkdir(parents=True, exist_ok=True)
        budget_path.write_text("not valid json", encoding="utf-8")
        result = api_budget.load(self.home)
        self.assertEqual(result, {})

    def test_load_returns_budget_when_valid(self) -> None:
        api_budget.set_api_budget(50.0, 5.0, home=self.home)
        result = api_budget.load(self.home)
        self.assertEqual(result["total_usd"], 50.0)
        self.assertEqual(result["call_cap_usd"], 5.0)
        self.assertTrue(result["approved"])

    def test_is_api_provider_checks_deployment(self) -> None:
        api_provider = {"adapter": "anthropic_api", "profile": {"deployment": "api"}}
        local_provider = {"adapter": "local_llm", "profile": {"deployment": "local"}}
        self.assertTrue(api_budget.is_api_provider(api_provider))
        self.assertFalse(api_budget.is_api_provider(local_provider))

    def test_is_api_provider_infers_from_adapter(self) -> None:
        api_provider = {"adapter": "anthropic_api"}
        subscription_provider = {"adapter": "claude_code"}
        self.assertTrue(api_budget.is_api_provider(api_provider))
        self.assertFalse(api_budget.is_api_provider(subscription_provider))

    def test_check_includes_remaining_and_call_cap(self) -> None:
        api_budget.set_api_budget(50.0, 5.0, home=self.home)
        api_budget.record_api_spend(15.0, call_id="call1", provider="anthropic", home=self.home)
        result = api_budget.check(self.home)
        self.assertEqual(result["remaining_usd"], 35.0)
        self.assertEqual(result["call_cap_usd"], 5.0)

    def test_api_remaining_returns_none_on_non_numeric_total_usd(self) -> None:
        budget_path = api_budget.api_budget_path(self.home)
        budget_path.parent.mkdir(parents=True, exist_ok=True)
        budget_path.write_text('{"total_usd": "invalid", "call_cap_usd": 10.0, "approved": true}', encoding="utf-8")
        remaining = api_budget.api_remaining(self.home)
        self.assertIsNone(remaining)

    def test_check_rejects_corrupt_budget_with_non_numeric_total_usd(self) -> None:
        budget_path = api_budget.api_budget_path(self.home)
        budget_path.parent.mkdir(parents=True, exist_ok=True)
        budget_path.write_text('{"total_usd": "invalid", "call_cap_usd": 10.0, "approved": true}', encoding="utf-8")
        result = api_budget.check(self.home)
        self.assertFalse(result["allowed"])
        self.assertEqual(result["reason"], "API budget invalid; re-run api-budget set")
        self.assertIsNone(result["remaining_usd"])

    def test_check_rejects_corrupt_budget_with_missing_total_usd(self) -> None:
        budget_path = api_budget.api_budget_path(self.home)
        budget_path.parent.mkdir(parents=True, exist_ok=True)
        budget_path.write_text('{"call_cap_usd": 10.0, "approved": true}', encoding="utf-8")
        result = api_budget.check(self.home)
        self.assertFalse(result["allowed"])
        self.assertEqual(result["reason"], "API budget invalid; re-run api-budget set")
        self.assertIsNone(result["remaining_usd"])

    def test_estimated_cost_below_cap_is_allowed(self) -> None:
        api_budget.set_api_budget(100.0, 10.0, home=self.home)
        result = api_budget.check(self.home, estimated_cost_usd=5.0)
        self.assertTrue(result["allowed"])
        self.assertEqual(result["reason"], "within API budget")
        self.assertEqual(result["estimated_cost_usd"], 5.0)

    def test_estimated_cost_above_cap_is_blocked(self) -> None:
        api_budget.set_api_budget(100.0, 10.0, home=self.home)
        result = api_budget.check(self.home, estimated_cost_usd=15.0)
        self.assertFalse(result["allowed"])
        self.assertIn("per-call cap", result["reason"])
        self.assertEqual(result["estimated_cost_usd"], 15.0)

    def test_estimated_cost_above_remaining_budget_is_blocked(self) -> None:
        api_budget.set_api_budget(1.0, 0.5, home=self.home)
        api_budget.record_api_spend(0.8, call_id="call1", provider="anthropic", home=self.home)
        result = api_budget.check(self.home, estimated_cost_usd=0.3)
        self.assertFalse(result["allowed"])
        self.assertIn("remaining", result["reason"])
        self.assertEqual(result["estimated_cost_usd"], 0.3)

    def test_check_without_estimate_returns_none(self) -> None:
        api_budget.set_api_budget(100.0, 10.0, home=self.home)
        result = api_budget.check(self.home)
        self.assertTrue(result["allowed"])
        self.assertIsNone(result["estimated_cost_usd"])

    def test_check_without_budget_includes_estimated_cost_key(self) -> None:
        result = api_budget.check(self.home, estimated_cost_usd=5.0)
        self.assertFalse(result["allowed"])
        self.assertIn("no API budget set", result["reason"])
        self.assertEqual(result["estimated_cost_usd"], 5.0)

    def test_set_budget_without_period_defaults_to_total(self) -> None:
        result = api_budget.set_api_budget(100.0, 10.0, home=self.home)
        self.assertEqual(result["period"], "total")
        loaded = api_budget.load(self.home)
        self.assertEqual(loaded["period"], "total")

    def test_set_budget_with_monthly_period(self) -> None:
        result = api_budget.set_api_budget(100.0, 10.0, period="monthly", home=self.home)
        self.assertEqual(result["period"], "monthly")
        self.assertIsNotNone(result["period_start"])
        loaded = api_budget.load(self.home)
        self.assertEqual(loaded["period"], "monthly")

    def test_set_budget_rejects_invalid_period(self) -> None:
        with self.assertRaises(ValueError) as cm:
            api_budget.set_api_budget(100.0, 10.0, period="invalid", home=self.home)
        self.assertIn("period must be one of", str(cm.exception))

    def test_period_start_returns_none_for_total(self) -> None:
        budget = {"period": "total"}
        ps = api_budget.period_start(budget)
        self.assertIsNone(ps)

    def test_period_start_returns_first_of_month_for_monthly(self) -> None:
        budget = {"period": "monthly"}
        test_date = datetime.datetime(2026, 5, 15, 12, 30, 45, tzinfo=timezone.utc)
        ps = api_budget.period_start(budget, now=test_date)
        self.assertEqual(ps, "2026-05-01T00:00:00+00:00")

    def test_period_start_defaults_to_total_when_missing(self) -> None:
        budget = {}
        ps = api_budget.period_start(budget)
        self.assertIsNone(ps)

    def test_api_spent_without_period_sums_all_spend(self) -> None:
        api_budget.set_api_budget(100.0, 10.0, home=self.home)
        api_budget.record_api_spend(2.5, call_id="call1", provider="anthropic", home=self.home)
        api_budget.record_api_spend(3.75, call_id="call2", provider="openai", home=self.home)
        total = api_budget.api_spent(self.home)
        self.assertAlmostEqual(total, 6.25, places=6)

    def test_api_spent_with_monthly_period_excludes_previous_month(self) -> None:
        api_budget.set_api_budget(100.0, 10.0, period="monthly", home=self.home)

        spend_path = self.home / "api-spend.jsonl"
        spend_path.parent.mkdir(parents=True, exist_ok=True)

        previous_month = datetime.datetime(2026, 9, 15, 10, 0, 0, tzinfo=timezone.utc)
        current_month = datetime.datetime(2026, 10, 1, 10, 0, 0, tzinfo=timezone.utc)

        with spend_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps({"at": previous_month.isoformat(), "call_id": "call1", "provider": "anthropic", "amount_usd": 5.0}) + "\n")
            f.write(json.dumps({"at": current_month.isoformat(), "call_id": "call2", "provider": "openai", "amount_usd": 3.0}) + "\n")

        period_start_str = api_budget.period_start({"period": "monthly"}, now=current_month)
        total = api_budget.api_spent(self.home, since=period_start_str)
        self.assertAlmostEqual(total, 3.0, places=6)

    def test_api_remaining_with_monthly_period(self) -> None:
        api_budget.set_api_budget(100.0, 10.0, period="monthly", home=self.home)

        spend_path = self.home / "api-spend.jsonl"
        spend_path.parent.mkdir(parents=True, exist_ok=True)

        previous_month = datetime.datetime(2026, 9, 15, 10, 0, 0, tzinfo=timezone.utc)
        current_month = datetime.datetime(2026, 10, 1, 10, 0, 0, tzinfo=timezone.utc)

        with spend_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps({"at": previous_month.isoformat(), "call_id": "call1", "provider": "anthropic", "amount_usd": 50.0}) + "\n")
            f.write(json.dumps({"at": current_month.isoformat(), "call_id": "call2", "provider": "openai", "amount_usd": 25.0}) + "\n")

        remaining = api_budget.api_remaining(self.home, now=current_month)
        self.assertAlmostEqual(remaining, 75.0, places=6)

    def test_check_with_monthly_period_includes_period(self) -> None:
        api_budget.set_api_budget(100.0, 10.0, period="monthly", home=self.home)
        result = api_budget.check(self.home)
        self.assertEqual(result["period"], "monthly")

    def test_check_with_exhausted_monthly_budget_says_this_month(self) -> None:
        api_budget.set_api_budget(10.0, 5.0, period="monthly", home=self.home)
        current_month = datetime.datetime(2026, 10, 1, 10, 0, 0, tzinfo=timezone.utc)

        spend_path = self.home / "api-spend.jsonl"
        spend_path.parent.mkdir(parents=True, exist_ok=True)
        with spend_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps({"at": current_month.isoformat(), "call_id": "call1", "provider": "anthropic", "amount_usd": 10.0}) + "\n")

        result = api_budget.check(self.home, now=current_month)
        self.assertFalse(result["allowed"])
        self.assertEqual(result["reason"], "API budget exhausted for this month")

    def test_api_spent_skips_entries_with_missing_at(self) -> None:
        api_budget.set_api_budget(100.0, 10.0, home=self.home)
        spend_path = self.home / "api-spend.jsonl"
        spend_path.parent.mkdir(parents=True, exist_ok=True)

        current_month = datetime.datetime(2026, 10, 1, 10, 0, 0, tzinfo=timezone.utc)
        period_start_str = api_budget.period_start({"period": "monthly"}, now=current_month)

        with spend_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps({"call_id": "call1", "provider": "anthropic", "amount_usd": 5.0}) + "\n")
            f.write(json.dumps({"at": current_month.isoformat(), "call_id": "call2", "provider": "openai", "amount_usd": 3.0}) + "\n")

        total = api_budget.api_spent(self.home, since=period_start_str)
        self.assertAlmostEqual(total, 3.0, places=6)

    def test_api_spent_skips_entries_with_unparseable_at(self) -> None:
        api_budget.set_api_budget(100.0, 10.0, home=self.home)
        spend_path = self.home / "api-spend.jsonl"
        spend_path.parent.mkdir(parents=True, exist_ok=True)

        current_month = datetime.datetime(2026, 10, 1, 10, 0, 0, tzinfo=timezone.utc)
        period_start_str = api_budget.period_start({"period": "monthly"}, now=current_month)

        with spend_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps({"at": "not-a-date", "call_id": "call1", "provider": "anthropic", "amount_usd": 5.0}) + "\n")
            f.write(json.dumps({"at": current_month.isoformat(), "call_id": "call2", "provider": "openai", "amount_usd": 3.0}) + "\n")

        total = api_budget.api_spent(self.home, since=period_start_str)
        self.assertAlmostEqual(total, 3.0, places=6)


if __name__ == "__main__":
    unittest.main()
