from __future__ import annotations

import sys
import unittest
from datetime import date
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import cli


class ExecutiveProjectActionsCli(unittest.TestCase):
    def test_project_next_parser_accepts_project_and_flags(self):
        args = cli.parser().parse_args(["executive", "project-next", "myproject", "--stale-days", "45", "--today", "2026-10-05"])
        self.assertEqual(args.command, "executive")
        self.assertEqual(args.executive_command, "project-next")
        self.assertEqual(args.project, "myproject")
        self.assertEqual(args.stale_days, 45)
        self.assertEqual(args.today, "2026-10-05")

    def test_project_next_parser_defaults(self):
        args = cli.parser().parse_args(["executive", "project-next", "myproject"])
        self.assertEqual(args.stale_days, None)
        self.assertEqual(args.today, None)

    def test_project_next_dispatch_calls_project_next_action(self):
        mock_project = {"id": "test-project", "state_file": "state.json"}
        mock_state = {
            "project": "test-project",
            "status": "active",
            "goal": "Build something",
            "next_action": "Write code",
            "blockers": [],
            "waiting_on": [],
            "decisions_needed": [],
            "delegable_work": [],
            "updated_at": "2026-10-01",
        }

        with patch("agent_os.registry.get_project", return_value=mock_project) as mock_get_project, \
             patch("agent_os.registry.load_state", return_value=mock_state) as mock_load_state:

            args = cli.parser().parse_args(["executive", "project-next", "test-project", "--today", "2026-10-05", "--stale-days", "30"])
            with patch("builtins.print") as mock_print:
                code = cli._dispatch_executive(args)

                mock_get_project.assert_called_once_with("test-project")
                mock_load_state.assert_called_once_with(mock_project)
                self.assertEqual(code, 0)

                # Verify print was called with JSON containing the expected keys
                call_args = mock_print.call_args[0][0]
                self.assertIsInstance(call_args, str)
                import json
                output = json.loads(call_args)
                self.assertIn("project", output)
                self.assertIn("next_action", output)
                self.assertIn("flags", output)

    def test_project_next_unknown_project_raises_error(self):
        with patch("agent_os.registry.get_project", side_effect=KeyError("Unknown project")) as mock_get_project:
            args = cli.parser().parse_args(["executive", "project-next", "unknown-project"])

            with self.assertRaises(ValueError) as context:
                cli._dispatch_executive(args)

            self.assertIn("unknown project", str(context.exception))

    def test_project_next_with_fixed_today(self):
        mock_project = {"id": "test-project", "state_file": "state.json"}
        mock_state = {
            "project": "test-project",
            "status": "active",
            "goal": "Build",
            "next_action": "Code",
            "updated_at": "2026-09-01",
        }

        with patch("agent_os.registry.get_project", return_value=mock_project), \
             patch("agent_os.registry.load_state", return_value=mock_state), \
             patch("agent_os.executive.project_actions.project_next_action", wraps=lambda state, **kw: {
                 "project": "test-project", "age_days": 34, "next_action": "Code", "flags": ["stalled"]
             }) as mock_pna:

            args = cli.parser().parse_args(["executive", "project-next", "test-project", "--today", "2026-10-05"])
            with patch("builtins.print"):
                cli._dispatch_executive(args)

            # Verify that today was passed as a date object
            mock_pna.assert_called_once()
            call_kwargs = mock_pna.call_args[1]
            self.assertEqual(call_kwargs["today"], date(2026, 10, 5))

    def test_project_scan_parser_accepts_flags(self):
        args = cli.parser().parse_args(["executive", "project-scan", "--stale-days", "60", "--today", "2026-10-05", "--all"])
        self.assertEqual(args.command, "executive")
        self.assertEqual(args.executive_command, "project-scan")
        self.assertEqual(args.stale_days, 60)
        self.assertEqual(args.today, "2026-10-05")
        self.assertTrue(args.all)

    def test_project_scan_parser_defaults(self):
        args = cli.parser().parse_args(["executive", "project-scan"])
        self.assertEqual(args.stale_days, None)
        self.assertEqual(args.today, None)
        self.assertFalse(args.all)

    def test_project_scan_dispatch_loads_all_states_and_scans(self):
        mock_projects = [
            {"id": "proj1", "state_file": "state1.json"},
            {"id": "proj2", "state_file": "state2.json"},
        ]
        mock_states = [
            {"project": "proj1", "status": "active", "next_action": "Do something", "updated_at": "2026-10-05"},
            {"project": "proj2", "status": "active", "next_action": "Do other", "updated_at": "2026-10-05"},
        ]

        with patch("agent_os.registry.canonical_projects", return_value=mock_projects), \
             patch("agent_os.registry.load_state", side_effect=mock_states):

            args = cli.parser().parse_args(["executive", "project-scan", "--today", "2026-10-05"])
            with patch("builtins.print") as mock_print:
                code = cli._dispatch_executive(args)

                self.assertEqual(code, 0)

                # Verify print was called with JSON including errors and projects
                call_args = mock_print.call_args[0][0]
                import json
                output = json.loads(call_args)
                self.assertIn("errors", output)
                self.assertIn("projects", output)
                self.assertEqual(len(output["projects"]), 2)

    def test_project_scan_skips_entries_without_state_file(self):
        mock_projects = [
            {"id": "proj1", "state_file": "state1.json"},
            {"id": "proj2"},  # No state_file
        ]
        mock_state = {"project": "proj1", "status": "active", "next_action": "Work"}

        with patch("agent_os.registry.canonical_projects", return_value=mock_projects), \
             patch("agent_os.registry.load_state", return_value=mock_state) as mock_load:

            args = cli.parser().parse_args(["executive", "project-scan"])
            with patch("builtins.print"):
                cli._dispatch_executive(args)

            # load_state should only be called once (for proj1)
            self.assertEqual(mock_load.call_count, 1)

    def test_project_scan_records_load_errors(self):
        mock_projects = [
            {"id": "proj1", "state_file": "state1.json"},
            {"id": "proj2", "state_file": "state2.json"},
        ]
        mock_state_good = {"project": "proj1", "status": "active", "next_action": "Code"}

        def side_effect(proj):
            if proj["id"] == "proj1":
                return mock_state_good
            raise IOError("File not found")

        with patch("agent_os.registry.canonical_projects", return_value=mock_projects), \
             patch("agent_os.registry.load_state", side_effect=side_effect):

            args = cli.parser().parse_args(["executive", "project-scan"])
            with patch("builtins.print") as mock_print:
                code = cli._dispatch_executive(args)

                self.assertEqual(code, 0)
                call_args = mock_print.call_args[0][0]
                import json
                output = json.loads(call_args)

                # Should have one error for proj2
                self.assertEqual(len(output["errors"]), 1)
                self.assertEqual(output["errors"][0]["project"], "proj2")
                self.assertIn("File not found", output["errors"][0]["error"])

    def test_project_scan_with_all_flag_includes_inactive(self):
        mock_projects = [
            {"id": "proj1", "state_file": "state1.json"},
        ]
        mock_state = {"project": "proj1", "status": "inactive", "next_action": "Work"}

        with patch("agent_os.registry.canonical_projects", return_value=mock_projects), \
             patch("agent_os.registry.load_state", return_value=mock_state):

            args = cli.parser().parse_args(["executive", "project-scan", "--all"])
            with patch("builtins.print") as mock_print:
                cli._dispatch_executive(args)

                call_args = mock_print.call_args[0][0]
                import json
                output = json.loads(call_args)
                # With --all, inactive projects should be included
                self.assertEqual(len(output["projects"]), 1)
                self.assertEqual(output["projects"][0]["project"], "proj1")

    def test_project_scan_without_all_flag_excludes_inactive(self):
        mock_projects = [
            {"id": "proj1", "state_file": "state1.json"},
            {"id": "proj2", "state_file": "state2.json"},
        ]
        mock_states = [
            {"project": "proj1", "status": "active", "next_action": "Work"},
            {"project": "proj2", "status": "inactive", "next_action": "Work"},
        ]

        with patch("agent_os.registry.canonical_projects", return_value=mock_projects), \
             patch("agent_os.registry.load_state", side_effect=mock_states):

            args = cli.parser().parse_args(["executive", "project-scan"])
            with patch("builtins.print") as mock_print:
                cli._dispatch_executive(args)

                call_args = mock_print.call_args[0][0]
                import json
                output = json.loads(call_args)
                # Without --all, only active projects should be included
                self.assertEqual(len(output["projects"]), 1)
                self.assertEqual(output["projects"][0]["project"], "proj1")

    def test_project_scan_output_contains_stalled_and_no_next_action_lists(self):
        mock_projects = [
            {"id": "proj1", "state_file": "state1.json"},
            {"id": "proj2", "state_file": "state2.json"},
        ]
        # proj1: stalled (updated_at > 30 days ago), proj2: no_next_action (no next_action)
        mock_states = [
            {"project": "proj1", "status": "active", "next_action": "Work", "updated_at": "2026-09-01"},
            {"project": "proj2", "status": "active", "updated_at": "2026-10-05"},
        ]

        with patch("agent_os.registry.canonical_projects", return_value=mock_projects), \
             patch("agent_os.registry.load_state", side_effect=mock_states):

            args = cli.parser().parse_args(["executive", "project-scan", "--today", "2026-10-05"])
            with patch("builtins.print") as mock_print:
                cli._dispatch_executive(args)

                call_args = mock_print.call_args[0][0]
                import json
                output = json.loads(call_args)

                self.assertEqual(output["stalled"], ["proj1"])
                self.assertEqual(output["no_next_action"], ["proj2"])
                self.assertIn("errors", output)

    def test_project_scan_output_contains_vague_next_action_list(self):
        mock_projects = [
            {"id": "proj1", "state_file": "state1.json"},
            {"id": "proj2", "state_file": "state2.json"},
            {"id": "proj3", "state_file": "state3.json"},
        ]
        # proj1: vague_next_action (TBD), proj2: specific action, proj3: no next_action
        mock_states = [
            {"project": "proj1", "status": "active", "next_action": "TBD", "updated_at": "2026-10-05"},
            {"project": "proj2", "status": "active", "next_action": "Write tests", "updated_at": "2026-10-05"},
            {"project": "proj3", "status": "active", "updated_at": "2026-10-05"},
        ]

        with patch("agent_os.registry.canonical_projects", return_value=mock_projects), \
             patch("agent_os.registry.load_state", side_effect=mock_states):

            args = cli.parser().parse_args(["executive", "project-scan", "--today", "2026-10-05"])
            with patch("builtins.print") as mock_print:
                cli._dispatch_executive(args)

                call_args = mock_print.call_args[0][0]
                import json
                output = json.loads(call_args)

                self.assertEqual(output["vague_next_action"], ["proj1"])
                self.assertIn("errors", output)


if __name__ == "__main__":
    unittest.main()
