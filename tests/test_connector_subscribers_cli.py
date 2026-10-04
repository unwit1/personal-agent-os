from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.cli import parser, main


class ConnectorSubscribersCliTests(unittest.TestCase):
    def test_parser_recognizes_connector_subscriber_poll_command_with_subscriber_id(self) -> None:
        p = parser()
        args = p.parse_args(["connector-subscriber-poll", "my-subscriber"])
        self.assertEqual(args.command, "connector-subscriber-poll")
        self.assertEqual(args.subscriber_id, "my-subscriber")
        self.assertEqual(args.limit, 50)

    def test_parser_recognizes_connector_subscriber_poll_with_limit(self) -> None:
        p = parser()
        args = p.parse_args(["connector-subscriber-poll", "my-subscriber", "--limit", "10"])
        self.assertEqual(args.subscriber_id, "my-subscriber")
        self.assertEqual(args.limit, 10)

    def test_parser_recognizes_connector_subscriber_ack_command(self) -> None:
        p = parser()
        args = p.parse_args(["connector-subscriber-ack", "my-subscriber", "--seq", "5"])
        self.assertEqual(args.command, "connector-subscriber-ack")
        self.assertEqual(args.subscriber_id, "my-subscriber")
        self.assertEqual(args.seq, 5)
        self.assertFalse(args.confirm_write)

    def test_parser_recognizes_connector_subscriber_ack_with_confirm_write(self) -> None:
        p = parser()
        args = p.parse_args(["connector-subscriber-ack", "my-subscriber", "--seq", "5", "--confirm-write"])
        self.assertEqual(args.command, "connector-subscriber-ack")
        self.assertEqual(args.subscriber_id, "my-subscriber")
        self.assertEqual(args.seq, 5)
        self.assertTrue(args.confirm_write)

    def test_parser_confirm_write_defaults_to_false(self) -> None:
        p = parser()
        args = p.parse_args(["connector-subscriber-ack", "my-subscriber", "--seq", "5"])
        self.assertFalse(args.confirm_write)

    def test_main_dispatches_connector_subscriber_poll_and_outputs_result(self) -> None:
        mock_result = {
            "schema": "personal-agent/connector-subscriber-poll/v1",
            "subscriber_id": "my-subscriber",
            "limit": 50,
            "events": [],
        }
        with patch("agent_os.cli.connector_subscriber_poll", return_value=mock_result) as mock_fn:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(["connector-subscriber-poll", "my-subscriber"])
            mock_fn.assert_called_once_with("my-subscriber", 50)
            self.assertIn("connector-subscriber-poll/v1", output.getvalue())

    def test_main_dispatches_connector_subscriber_poll_with_limit(self) -> None:
        mock_result = {
            "schema": "personal-agent/connector-subscriber-poll/v1",
            "subscriber_id": "my-subscriber",
            "limit": 10,
            "events": [],
        }
        with patch("agent_os.cli.connector_subscriber_poll", return_value=mock_result) as mock_fn:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(["connector-subscriber-poll", "my-subscriber", "--limit", "10"])
            mock_fn.assert_called_once_with("my-subscriber", 10)
            self.assertIn("connector-subscriber-poll/v1", output.getvalue())

    def test_main_dispatches_connector_subscriber_ack_and_outputs_result(self) -> None:
        mock_result = {
            "schema": "personal-agent/connector-subscriber-ack/v1",
            "subscriber_id": "my-subscriber",
            "seq": 5,
        }
        with patch("agent_os.cli.connector_subscriber_ack", return_value=mock_result) as mock_fn:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(["connector-subscriber-ack", "my-subscriber", "--seq", "5"])
            mock_fn.assert_called_once_with("my-subscriber", 5, confirm_write=False)
            self.assertIn("connector-subscriber-ack/v1", output.getvalue())

    def test_main_dispatches_connector_subscriber_ack_with_confirm_write(self) -> None:
        mock_result = {
            "schema": "personal-agent/connector-subscriber-ack/v1",
            "subscriber_id": "my-subscriber",
            "seq": 5,
        }
        with patch("agent_os.cli.connector_subscriber_ack", return_value=mock_result) as mock_fn:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(["connector-subscriber-ack", "my-subscriber", "--seq", "5", "--confirm-write"])
            mock_fn.assert_called_once_with("my-subscriber", 5, confirm_write=True)
            self.assertIn("connector-subscriber-ack/v1", output.getvalue())
