from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.cli import parser, main


class ConnectorEventsCliTests(unittest.TestCase):
    def test_parser_recognizes_connector_events_command_with_limit_and_connector(self) -> None:
        p = parser()
        args = p.parse_args(["connector-events", "--limit", "5", "--connector", "demo"])
        self.assertEqual(args.command, "connector-events")
        self.assertEqual(args.limit, 5)
        self.assertEqual(args.connector_id, "demo")

    def test_parser_recognizes_connector_events_with_after_seq(self) -> None:
        p = parser()
        args = p.parse_args(["connector-events", "--after-seq", "7"])
        self.assertEqual(args.after_seq, 7)

    def test_parser_after_seq_defaults_to_none(self) -> None:
        p = parser()
        args = p.parse_args(["connector-events"])
        self.assertIsNone(args.after_seq)

    def test_parser_recognizes_connector_unregister_command(self) -> None:
        p = parser()
        args = p.parse_args(["connector-unregister", "demo"])
        self.assertEqual(args.command, "connector-unregister")
        self.assertEqual(args.connector_id, "demo")
        self.assertFalse(args.confirm_write)

    def test_parser_recognizes_connector_unregister_with_confirm_flag(self) -> None:
        p = parser()
        args = p.parse_args(["connector-unregister", "demo", "--confirm-write"])
        self.assertEqual(args.command, "connector-unregister")
        self.assertEqual(args.connector_id, "demo")
        self.assertTrue(args.confirm_write)

    def test_main_dispatches_connector_events_and_outputs_result(self) -> None:
        mock_result = {
            "schema": "personal-agent/connector-events/v1",
            "limit": 50,
            "connector_id": None,
            "events": [],
        }
        with patch("agent_os.cli.connector_events", return_value=mock_result) as mock_fn:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(["connector-events"])
            mock_fn.assert_called_once_with(50, None, None)
            self.assertIn("connector-events/v1", output.getvalue())

    def test_main_dispatches_connector_events_with_after_seq(self) -> None:
        mock_result = {
            "schema": "personal-agent/connector-events/v1",
            "limit": 50,
            "connector_id": None,
            "events": [],
        }
        with patch("agent_os.cli.connector_events", return_value=mock_result) as mock_fn:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(["connector-events", "--after-seq", "3"])
            mock_fn.assert_called_once_with(50, None, 3)
            self.assertIn("connector-events/v1", output.getvalue())

    def test_main_dispatches_connector_unregister_with_confirm_flag(self) -> None:
        with patch("agent_os.cli.unregister_connector") as mock_fn:
            mock_fn.return_value = {"schema": "personal-agent/connector-unregister/v1"}
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(["connector-unregister", "demo", "--confirm-write"])
            mock_fn.assert_called_once_with("demo", confirm_write=True)
