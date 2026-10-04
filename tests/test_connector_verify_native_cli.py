from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.cli import parser, main


class ConnectorVerifyNativeCliTests(unittest.TestCase):
    def test_parser_recognizes_connector_verify_native_command_with_connector_id(self) -> None:
        p = parser()
        args = p.parse_args(["connector-verify-native", "my-connector"])
        self.assertEqual(args.command, "connector-verify-native")
        self.assertEqual(args.connector_id, "my-connector")

    def test_parser_recognizes_connector_verify_native_without_connector_id(self) -> None:
        p = parser()
        args = p.parse_args(["connector-verify-native"])
        self.assertEqual(args.command, "connector-verify-native")
        self.assertIsNone(args.connector_id)

    def test_parser_confirm_write_defaults_false(self) -> None:
        p = parser()
        args = p.parse_args(["connector-verify-native"])
        self.assertFalse(args.confirm_write)

    def test_parser_confirm_write_sets_true(self) -> None:
        p = parser()
        args = p.parse_args(["connector-verify-native", "--confirm-write"])
        self.assertTrue(args.confirm_write)

    def test_main_dispatches_connector_verify_native_and_outputs_result(self) -> None:
        mock_result = {
            "schema": "personal-agent/connector-verify-native/v1",
            "connector_filter": None,
            "read_only": True,
            "count": 0,
            "verified": [],
        }
        with patch("agent_os.cli.verify_native_registrations", return_value=mock_result) as mock_fn:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main(["connector-verify-native"])
            mock_fn.assert_called_once_with(None, confirm_write=False)
            self.assertEqual(exit_code, 0)
            self.assertIn("connector-verify-native/v1", output.getvalue())
