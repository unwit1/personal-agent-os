from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.cli import parser, main


class ConnectorCredentialStatusCliTests(unittest.TestCase):
    def test_parser_recognizes_connector_credential_status_command_with_surface(self) -> None:
        p = parser()
        args = p.parse_args(["connector-credential-status", "--surface", "codex-cli"])
        self.assertEqual(args.command, "connector-credential-status")
        self.assertEqual(args.surface, "codex-cli")

    def test_main_dispatches_connector_credential_status_and_outputs_result(self) -> None:
        mock_result = {
            "schema": "personal-agent/connector-credential-status/v1",
            "values_returned": False,
            "surface_filter": None,
            "count": 0,
            "status_counts": {},
            "items": [],
        }
        with patch("agent_os.cli.connector_credential_status", return_value=mock_result) as mock_fn:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(["connector-credential-status"])
            mock_fn.assert_called_once_with(None)
            self.assertIn("connector-credential-status/v1", output.getvalue())
