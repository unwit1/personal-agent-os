from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.cli import parser, main


class ConnectorPruneStalCliTests(unittest.TestCase):
    def test_parser_recognizes_connector_prune_stale_with_no_id(self) -> None:
        p = parser()
        args = p.parse_args(["connector-prune-stale"])
        self.assertEqual(args.command, "connector-prune-stale")
        self.assertIsNone(args.connector_id)
        self.assertFalse(args.confirm_write)

    def test_parser_recognizes_connector_prune_stale_with_id_and_confirm_flag(self) -> None:
        p = parser()
        args = p.parse_args(["connector-prune-stale", "demo", "--confirm-write"])
        self.assertEqual(args.command, "connector-prune-stale")
        self.assertEqual(args.connector_id, "demo")
        self.assertTrue(args.confirm_write)

    def test_main_dispatches_prune_stale_registrations_with_no_id(self) -> None:
        with patch("agent_os.cli.prune_stale_registrations") as mock_fn:
            mock_fn.return_value = {"schema": "personal-agent/connector-prune-stale/v1"}
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(["connector-prune-stale"])
            mock_fn.assert_called_once_with(None, confirm_write=False)

    def test_main_dispatches_prune_stale_registrations_with_id_and_confirm(self) -> None:
        with patch("agent_os.cli.prune_stale_registrations") as mock_fn:
            mock_fn.return_value = {"schema": "personal-agent/connector-prune-stale/v1"}
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(["connector-prune-stale", "demo", "--confirm-write"])
            mock_fn.assert_called_once_with("demo", confirm_write=True)
