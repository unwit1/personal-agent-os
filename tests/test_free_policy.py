"""Tests for free-compute broker policy loading and quota management."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from unittest import mock
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import free_policy  # noqa: E402
from agent_os.orchestrator.store import HOME_ENV  # noqa: E402
from agent_os.storage import write_json  # noqa: E402


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class FreePolicyLoadTests(unittest.TestCase):
    """Test policy loading and merging."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        patcher = mock.patch.dict(os.environ, {HOME_ENV: str(self.home)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_load_canonical_policy(self) -> None:
        """Load the canonical policy from Git."""
        record = free_policy.load()
        self.assertEqual(record["schema_version"], "agent-os/provider-policy/v1")
        self.assertEqual(record["provider"], "openrouter")
        self.assertEqual(record["policy"], "free-model-allowance")
        self.assertEqual(record["version"], 1)
        self.assertIn("free_rpm", record)
        self.assertIn("daily_free_requests_low", record)
        self.assertIn("daily_free_requests_high", record)
        self.assertIn("credit_threshold_usd", record)

    def test_load_with_explicit_overrides(self) -> None:
        """Overrides passed explicitly take precedence."""
        overrides = {"daily_free_requests_low": 100, "free_rpm": 50}
        record = free_policy.load(overrides=overrides)
        self.assertEqual(record["daily_free_requests_low"], 100)
        self.assertEqual(record["free_rpm"], 50)
        self.assertIn("daily_free_requests_low", record["overridden"])
        self.assertIn("free_rpm", record["overridden"])

    def test_load_with_file_overrides(self) -> None:
        """Overrides from policy-overrides.json take precedence."""
        policy_overrides = {"daily_free_requests_high": 2000, "credit_threshold_usd": 20.0}
        overrides_file = self.home / "free-compute" / "policy-overrides.json"
        overrides_file.parent.mkdir(parents=True, exist_ok=True)
        write_json(overrides_file, policy_overrides)

        record = free_policy.load()
        self.assertEqual(record["daily_free_requests_high"], 2000)
        self.assertEqual(record["credit_threshold_usd"], 20.0)
        self.assertEqual(sorted(record["overridden"]), ["credit_threshold_usd", "daily_free_requests_high"])
        self.assertIn("daily_free_requests_high", record["overridden"])
        self.assertIn("credit_threshold_usd", record["overridden"])

    def test_missing_overrides_file_means_no_overrides(self) -> None:
        record = free_policy.load()
        self.assertEqual(record["overridden"], [])
        self.assertEqual(record["free_rpm"], 20)

    def test_corrupt_overrides_file_raises(self) -> None:
        overrides_file = self.home / "free-compute" / "policy-overrides.json"
        overrides_file.parent.mkdir(parents=True)
        overrides_file.write_text("{not json", encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            free_policy.load()
        self.assertIn("policy-overrides.json", str(ctx.exception))

    def test_non_object_overrides_file_raises(self) -> None:
        overrides_file = self.home / "free-compute" / "policy-overrides.json"
        overrides_file.parent.mkdir(parents=True)
        overrides_file.write_text("[1, 2]", encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            free_policy.load()
        self.assertIn("policy-overrides.json", str(ctx.exception))

    def test_overrides_with_none_value_are_ignored(self) -> None:
        """None values in overrides are not applied."""
        overrides = {"daily_free_requests_low": 100, "free_rpm": None}
        record = free_policy.load(overrides=overrides)
        self.assertEqual(record["daily_free_requests_low"], 100)
        self.assertIn("daily_free_requests_low", record["overridden"])
        self.assertNotIn("free_rpm", record["overridden"])

    def test_invalid_policy_file_raises_error(self) -> None:
        """Invalid policy file raises ValueError."""
        invalid_file = self.home / "invalid-policy.json"
        write_json(invalid_file, {"not": "a valid policy"})
        with self.assertRaises(ValueError):
            free_policy.load(path=invalid_file)

    def test_empty_versions_raises_error(self) -> None:
        """Policy history with no versions raises ValueError."""
        invalid_file = self.home / "empty-policy.json"
        write_json(invalid_file, {"schema_version": "agent-os/provider-policy-history/v1", "versions": []})
        with self.assertRaises(ValueError):
            free_policy.load(path=invalid_file)


class FreePolicyStalenessTests(unittest.TestCase):
    """Test staleness checking."""

    def test_fresh_policy_is_not_stale(self) -> None:
        """A policy verified today is not stale."""
        record = {
            "verified_at": "2026-10-01T12:00:00Z",
            "max_age_days": 30,
        }
        self.assertFalse(free_policy.is_stale(record, now=_dt("2026-10-01T13:00:00Z")))

    def test_policy_at_max_age_boundary(self) -> None:
        """A policy exactly at max age is not stale."""
        record = {
            "verified_at": "2026-09-01T00:00:00Z",
            "max_age_days": 30,
        }
        # Exactly 30 days later should not be stale
        self.assertFalse(free_policy.is_stale(record, now=_dt("2026-10-01T00:00:00Z")))

    def test_policy_past_max_age_is_stale(self) -> None:
        """A policy past max age is stale."""
        record = {
            "verified_at": "2026-09-01T00:00:00Z",
            "max_age_days": 30,
        }
        # One day after max age
        self.assertTrue(free_policy.is_stale(record, now=_dt("2026-10-01T00:01:00Z")))

    def test_stale_policy_uses_default_max_age(self) -> None:
        """Missing max_age_days defaults to 30."""
        record = {
            "verified_at": "2026-08-01T00:00:00Z",
        }
        # 61 days old, default 30-day max age
        self.assertTrue(free_policy.is_stale(record, now=_dt("2026-09-30T00:00:00Z")))

    def test_stale_policy_with_explicit_max_age(self) -> None:
        """Explicit max_age_days parameter overrides record."""
        record = {
            "verified_at": "2026-09-01T00:00:00Z",
            "max_age_days": 30,
        }
        # 10 days old, but max_age_days=5 passed explicitly
        self.assertTrue(free_policy.is_stale(record, now=_dt("2026-09-11T00:00:00Z"), max_age_days=5))

    def test_missing_verified_at_is_stale(self) -> None:
        """A record with no verified_at is considered stale."""
        record: dict = {}
        self.assertTrue(free_policy.is_stale(record, now=_dt("2026-10-02T00:00:00Z")))

    def test_invalid_verified_at_is_stale(self) -> None:
        """A record with invalid verified_at is considered stale."""
        record = {"verified_at": "not-a-date"}
        self.assertTrue(free_policy.is_stale(record, now=_dt("2026-10-02T00:00:00Z")))

    def test_naive_now_is_treated_as_utc(self) -> None:
        record = {"verified_at": "2026-10-01T00:00:00Z", "max_age_days": 30}
        self.assertFalse(free_policy.is_stale(record, now=datetime(2026, 10, 2)))


class FreePolicyAllowanceTests(unittest.TestCase):
    """Test quota allowance computation."""

    def test_allowance_high_tier(self) -> None:
        """High tier returns high allowance."""
        record = {
            "daily_free_requests_high": 1000,
            "daily_free_requests_low": 50,
            "free_rpm": 20,
        }
        result = free_policy.allowance(record, high_tier=True)
        self.assertEqual(result["daily"], 1000)
        self.assertEqual(result["rpm"], 20)

    def test_allowance_low_tier(self) -> None:
        """Low tier returns low allowance."""
        record = {
            "daily_free_requests_high": 1000,
            "daily_free_requests_low": 50,
            "free_rpm": 20,
        }
        result = free_policy.allowance(record, high_tier=False)
        self.assertEqual(result["daily"], 50)
        self.assertEqual(result["rpm"], 20)

    def test_allowance_returns_integers(self) -> None:
        """Allowance values are returned as integers."""
        record = {
            "daily_free_requests_high": 1000.5,
            "daily_free_requests_low": 50.7,
            "free_rpm": 20.9,
        }
        result = free_policy.allowance(record, high_tier=True)
        self.assertIsInstance(result["daily"], int)
        self.assertIsInstance(result["rpm"], int)
        self.assertEqual(result["daily"], 1000)
        self.assertEqual(result["rpm"], 20)

    def test_allowance_missing_field_raises_error(self) -> None:
        """Missing allowance fields raise ValueError."""
        record = {"daily_free_requests_high": 1000}
        with self.assertRaises(ValueError):
            free_policy.allowance(record, high_tier=True)

    def test_allowance_missing_rpm_raises_error(self) -> None:
        """Missing free_rpm raises ValueError."""
        record = {
            "daily_free_requests_high": 1000,
            "daily_free_requests_low": 50,
        }
        with self.assertRaises(ValueError):
            free_policy.allowance(record, high_tier=True)


class FreePolicyIntegrationTests(unittest.TestCase):
    """Integration tests combining load, staleness, and allowance."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        patcher = mock.patch.dict(os.environ, {HOME_ENV: str(self.home)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_load_fresh_policy_and_get_allowance(self) -> None:
        """Load a fresh policy and compute allowance for both tiers."""
        record = free_policy.load()
        self.assertFalse(free_policy.is_stale(record, now=_dt("2026-10-02T00:00:00Z")))

        high = free_policy.allowance(record, high_tier=True)
        low = free_policy.allowance(record, high_tier=False)

        self.assertGreater(high["daily"], low["daily"])
        self.assertEqual(high["rpm"], low["rpm"])

    def test_overridden_policy_staleness_and_allowance(self) -> None:
        """Stale policy with overrides still uses overridden values."""
        overrides = {"daily_free_requests_high": 5000, "daily_free_requests_low": 200}
        record = free_policy.load(overrides=overrides)

        # Make it stale manually
        record["verified_at"] = "2026-01-01T00:00:00Z"

        self.assertTrue(free_policy.is_stale(record, now=_dt("2026-10-02T00:00:00Z")))
        high = free_policy.allowance(record, high_tier=True)
        low = free_policy.allowance(record, high_tier=False)

        self.assertEqual(high["daily"], 5000)
        self.assertEqual(low["daily"], 200)

    def test_override_file_merge_with_staleness(self) -> None:
        """Override file is loaded and merged correctly."""
        # Create an overrides file
        policy_overrides = {"daily_free_requests_high": 2000}
        overrides_file = self.home / "free-compute" / "policy-overrides.json"
        overrides_file.parent.mkdir(parents=True, exist_ok=True)
        write_json(overrides_file, policy_overrides)

        # Load with overrides
        record = free_policy.load()

        self.assertEqual(record["daily_free_requests_high"], 2000)
        self.assertFalse(free_policy.is_stale(record, now=_dt("2026-10-02T00:00:00Z")))


if __name__ == "__main__":
    unittest.main()
