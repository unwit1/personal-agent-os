"""Tests for estimate_cost function in http_api module."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator.adapters import http_api  # noqa: E402


class EstimateCostTests(unittest.TestCase):
    @patch("agent_os.orchestrator.model_value.load_evidence", return_value={"models": {"m": {"price": {"input": 3.0, "output": 15.0}}}})
    def test_estimate_cost_calculates_correctly(self, mock_load_evidence) -> None:
        cost = http_api.estimate_cost("m", 4000, 1000)
        self.assertEqual(cost, 0.018)

    @patch("agent_os.orchestrator.model_value.load_evidence", return_value={"models": {"m": {"price": {"input": 3.0, "output": 15.0}}}})
    def test_estimate_cost_unknown_model_returns_none(self, mock_load_evidence) -> None:
        cost = http_api.estimate_cost("unknown_model", 4000, 1000)
        self.assertIsNone(cost)

    @patch("agent_os.orchestrator.model_value.load_evidence", return_value={"models": {"m": {"price": {"input": 3.0, "output": 15.0}}}})
    def test_estimate_cost_prompt_chars_1_counts_as_1_token(self, mock_load_evidence) -> None:
        cost = http_api.estimate_cost("m", 1, 1)
        expected = round((1 * 3.0 + 1 * 15.0) / 1_000_000, 6)
        self.assertEqual(cost, expected)


if __name__ == "__main__":
    unittest.main()
