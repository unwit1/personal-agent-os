from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import cli


class ExecutiveWindowCli(unittest.TestCase):
    def test_window_parser_accepts_port_and_no_open(self):
        args = cli.parser().parse_args(["executive", "window", "--no-open", "--port", "0"])
        self.assertEqual(args.command, "executive")
        self.assertEqual(args.executive_command, "window")
        self.assertEqual(args.port, 0)
        self.assertTrue(args.no_open)

    def test_window_parser_defaults(self):
        args = cli.parser().parse_args(["executive", "window"])
        self.assertEqual(args.port, 8770)
        self.assertFalse(args.no_open)

    def test_dispatch_window_calls_serve_with_correct_args(self):
        with patch("agent_os.executive.window.server.serve", return_value=0) as mock_serve:
            args = cli.parser().parse_args(["executive", "window", "--no-open", "--port", "9999"])
            code = cli._dispatch_executive(args)
            mock_serve.assert_called_once_with(port=9999, open_window=False)
            self.assertEqual(code, 0)

    def test_dispatch_window_open_window_true_when_no_no_open(self):
        with patch("agent_os.executive.window.server.serve", return_value=0) as mock_serve:
            args = cli.parser().parse_args(["executive", "window", "--port", "7777"])
            code = cli._dispatch_executive(args)
            mock_serve.assert_called_once_with(port=7777, open_window=True)
            self.assertEqual(code, 0)

    def test_launcher_script_exists_and_contains_executive_window(self):
        launcher_path = Path(__file__).resolve().parents[1] / "tools" / "executive-window.cmd"
        self.assertTrue(launcher_path.exists(), f"Launcher script not found at {launcher_path}")
        content = launcher_path.read_text()
        self.assertIn("executive window", content)


if __name__ == "__main__":
    unittest.main()
