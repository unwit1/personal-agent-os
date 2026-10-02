from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.cli import parser, main


class ConnectorReconcileCliTests(unittest.TestCase):
    def test_parser_recognizes_connector_reconcile_plan_command_with_surface(self) -> None:
        p = parser()
        args = p.parse_args(["connector-reconcile-plan", "--surface", "codex-cli"])
        self.assertEqual(args.command, "connector-reconcile-plan")
        self.assertEqual(args.surface, "codex-cli")

    def test_main_dispatches_connector_reconcile_plan_and_outputs_result(self) -> None:
        mock_result = {
            "schema": "personal-agent/connector-reconcile-plan/v1",
            "applied": False,
            "count": 0,
            "items": [],
        }
        with patch("agent_os.cli.connector_reconcile_plan", return_value=mock_result) as mock_fn:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(["connector-reconcile-plan"])
            mock_fn.assert_called_once_with(None)
            self.assertIn("connector-reconcile-plan/v1", output.getvalue())
