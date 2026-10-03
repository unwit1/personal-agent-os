from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.cli import parser, main


class ConnectorConflictsCliTests(unittest.TestCase):
    def test_parser_recognizes_connector_conflicts_command_with_surface(self) -> None:
        p = parser()
        args = p.parse_args(["connector-conflicts", "--surface", "claude-code"])
        self.assertEqual(args.command, "connector-conflicts")
        self.assertEqual(args.surface, "claude-code")

    def test_parser_recognizes_connector_conflicts_without_surface(self) -> None:
        p = parser()
        args = p.parse_args(["connector-conflicts"])
        self.assertEqual(args.command, "connector-conflicts")
        self.assertIsNone(args.surface)

    def test_main_dispatches_connector_conflicts_and_outputs_result(self) -> None:
        mock_result = {
            "schema": "personal-agent/connector-conflicts/v1",
            "surface_filter": None,
            "read_only": True,
            "count": 0,
            "kind_counts": {},
            "conflicts": [],
        }
        with patch("agent_os.cli.connector_conflicts", return_value=mock_result) as mock_fn:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(["connector-conflicts"])
            mock_fn.assert_called_once_with(None)
            self.assertIn("connector-conflicts/v1", output.getvalue())
