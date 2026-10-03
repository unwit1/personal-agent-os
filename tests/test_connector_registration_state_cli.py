from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.cli import parser, main


class ConnectorSetRegistrationStateCliTests(unittest.TestCase):
    def test_parser_recognizes_connector_set_registration_state_with_all_args(self) -> None:
        p = parser()
        args = p.parse_args(["connector-set-registration-state", "demo", "agent-os-mcp", "disabled"])
        self.assertEqual(args.command, "connector-set-registration-state")
        self.assertEqual(args.connector_id, "demo")
        self.assertEqual(args.surface_id, "agent-os-mcp")
        self.assertEqual(args.state, "disabled")
        self.assertFalse(args.confirm_write)

    def test_parser_recognizes_connector_set_registration_state_with_confirm_flag(self) -> None:
        p = parser()
        args = p.parse_args(["connector-set-registration-state", "demo", "agent-os-mcp", "desired", "--confirm-write"])
        self.assertEqual(args.command, "connector-set-registration-state")
        self.assertEqual(args.connector_id, "demo")
        self.assertEqual(args.surface_id, "agent-os-mcp")
        self.assertEqual(args.state, "desired")
        self.assertTrue(args.confirm_write)

    def test_parser_rejects_invalid_state(self) -> None:
        p = parser()
        with self.assertRaises(SystemExit):
            p.parse_args(["connector-set-registration-state", "demo", "agent-os-mcp", "registered"])

    def test_main_dispatches_set_registration_state(self) -> None:
        with patch("agent_os.cli.set_registration_state") as mock_fn:
            mock_fn.return_value = {"schema": "personal-agent/connector-set-registration-state/v1"}
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(["connector-set-registration-state", "demo", "agent-os-mcp", "disabled"])
            mock_fn.assert_called_once_with("demo", "agent-os-mcp", "disabled", confirm_write=False)

    def test_main_dispatches_set_registration_state_with_confirm(self) -> None:
        with patch("agent_os.cli.set_registration_state") as mock_fn:
            mock_fn.return_value = {"schema": "personal-agent/connector-set-registration-state/v1"}
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(["connector-set-registration-state", "demo", "agent-os-mcp", "desired", "--confirm-write"])
            mock_fn.assert_called_once_with("demo", "agent-os-mcp", "desired", confirm_write=True)
