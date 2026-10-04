from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.telemetry import (  # noqa: E402
    PROVIDER_USAGE_FORMATS,
    TelemetryPrivacyError,
    token_counts_from_provider_usage,
)


class ProviderUsageAdapterTests(unittest.TestCase):
    """Test token_counts_from_provider_usage adapter for all provider formats."""

    def test_provider_usage_formats_constant_exists(self) -> None:
        self.assertEqual(
            PROVIDER_USAGE_FORMATS,
            ("anthropic", "openai-chat", "openai-responses", "normalized"),
        )

    def test_invalid_usage_format_raises_telemetry_privacy_error(self) -> None:
        with self.assertRaises(TelemetryPrivacyError) as ctx:
            token_counts_from_provider_usage({}, "invalid-format")
        self.assertIn("unsupported provider usage format", str(ctx.exception))
        self.assertIn("invalid-format", str(ctx.exception))

    def test_none_usage_returns_all_none(self) -> None:
        result = token_counts_from_provider_usage(None, "normalized")
        self.assertEqual(
            result,
            {
                "input_tokens": None,
                "cached_tokens": None,
                "reasoning_tokens": None,
                "output_tokens": None,
            },
        )

    def test_falsy_usage_returns_all_none(self) -> None:
        result = token_counts_from_provider_usage({}, "anthropic")
        self.assertEqual(
            result,
            {
                "input_tokens": None,
                "cached_tokens": None,
                "reasoning_tokens": None,
                "output_tokens": None,
            },
        )

    def test_non_mapping_usage_returns_all_none(self) -> None:
        result = token_counts_from_provider_usage("not a mapping", "openai-chat")  # type: ignore
        self.assertEqual(
            result,
            {
                "input_tokens": None,
                "cached_tokens": None,
                "reasoning_tokens": None,
                "output_tokens": None,
            },
        )

    def test_usage_key_extracts_inner_mapping(self) -> None:
        usage = {
            "usage": {
                "input_tokens": 10,
                "output_tokens": 5,
            },
            "other_field": "should be ignored",
        }
        result = token_counts_from_provider_usage(usage, "openai-responses")
        self.assertEqual(result["input_tokens"], 10)
        self.assertEqual(result["output_tokens"], 5)

    def test_usage_key_non_mapping_is_ignored(self) -> None:
        usage = {
            "usage": "not a mapping",
            "input_tokens": 10,
            "output_tokens": 5,
        }
        result = token_counts_from_provider_usage(usage, "openai-responses")
        self.assertEqual(result["input_tokens"], 10)
        self.assertEqual(result["output_tokens"], 5)

    def test_normalized_format_requires_exact_accuracy(self) -> None:
        usage = {
            "accuracy": "estimated",
            "input_tokens": 10,
            "output_tokens": 5,
        }
        result = token_counts_from_provider_usage(usage, "normalized")
        self.assertEqual(
            result,
            {
                "input_tokens": None,
                "cached_tokens": None,
                "reasoning_tokens": None,
                "output_tokens": None,
            },
        )

    def test_normalized_format_with_exact_accuracy(self) -> None:
        usage = {
            "accuracy": "exact",
            "input_tokens": 10,
            "cached_tokens": 3,
            "reasoning_tokens": 2,
            "output_tokens": 5,
        }
        result = token_counts_from_provider_usage(usage, "normalized")
        self.assertEqual(result["input_tokens"], 10)
        self.assertEqual(result["cached_tokens"], 3)
        self.assertEqual(result["reasoning_tokens"], 2)
        self.assertEqual(result["output_tokens"], 5)

    def test_normalized_format_cache_read_tokens_preferred(self) -> None:
        usage = {
            "accuracy": "exact",
            "input_tokens": 10,
            "cache_read_tokens": 3,
            "cached_tokens": 999,
            "output_tokens": 5,
        }
        result = token_counts_from_provider_usage(usage, "normalized")
        self.assertEqual(result["cached_tokens"], 3)

    def test_normalized_format_cached_tokens_fallback(self) -> None:
        usage = {
            "accuracy": "exact",
            "input_tokens": 10,
            "cached_tokens": 3,
            "output_tokens": 5,
        }
        result = token_counts_from_provider_usage(usage, "normalized")
        self.assertEqual(result["cached_tokens"], 3)

    def test_normalized_format_missing_accuracy_returns_none(self) -> None:
        usage = {
            "input_tokens": 10,
            "output_tokens": 5,
        }
        result = token_counts_from_provider_usage(usage, "normalized")
        self.assertEqual(
            result,
            {
                "input_tokens": None,
                "cached_tokens": None,
                "reasoning_tokens": None,
                "output_tokens": None,
            },
        )

    def test_anthropic_format_basic(self) -> None:
        usage = {
            "input_tokens": 100,
            "output_tokens": 50,
        }
        result = token_counts_from_provider_usage(usage, "anthropic")
        self.assertEqual(result["input_tokens"], 100)
        self.assertEqual(result["cached_tokens"], 0)
        self.assertEqual(result["reasoning_tokens"], None)
        self.assertEqual(result["output_tokens"], 50)

    def test_anthropic_format_with_cache_read(self) -> None:
        usage = {
            "input_tokens": 100,
            "cache_read_input_tokens": 25,
            "output_tokens": 50,
        }
        result = token_counts_from_provider_usage(usage, "anthropic")
        self.assertEqual(result["input_tokens"], 125)
        self.assertEqual(result["cached_tokens"], 25)
        self.assertEqual(result["reasoning_tokens"], None)
        self.assertEqual(result["output_tokens"], 50)

    def test_anthropic_format_with_cache_creation(self) -> None:
        usage = {
            "input_tokens": 100,
            "cache_creation_input_tokens": 30,
            "output_tokens": 50,
        }
        result = token_counts_from_provider_usage(usage, "anthropic")
        self.assertEqual(result["input_tokens"], 130)
        self.assertEqual(result["cached_tokens"], 0)
        self.assertEqual(result["reasoning_tokens"], None)
        self.assertEqual(result["output_tokens"], 50)

    def test_anthropic_format_with_both_cache_types(self) -> None:
        usage = {
            "input_tokens": 100,
            "cache_read_input_tokens": 25,
            "cache_creation_input_tokens": 30,
            "output_tokens": 50,
        }
        result = token_counts_from_provider_usage(usage, "anthropic")
        self.assertEqual(result["input_tokens"], 155)
        self.assertEqual(result["cached_tokens"], 25)
        self.assertEqual(result["reasoning_tokens"], None)
        self.assertEqual(result["output_tokens"], 50)

    def test_anthropic_format_missing_input_tokens_returns_all_none(self) -> None:
        usage = {
            "cache_read_input_tokens": 25,
            "output_tokens": 50,
        }
        result = token_counts_from_provider_usage(usage, "anthropic")
        self.assertEqual(
            result,
            {
                "input_tokens": None,
                "cached_tokens": None,
                "reasoning_tokens": None,
                "output_tokens": None,
            },
        )

    def test_anthropic_format_invalid_cache_fields_treated_as_zero(self) -> None:
        usage = {
            "input_tokens": 100,
            "cache_read_input_tokens": "invalid",
            "cache_creation_input_tokens": True,
            "output_tokens": 50,
        }
        result = token_counts_from_provider_usage(usage, "anthropic")
        self.assertEqual(result["input_tokens"], 100)
        self.assertEqual(result["cached_tokens"], 0)

    def test_openai_chat_format_basic(self) -> None:
        usage = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
        }
        result = token_counts_from_provider_usage(usage, "openai-chat")
        self.assertEqual(result["input_tokens"], 100)
        self.assertEqual(result["cached_tokens"], None)
        self.assertEqual(result["reasoning_tokens"], None)
        self.assertEqual(result["output_tokens"], 50)

    def test_openai_chat_format_with_details(self) -> None:
        usage = {
            "prompt_tokens": 100,
            "prompt_tokens_details": {
                "cached_tokens": 30,
            },
            "completion_tokens": 50,
            "completion_tokens_details": {
                "reasoning_tokens": 10,
            },
        }
        result = token_counts_from_provider_usage(usage, "openai-chat")
        self.assertEqual(result["input_tokens"], 100)
        self.assertEqual(result["cached_tokens"], 30)
        self.assertEqual(result["reasoning_tokens"], 10)
        self.assertEqual(result["output_tokens"], 50)

    def test_openai_chat_format_missing_details(self) -> None:
        usage = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
        }
        result = token_counts_from_provider_usage(usage, "openai-chat")
        self.assertEqual(result["input_tokens"], 100)
        self.assertEqual(result["cached_tokens"], None)
        self.assertEqual(result["reasoning_tokens"], None)
        self.assertEqual(result["output_tokens"], 50)

    def test_openai_chat_format_non_mapping_details(self) -> None:
        usage = {
            "prompt_tokens": 100,
            "prompt_tokens_details": "not a mapping",
            "completion_tokens": 50,
            "completion_tokens_details": "also not a mapping",
        }
        result = token_counts_from_provider_usage(usage, "openai-chat")
        self.assertEqual(result["input_tokens"], 100)
        self.assertEqual(result["cached_tokens"], None)
        self.assertEqual(result["reasoning_tokens"], None)
        self.assertEqual(result["output_tokens"], 50)

    def test_openai_responses_format_basic(self) -> None:
        usage = {
            "input_tokens": 100,
            "output_tokens": 50,
        }
        result = token_counts_from_provider_usage(usage, "openai-responses")
        self.assertEqual(result["input_tokens"], 100)
        self.assertEqual(result["cached_tokens"], None)
        self.assertEqual(result["reasoning_tokens"], None)
        self.assertEqual(result["output_tokens"], 50)

    def test_openai_responses_format_with_details(self) -> None:
        usage = {
            "input_tokens": 100,
            "input_tokens_details": {
                "cached_tokens": 30,
            },
            "output_tokens": 50,
            "output_tokens_details": {
                "reasoning_tokens": 10,
            },
        }
        result = token_counts_from_provider_usage(usage, "openai-responses")
        self.assertEqual(result["input_tokens"], 100)
        self.assertEqual(result["cached_tokens"], 30)
        self.assertEqual(result["reasoning_tokens"], 10)
        self.assertEqual(result["output_tokens"], 50)

    def test_openai_responses_format_missing_details(self) -> None:
        usage = {
            "input_tokens": 100,
            "output_tokens": 50,
        }
        result = token_counts_from_provider_usage(usage, "openai-responses")
        self.assertEqual(result["input_tokens"], 100)
        self.assertEqual(result["cached_tokens"], None)
        self.assertEqual(result["reasoning_tokens"], None)
        self.assertEqual(result["output_tokens"], 50)

    def test_openai_responses_format_non_mapping_details(self) -> None:
        usage = {
            "input_tokens": 100,
            "input_tokens_details": "not a mapping",
            "output_tokens": 50,
            "output_tokens_details": "also not a mapping",
        }
        result = token_counts_from_provider_usage(usage, "openai-responses")
        self.assertEqual(result["input_tokens"], 100)
        self.assertEqual(result["cached_tokens"], None)
        self.assertEqual(result["reasoning_tokens"], None)
        self.assertEqual(result["output_tokens"], 50)

    def test_boolean_values_are_invalid(self) -> None:
        usage = {
            "accuracy": "exact",
            "input_tokens": True,
            "output_tokens": False,
        }
        result = token_counts_from_provider_usage(usage, "normalized")
        self.assertEqual(result["input_tokens"], None)
        self.assertEqual(result["output_tokens"], None)

    def test_negative_values_are_invalid(self) -> None:
        usage = {
            "accuracy": "exact",
            "input_tokens": -10,
            "output_tokens": -5,
        }
        result = token_counts_from_provider_usage(usage, "normalized")
        self.assertEqual(result["input_tokens"], None)
        self.assertEqual(result["output_tokens"], None)

    def test_string_values_are_invalid(self) -> None:
        usage = {
            "accuracy": "exact",
            "input_tokens": "ten",
            "output_tokens": "five",
        }
        result = token_counts_from_provider_usage(usage, "normalized")
        self.assertEqual(result["input_tokens"], None)
        self.assertEqual(result["output_tokens"], None)

    def test_float_values_are_invalid(self) -> None:
        usage = {
            "accuracy": "exact",
            "input_tokens": 10.5,
            "output_tokens": 5.2,
        }
        result = token_counts_from_provider_usage(usage, "normalized")
        self.assertEqual(result["input_tokens"], None)
        self.assertEqual(result["output_tokens"], None)

    def test_zero_is_valid(self) -> None:
        usage = {
            "accuracy": "exact",
            "input_tokens": 0,
            "output_tokens": 0,
        }
        result = token_counts_from_provider_usage(usage, "normalized")
        self.assertEqual(result["input_tokens"], 0)
        self.assertEqual(result["output_tokens"], 0)

    def test_nested_usage_key_extraction_with_anthropic(self) -> None:
        usage = {
            "usage": {
                "input_tokens": 100,
                "cache_read_input_tokens": 25,
                "output_tokens": 50,
            },
            "other_field": "ignored",
        }
        result = token_counts_from_provider_usage(usage, "anthropic")
        self.assertEqual(result["input_tokens"], 125)
        self.assertEqual(result["cached_tokens"], 25)
        self.assertEqual(result["output_tokens"], 50)

    def test_nested_usage_key_extraction_with_openai_chat(self) -> None:
        usage = {
            "usage": {
                "prompt_tokens": 100,
                "prompt_tokens_details": {"cached_tokens": 30},
                "completion_tokens": 50,
            },
            "other_field": "ignored",
        }
        result = token_counts_from_provider_usage(usage, "openai-chat")
        self.assertEqual(result["input_tokens"], 100)
        self.assertEqual(result["cached_tokens"], 30)
        self.assertEqual(result["output_tokens"], 50)

    def test_all_formats_return_correct_keys(self) -> None:
        usage = {
            "input_tokens": 10,
            "output_tokens": 5,
        }
        for fmt in PROVIDER_USAGE_FORMATS:
            result = token_counts_from_provider_usage(usage, fmt)
            self.assertEqual(
                set(result.keys()),
                {"input_tokens", "cached_tokens", "reasoning_tokens", "output_tokens"},
            )

    def test_anthropic_no_cache_read_with_valid_input(self) -> None:
        usage = {
            "input_tokens": 100,
            "output_tokens": 50,
        }
        result = token_counts_from_provider_usage(usage, "anthropic")
        self.assertEqual(result["cached_tokens"], 0)


if __name__ == "__main__":
    unittest.main()
