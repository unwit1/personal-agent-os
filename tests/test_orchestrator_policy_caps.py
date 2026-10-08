from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator.model import DEFAULT_POLICY, PolicyError, merge_policy


class PolicyCapTests(unittest.TestCase):
    def test_cap_defaults_and_valid_values(self) -> None:
        self.assertIsNone(DEFAULT_POLICY["max_usd"])
        self.assertIsNone(DEFAULT_POLICY["max_tokens"])
        self.assertEqual(DEFAULT_POLICY["max_same_provider_review_rounds"], 2)
        self.assertEqual(merge_policy({"max_usd": 5})["max_usd"], 5)
        self.assertEqual(merge_policy({"max_tokens": 1000})["max_tokens"], 1000)

    def test_invalid_money_caps(self) -> None:
        for value in (0, -1, "x", True):
            with self.subTest(value=value), self.assertRaisesRegex(PolicyError, "max_usd must be null or a positive number"):
                merge_policy({"max_usd": value})

    def test_invalid_token_caps(self) -> None:
        for value in (0, 1.5, True):
            with self.subTest(value=value), self.assertRaisesRegex(PolicyError, "max_tokens must be null or a positive integer"):
                merge_policy({"max_tokens": value})

    def test_negative_same_provider_round_cap_is_rejected(self) -> None:
        with self.assertRaisesRegex(PolicyError, "max_same_provider_review_rounds must be a non-negative integer"):
            merge_policy({"max_same_provider_review_rounds": -1})

    def test_old_policy_without_new_keys_remains_loadable(self) -> None:
        base = dict(DEFAULT_POLICY)
        for key in ("max_usd", "max_tokens", "max_same_provider_review_rounds"):
            del base[key]
        self.assertEqual(merge_policy({}, base=base), base)


if __name__ == "__main__":
    unittest.main()
