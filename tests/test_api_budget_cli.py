"""Tests for api-budget orchestrate CLI action."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import cli  # noqa: E402


class ApiBudgetCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def _call_cli(self, *args: str) -> tuple[int, dict]:
        """Call the orchestrate CLI and capture output."""
        import argparse
        parser = argparse.ArgumentParser()
        commands = parser.add_subparsers(dest="command", required=True)
        cli.register(commands)

        output_buffer = []
        def emit(data: dict) -> None:
            output_buffer.append(data)

        parsed = parser.parse_args(["orchestrate", *args])

        with mock.patch("agent_os.orchestrator.api_budget._home", return_value=self.home):
            exit_code = cli.dispatch(parsed, emit)

        return exit_code, output_buffer[0] if output_buffer else {}

    def test_api_budget_show_unset(self) -> None:
        exit_code, output = self._call_cli("api-budget", "show")
        self.assertEqual(exit_code, 0)
        self.assertFalse(output["approved"])
        self.assertIn("no API budget set", output.get("note", ""))

    def test_api_budget_set_then_show(self) -> None:
        exit_code, output = self._call_cli("api-budget", "set", "--total-usd", "100", "--call-cap-usd", "10")
        self.assertEqual(exit_code, 0)
        self.assertTrue(output["approved"])
        self.assertEqual(output["total_usd"], 100.0)
        self.assertEqual(output["call_cap_usd"], 10.0)
        self.assertEqual(output["spent_usd"], 0.0)
        self.assertEqual(output["remaining_usd"], 100.0)

        exit_code, output = self._call_cli("api-budget", "show")
        self.assertEqual(exit_code, 0)
        self.assertTrue(output["approved"])
        self.assertEqual(output["total_usd"], 100.0)
        self.assertEqual(output["call_cap_usd"], 10.0)
        self.assertEqual(output["spent_usd"], 0.0)
        self.assertEqual(output["remaining_usd"], 100.0)

    def test_api_budget_set_requires_both_args(self) -> None:
        exit_code, output = self._call_cli("api-budget", "set", "--total-usd", "100")
        self.assertEqual(exit_code, 2)
        self.assertIn("error", output)
        self.assertIn("set needs --total-usd and --call-cap-usd", output["error"])

        exit_code, output = self._call_cli("api-budget", "set", "--call-cap-usd", "10")
        self.assertEqual(exit_code, 2)
        self.assertIn("error", output)
        self.assertIn("set needs --total-usd and --call-cap-usd", output["error"])

    def test_api_budget_set_call_cap_greater_than_total(self) -> None:
        exit_code, output = self._call_cli("api-budget", "set", "--total-usd", "100", "--call-cap-usd", "200")
        self.assertEqual(exit_code, 2)
        self.assertIn("error", output)
        self.assertIn("per-call cap cannot exceed the total budget", output["error"])


if __name__ == "__main__":
    unittest.main()
