from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import cli


class ExecutiveRescueCli(unittest.TestCase):
    def test_rescue_parser_defaults_and_flags(self):
        defaults = cli.parser().parse_args(["executive", "rescue"])
        self.assertIsNone(defaults.tab)
        self.assertIsNone(defaults.today)
        self.assertIsNone(defaults.stale_days)
        self.assertEqual(defaults.horizon_days, 1)

        parsed = cli.parser().parse_args([
            "executive", "rescue", "--tab", "work", "--today", "2026-10-05",
            "--stale-days", "20", "--horizon-days", "3",
        ])
        self.assertEqual((parsed.tab, parsed.today, parsed.stale_days, parsed.horizon_days),
                         ("work", "2026-10-05", 20, 3))

    def test_resume_parser_defaults_and_flags(self):
        defaults = cli.parser().parse_args(["executive", "resume", "my-project"])
        self.assertEqual(defaults.project, "my-project")
        self.assertIsNone(defaults.today)
        self.assertIsNone(defaults.stale_days)
        parsed = cli.parser().parse_args([
            "executive", "resume", "my-project", "--today", "2026-10-05", "--stale-days", "12",
        ])
        self.assertEqual((parsed.today, parsed.stale_days), ("2026-10-05", 12))

    def test_rescue_dispatch_includes_project_action(self):
        project = {"id": "test-project", "state_file": "state.json"}
        state = {"project": "test-project", "status": "active", "next_action": "Write the plan",
                 "updated_at": "2026-10-05"}
        with patch("agent_os.cli._executive_window_queue", return_value={"queue_items": [], "errors": []}), \
             patch("agent_os.registry.canonical_projects", return_value=[project]), \
             patch("agent_os.registry.load_state", return_value=state), \
             patch("builtins.print") as printed:
            args = cli.parser().parse_args(["executive", "rescue", "--today", "2026-10-05"])
            self.assertEqual(cli._dispatch_executive(args), 0)
        output = json.loads(printed.call_args.args[0])
        self.assertEqual(output["mode"], "rescue")
        self.assertEqual(output["action"]["project"], "test-project")
        self.assertEqual(output["action"]["title"], "Write the plan")

    def test_rescue_dispatch_reports_project_load_error(self):
        project = {"id": "test-project", "state_file": "state.json"}
        with patch("agent_os.cli._executive_window_queue", return_value={"queue_items": [], "errors": []}), \
             patch("agent_os.registry.canonical_projects", return_value=[project]), \
             patch("agent_os.registry.load_state", side_effect=RuntimeError("boom")), \
             patch("builtins.print") as printed:
            args = cli.parser().parse_args(["executive", "rescue", "--today", "2026-10-05"])
            self.assertEqual(cli._dispatch_executive(args), 0)
        output = json.loads(printed.call_args.args[0])
        self.assertIn({"project": "test-project", "error": "boom"}, output["errors"])
        self.assertIsNone(output["action"])

    def test_resume_dispatch_prints_packet(self):
        project = {"id": "test-project", "state_file": "state.json"}
        state = {"project": "test-project", "status": "active", "next_action": "Write the plan",
                 "updated_at": "2026-10-05"}
        with patch("agent_os.registry.get_project", return_value=project), \
             patch("agent_os.registry.load_state", return_value=state), \
             patch("builtins.print") as printed:
            args = cli.parser().parse_args(["executive", "resume", "test-project", "--today", "2026-10-05"])
            self.assertEqual(cli._dispatch_executive(args), 0)
        self.assertEqual(json.loads(printed.call_args.args[0])["schema"], "agent-os/resumption-packet@1")

    def test_resume_unknown_project_raises_value_error(self):
        with patch("agent_os.registry.get_project", side_effect=KeyError("missing")):
            args = cli.parser().parse_args(["executive", "resume", "missing"])
            with self.assertRaisesRegex(ValueError, "unknown project: missing"):
                cli._dispatch_executive(args)


if __name__ == "__main__":
    unittest.main()
