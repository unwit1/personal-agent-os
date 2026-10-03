from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.cli import parser, main


class ConnectorProvisioningReadinessCliTests(unittest.TestCase):
    def test_parser_recognizes_connector_provisioning_readiness_with_surface(self) -> None:
        p = parser()
        args = p.parse_args(["connector-provisioning-readiness", "--surface", "claude-code"])
        self.assertEqual(args.command, "connector-provisioning-readiness")
        self.assertEqual(args.surface, "claude-code")

    def test_parser_recognizes_connector_provisioning_readiness_without_surface(self) -> None:
        p = parser()
        args = p.parse_args(["connector-provisioning-readiness"])
        self.assertEqual(args.command, "connector-provisioning-readiness")
        self.assertIsNone(args.surface)

    def test_main_dispatches_connector_provisioning_readiness_and_outputs_result(self) -> None:
        mock_result = {
            "schema": "personal-agent/connector-provisioning-readiness/v1",
            "surface_filter": None,
            "read_only": True,
            "count": 0,
            "items": [],
        }
        with patch("agent_os.cli.connector_provisioning_readiness", return_value=mock_result) as mock_fn:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(["connector-provisioning-readiness"])
            mock_fn.assert_called_once_with(None)
            self.assertIn("connector-provisioning-readiness/v1", output.getvalue())
