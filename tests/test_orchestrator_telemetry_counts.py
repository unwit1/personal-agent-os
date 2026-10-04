"""Tests for _telemetry_token_counts token extraction and validation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator.engine import _telemetry_token_counts  # noqa: E402
from agent_os.orchestrator import usage  # noqa: E402
from agent_os.telemetry import TelemetryEvent  # noqa: E402


class TelemetryTokenCountsTests(unittest.TestCase):
    def test_exact_usage_extracts_all_token_counts(self) -> None:
        usage_dict = usage.normalized(
            total_input=100,
            cache_read=20,
            output=30,
            reasoning=5,
            source="test",
        )
        result = _telemetry_token_counts(usage_dict)
        self.assertEqual(result, {
            "input_tokens": 100,
            "cached_tokens": 20,
            "reasoning_tokens": 5,
            "output_tokens": 30,
        })

    def test_estimated_accuracy_gives_all_none(self) -> None:
        usage_dict = usage.normalized(
            total_input=100,
            cache_read=20,
            output=30,
            reasoning=5,
            source="test",
            accuracy="estimated",
        )
        result = _telemetry_token_counts(usage_dict)
        self.assertEqual(result, {
            "input_tokens": None,
            "cached_tokens": None,
            "reasoning_tokens": None,
            "output_tokens": None,
        })

    def test_unavailable_usage_gives_all_none(self) -> None:
        unavail = usage.unavailable("test")
        result = _telemetry_token_counts(unavail)
        self.assertEqual(result, {
            "input_tokens": None,
            "cached_tokens": None,
            "reasoning_tokens": None,
            "output_tokens": None,
        })

    def test_empty_dict_gives_all_none(self) -> None:
        result = _telemetry_token_counts({})
        self.assertEqual(result, {
            "input_tokens": None,
            "cached_tokens": None,
            "reasoning_tokens": None,
            "output_tokens": None,
        })

    def test_none_usage_gives_all_none(self) -> None:
        result = _telemetry_token_counts(None)
        self.assertEqual(result, {
            "input_tokens": None,
            "cached_tokens": None,
            "reasoning_tokens": None,
            "output_tokens": None,
        })

    def test_legacy_dict_with_cached_tokens(self) -> None:
        legacy = {"accuracy": "exact", "input_tokens": 10, "cached_tokens": 3, "output_tokens": 4}
        result = _telemetry_token_counts(legacy)
        self.assertEqual(result["input_tokens"], 10)
        self.assertEqual(result["cached_tokens"], 3)
        self.assertEqual(result["output_tokens"], 4)
        self.assertIsNone(result["reasoning_tokens"])

    def test_cache_read_tokens_takes_precedence_over_cached_tokens(self) -> None:
        usage_dict = usage.normalized(
            total_input=100,
            cache_read=20,
            output=30,
            source="test",
        )
        result = _telemetry_token_counts(usage_dict)
        self.assertEqual(result["cached_tokens"], 20)

    def test_falls_back_to_cached_tokens_when_cache_read_is_none(self) -> None:
        # Build a dict with cached_tokens but no cache_read_tokens
        usage_dict = {
            "accuracy": "exact",
            "input_tokens": 100,
            "cache_read_tokens": None,
            "cached_tokens": 15,
            "output_tokens": 30,
        }
        result = _telemetry_token_counts(usage_dict)
        self.assertEqual(result["cached_tokens"], 15)

    def test_invalid_token_values_become_none(self) -> None:
        usage_dict = {
            "accuracy": "exact",
            "input_tokens": "not-an-int",
            "cached_tokens": True,
            "output_tokens": -5,
        }
        result = _telemetry_token_counts(usage_dict)
        self.assertIsNone(result["input_tokens"])
        self.assertIsNone(result["cached_tokens"])
        self.assertIsNone(result["output_tokens"])

    def test_result_can_be_passed_to_telemetry_event(self) -> None:
        usage_dict = usage.normalized(
            total_input=100,
            cache_read=20,
            output=30,
            reasoning=5,
            source="test",
        )
        counts = _telemetry_token_counts(usage_dict)
        # This should not raise any exceptions
        event = TelemetryEvent(
            project_id="test-project",
            task_category="orchestrator-implementer",
            **counts
        )
        self.assertEqual(event.input_tokens, 100)
        self.assertEqual(event.cached_tokens, 20)
        self.assertEqual(event.reasoning_tokens, 5)
        self.assertEqual(event.output_tokens, 30)

    def test_zero_tokens_are_valid(self) -> None:
        usage_dict = {
            "accuracy": "exact",
            "input_tokens": 0,
            "cached_tokens": 0,
            "reasoning_tokens": 0,
            "output_tokens": 0,
        }
        result = _telemetry_token_counts(usage_dict)
        self.assertEqual(result["input_tokens"], 0)
        self.assertEqual(result["cached_tokens"], 0)
        self.assertEqual(result["reasoning_tokens"], 0)
        self.assertEqual(result["output_tokens"], 0)

    def test_float_becomes_none(self) -> None:
        """R1-1: A float (3.7) should become None (not coerced to 3)."""
        usage_dict = {
            "accuracy": "exact",
            "input_tokens": 3.7,
        }
        result = _telemetry_token_counts(usage_dict)
        self.assertIsNone(result["input_tokens"])

    def test_numeric_string_becomes_none(self) -> None:
        """R1-1: A numeric string ('5') should become None (not coerced to 5)."""
        usage_dict = {
            "accuracy": "exact",
            "input_tokens": "5",
        }
        result = _telemetry_token_counts(usage_dict)
        self.assertIsNone(result["input_tokens"])


if __name__ == "__main__":
    unittest.main()
