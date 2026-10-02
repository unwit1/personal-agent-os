import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import free_metrics

T0 = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)
MODEL1 = "example-org/example-model:free"
MODEL2 = "other-org/other-model:free"
FAMILY1 = "unit_test_generation"
FAMILY2 = "documentation"


def make_event(
    ts=None,
    model=MODEL1,
    task_family=FAMILY1,
    outcome="success",
    validator_passed=True,
    accepted=True,
    escalated=False,
    useful_units=1,
    retry=0,
    tokens=None,
    event_id=None,
):
    """Create a synthetic ledger event."""
    if tokens is None:
        tokens = {"input": 1000, "output": 500}
    return {
        "schema_version": "agent-os/free-quota-event/v1",
        "event_id": event_id or f"FQE-{len(repr(model))}",
        "ts": (ts or T0).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model": model,
        "revision": f"{model}-rev-1",
        "task_family": task_family,
        "run_id": "run-test",
        "node_id": "test",
        "outcome": outcome,
        "http_status": 200,
        "retry": retry,
        "escalated": escalated,
        "validator_passed": validator_passed,
        "accepted": accepted,
        "useful_units": useful_units,
        "latency_ms": 1000,
        "tokens": tokens,
        "lane": "priority",
    }


def make_verdict(event_id, validator_passed=None, accepted=None, escalated=None):
    """Create a verdict event to update an attempt."""
    verdict = {
        "type": "verdict",
        "event_id": event_id,
        "ts": T0.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if validator_passed is not None:
        verdict["validator_passed"] = validator_passed
    if accepted is not None:
        verdict["accepted"] = accepted
    if escalated is not None:
        verdict["escalated"] = escalated
    return verdict


class FreeMetricsTests(unittest.TestCase):
    def test_zero_requests_no_division_error(self):
        """Empty ledger should return zero without division errors."""
        result = free_metrics.report([])
        self.assertEqual(result["requests"], 0)
        self.assertIsNone(result["useful_progress_per_request"])
        self.assertIsNone(result["validator_acceptance"])
        self.assertIsNone(result["review_acceptance"])
        self.assertEqual(result["retries"], 0)
        self.assertEqual(result["escalations"], 0)
        self.assertEqual(result["paid_fallbacks_avoided"], 0)
        self.assertIsNone(result["estimated_paid_cost_avoided_usd"])

    def test_basic_metrics(self):
        """Calculate basic metrics from a simple ledger."""
        events = [
            make_event(validator_passed=True, accepted=True, escalated=False, useful_units=1),
            make_event(validator_passed=True, accepted=True, escalated=False, useful_units=1),
            make_event(validator_passed=False, accepted=False, escalated=False, useful_units=0),
        ]
        result = free_metrics.report(events)
        self.assertEqual(result["requests"], 3)
        self.assertEqual(result["useful_progress_per_request"], round(2 / 3, 3))
        # 2 passed validators out of 3 non-null = 2/3 = 0.667
        self.assertEqual(result["validator_acceptance"], round(2 / 3, 3))
        # 2 accepted out of 3 non-null = 2/3 = 0.667
        self.assertEqual(result["review_acceptance"], round(2 / 3, 3))
        self.assertEqual(result["paid_fallbacks_avoided"], 2)

    def test_retries_counted(self):
        """Count retry attempts (retry > 0)."""
        events = [
            make_event(retry=0),
            make_event(retry=1),
            make_event(retry=2),
            make_event(retry=0),
        ]
        result = free_metrics.report(events)
        self.assertEqual(result["retries"], 2)

    def test_escalations_counted(self):
        """Count escalated requests."""
        events = [
            make_event(escalated=False),
            make_event(escalated=True),
            make_event(escalated=True),
            make_event(escalated=False),
        ]
        result = free_metrics.report(events)
        self.assertEqual(result["escalations"], 2)

    def test_paid_fallbacks_avoided(self):
        """Only count accepted + not escalated as fallbacks avoided."""
        events = [
            make_event(accepted=True, escalated=False),  # counts
            make_event(accepted=True, escalated=True),   # escalated, doesn't count
            make_event(accepted=False, escalated=False), # not accepted, doesn't count
            make_event(accepted=True, escalated=False),  # counts
        ]
        result = free_metrics.report(events)
        self.assertEqual(result["paid_fallbacks_avoided"], 2)

    def test_estimated_cost_with_prices(self):
        """Calculate estimated paid cost avoided with prices."""
        prices = {
            MODEL1: {"input": 0.003, "cached_input": 0.0009, "output": 0.012},
            MODEL2: {"input": 0.005, "output": 0.015},
        }
        events = [
            make_event(
                model=MODEL1,
                accepted=True,
                escalated=False,
                tokens={"input": 1000, "output": 500},
            ),
            make_event(
                model=MODEL1,
                accepted=True,
                escalated=False,
                tokens={"input": 2000, "output": 1000},
            ),
        ]
        result = free_metrics.report(events, prices=prices)
        # (1000 * 0.003 + 500 * 0.012) / 1e6 + (2000 * 0.003 + 1000 * 0.012) / 1e6
        # = (3 + 6) / 1e6 + (6 + 12) / 1e6 = 9 / 1e6 + 18 / 1e6 = 0.000027
        expected = round((1000 * 0.003 + 500 * 0.012 + 2000 * 0.003 + 1000 * 0.012) / 1e6, 2)
        self.assertEqual(result["estimated_paid_cost_avoided_usd"], expected)

    def test_missing_price_error(self):
        """Report when model prices are missing."""
        prices = {MODEL1: {"input": 0.001, "output": 0.002}}
        events = [
            make_event(model=MODEL1, accepted=True, escalated=False),
            make_event(model=MODEL2, accepted=True, escalated=False),
        ]
        result = free_metrics.report(events, prices=prices)
        # Cost should still be calculated for MODEL1, but error recorded for MODEL2
        self.assertIsNotNone(result["estimated_paid_cost_avoided_usd"])
        self.assertTrue(
            any("no price data" in str(err) for err in result["errors"]),
            f"Expected missing price error, got {result['errors']}"
        )

    def test_no_prices_dict(self):
        """When prices dict is None, cost avoided is None."""
        events = [
            make_event(accepted=True, escalated=False),
        ]
        result = free_metrics.report(events, prices=None)
        self.assertIsNone(result["estimated_paid_cost_avoided_usd"])
        self.assertIsNone(result["estimated_paid_cost_basis"])

    def test_verdict_updates_attempt(self):
        """Verdict events update attempt fields."""
        event_id = "FQE-test-001"
        attempt = make_event(
            event_id=event_id,
            validator_passed=None,
            accepted=None,
            escalated=None,
        )
        verdict = make_verdict(
            event_id,
            validator_passed=True,
            accepted=True,
            escalated=False,
        )
        result = free_metrics.report([attempt, verdict])
        self.assertEqual(result["validator_acceptance"], 1.0)
        self.assertEqual(result["review_acceptance"], 1.0)
        self.assertEqual(result["paid_fallbacks_avoided"], 1)

    def test_multiple_verdicts_last_wins(self):
        """Last verdict for an event_id wins."""
        event_id = "FQE-test-002"
        attempt = make_event(event_id=event_id, accepted=None)
        verdict1 = make_verdict(event_id, accepted=True)
        verdict2 = make_verdict(event_id, accepted=False)
        result = free_metrics.report([attempt, verdict1, verdict2])
        # The final state should have accepted=False
        self.assertEqual(result["paid_fallbacks_avoided"], 0)

    def test_by_task_family(self):
        """Breakdown by task family."""
        events = [
            make_event(task_family=FAMILY1, accepted=True, useful_units=1),
            make_event(task_family=FAMILY1, accepted=False, useful_units=0),
            make_event(task_family=FAMILY2, accepted=True, useful_units=2),
        ]
        result = free_metrics.report(events)
        by_fam = result["by_task_family"]
        self.assertIn(FAMILY1, by_fam)
        self.assertIn(FAMILY2, by_fam)
        self.assertEqual(by_fam[FAMILY1]["requests"], 2)
        self.assertEqual(by_fam[FAMILY1]["accepted"], 1)
        self.assertEqual(by_fam[FAMILY1]["useful_units"], 1)
        self.assertEqual(by_fam[FAMILY2]["requests"], 1)
        self.assertEqual(by_fam[FAMILY2]["accepted"], 1)
        self.assertEqual(by_fam[FAMILY2]["useful_units"], 2)

    def test_by_model(self):
        """Breakdown by model."""
        events = [
            make_event(model=MODEL1, accepted=True, useful_units=1),
            make_event(model=MODEL1, accepted=False, useful_units=0),
            make_event(model=MODEL2, accepted=True, useful_units=2),
        ]
        result = free_metrics.report(events)
        by_mdl = result["by_model"]
        self.assertIn(MODEL1, by_mdl)
        self.assertIn(MODEL2, by_mdl)
        self.assertEqual(by_mdl[MODEL1]["requests"], 2)
        self.assertEqual(by_mdl[MODEL1]["accepted"], 1)
        self.assertEqual(by_mdl[MODEL1]["useful_units"], 1)
        self.assertEqual(by_mdl[MODEL2]["requests"], 1)
        self.assertEqual(by_mdl[MODEL2]["accepted"], 1)
        self.assertEqual(by_mdl[MODEL2]["useful_units"], 2)

    def test_validator_acceptance_only_non_null(self):
        """Validator acceptance rate only counts where validator_passed is non-null."""
        events = [
            make_event(validator_passed=True),
            make_event(validator_passed=True),
            make_event(validator_passed=False),
            make_event(validator_passed=None),  # not counted in rate
            make_event(validator_passed=None),  # not counted in rate
        ]
        result = free_metrics.report(events)
        # 2 passed out of 3 non-null = 0.667
        self.assertEqual(result["validator_acceptance"], round(2 / 3, 3))

    def test_review_acceptance_only_non_null(self):
        """Review acceptance rate only counts where accepted is non-null."""
        events = [
            make_event(accepted=True),
            make_event(accepted=True),
            make_event(accepted=False),
            make_event(accepted=None),  # not counted in rate
            make_event(accepted=None),  # not counted in rate
        ]
        result = free_metrics.report(events)
        # 2 accepted out of 3 non-null = 0.667
        self.assertEqual(result["review_acceptance"], round(2 / 3, 3))

    def test_read_ledger_from_file(self):
        """read_ledger loads events from a real jsonl file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            ledger_path = home / "free-compute" / "ledger.jsonl"
            ledger_path.parent.mkdir(parents=True)

            events = [
                make_event(event_id="FQE-001"),
                make_event(event_id="FQE-002"),
            ]
            with ledger_path.open("w") as f:
                for evt in events:
                    f.write(__import__("json").dumps(evt) + "\n")

            loaded = free_metrics.read_ledger(home)
            self.assertEqual(len(loaded), 2)
            self.assertEqual(loaded[0]["event_id"], "FQE-001")
            self.assertEqual(loaded[1]["event_id"], "FQE-002")

    def test_read_ledger_nonexistent(self):
        """read_ledger returns empty list if ledger doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            loaded = free_metrics.read_ledger(home)
            self.assertEqual(loaded, [])

    def test_useful_units_default_zero(self):
        """useful_units defaults to 0 when absent."""
        events = [
            make_event(useful_units=2),
            make_event(useful_units=None),  # treated as 0
            make_event(),  # absent, treated as 0 by default creation
        ]
        # Remove useful_units from second event
        events[1].pop("useful_units", None)
        events[2].pop("useful_units", None)

        result = free_metrics.report(events)
        # Only first event has useful_units=2
        self.assertEqual(result["useful_progress_per_request"], round(2 / 3, 3))

    def test_tokens_missing_gracefully(self):
        """Missing tokens are handled gracefully in cost calculation."""
        prices = {MODEL1: {"input": 0.001, "output": 0.002}}
        events = [
            make_event(accepted=True, escalated=False, tokens=None),
        ]
        # Remove tokens from the event
        events[0].pop("tokens", None)
        result = free_metrics.report(events, prices=prices)
        # No cost calculated (no tokens), returns None
        self.assertIsNone(result["estimated_paid_cost_avoided_usd"])

    def test_schema_version(self):
        """Report includes schema version."""
        result = free_metrics.report([])
        self.assertEqual(result["schema_version"], "agent-os/free-metrics/v1")

    def test_cost_basis_included(self):
        """Cost basis is included when prices are provided."""
        prices = {MODEL1: {"input": 0.001, "output": 0.002}}
        events = [make_event(accepted=True, escalated=False)]
        result = free_metrics.report(events, prices=prices)
        self.assertIsNotNone(result["estimated_paid_cost_basis"])
        self.assertIn("cheapest paid route", result["estimated_paid_cost_basis"])


if __name__ == "__main__":
    unittest.main()
