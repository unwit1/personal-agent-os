from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import cli


class ExecutiveCaptureCli(unittest.TestCase):
    def test_gap_answer_preview_does_not_stage(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            from agent_os.executive.window import actions_knowledge_gaps as mod
            from agent_os.executive.window.gap_store import GapStore

            store = GapStore(temp_dir)
            store.add([{"id": "g1", "question": "Q?", "project": "alpha"}])
            with patch.object(mod, "STORE_FACTORY", lambda: store), \
                 patch.object(mod, "PROJECT_EXISTS", lambda pid: pid == "alpha"), \
                 patch.object(mod, "STAGE", return_value={"created": [{"id": "c1"}], "duplicates": []}) as stage, \
                 patch("builtins.print") as printed:
                args = cli.parser().parse_args(["executive", "gap-answer", "g1", "--answer", "soon"])
                self.assertEqual(cli._dispatch_executive(args), 0)
            output = json.loads(printed.call_args.args[0])
            self.assertTrue(output["dry_run"])
            self.assertIn("candidate", output)
            stage.assert_not_called()

    def test_gap_answer_confirm_stages_and_marks_answered(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            from agent_os.executive.window import actions_knowledge_gaps as mod
            from agent_os.executive.window.gap_store import GapStore

            store = GapStore(temp_dir)
            store.add([{"id": "g1", "question": "Q?", "project": "alpha"}])
            with patch.object(mod, "STORE_FACTORY", lambda: store), \
                 patch.object(mod, "PROJECT_EXISTS", lambda pid: pid == "alpha"), \
                 patch.object(mod, "STAGE", return_value={"created": [{"id": "c1"}], "duplicates": []}) as stage, \
                 patch("builtins.print") as printed:
                args = cli.parser().parse_args(["executive", "gap-answer", "g1", "--answer", "soon", "--confirm"])
                self.assertEqual(cli._dispatch_executive(args), 0)
            output = json.loads(printed.call_args.args[0])
            self.assertFalse(output["dry_run"])
            self.assertIn("staging", output)
            stage.assert_called_once()
            self.assertEqual(store.get("g1")["status"], "answered")

    def test_gap_answer_unknown_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            from agent_os.executive.window import actions_knowledge_gaps as mod
            from agent_os.executive.window.gap_store import GapStore

            store = GapStore(temp_dir)
            with patch.object(mod, "STORE_FACTORY", lambda: store), \
                 patch.object(mod, "PROJECT_EXISTS", lambda pid: pid == "alpha"):
                args = cli.parser().parse_args(["executive", "gap-answer", "missing", "--answer", "soon"])
                with self.assertRaisesRegex(ValueError, "unknown knowledge gap"):
                    cli._dispatch_executive(args)

    def test_brain_dump_requires_text_or_file(self):
        args = cli.parser().parse_args(["executive", "brain-dump"])
        with self.assertRaisesRegex(ValueError, "provide text or --file"):
            cli._dispatch_executive(args)

    def test_brain_dump_processes_and_stages_records(self):
        with patch("agent_os.registry.canonical_projects", return_value=[{"id": "alpha", "aliases": []}]), \
             patch("agent_os.candidates.stage_candidates", return_value={"staged": []}) as stage, \
             patch("builtins.print") as printed:
            args = cli.parser().parse_args(["executive", "brain-dump", "Ship alpha", "--stage-candidates", "alpha"])
            self.assertEqual(cli._dispatch_executive(args), 0)
        output = json.loads(printed.call_args.args[0])
        self.assertEqual(output["records"][0]["project"], "alpha")
        stage.assert_called_once()

    def test_gaps_dispatch_selects_questions(self):
        args = cli.parser().parse_args(["executive", "gaps", '[{"id":"g1","question":"Q?","utility":1}]'])
        with patch("builtins.print") as printed:
            self.assertEqual(cli._dispatch_executive(args), 0)
        output = json.loads(printed.call_args.args[0])
        self.assertEqual(output["ask"][0]["id"], "g1")
        self.assertNotIn("enqueued", output)

    def test_gaps_enqueue_stores_open_question(self):
        from agent_os.executive.window.gap_store import GapStore

        with tempfile.TemporaryDirectory() as temp_dir:
            store = GapStore(temp_dir)
            args = cli.parser().parse_args([
                "executive", "gaps", '[{"id":"g1","question":"Q?","utility":1}]', "--enqueue",
            ])
            with patch("agent_os.executive.window.gap_store.GapStore", side_effect=lambda: store), \
                 patch("builtins.print") as printed:
                self.assertEqual(cli._dispatch_executive(args), 0)
            output = json.loads(printed.call_args.args[0])
            self.assertEqual(output["enqueued"], ["g1"])
            self.assertEqual(store.get("g1")["status"], "open")

    def test_project_gaps_dispatch_selects_questions(self):
        with patch("agent_os.registry.canonical_projects", return_value=[{"id": "alpha", "state_file": "x"}]), \
             patch("agent_os.registry.load_state", return_value={"project": "alpha", "status": "active"}), \
             patch("builtins.print") as printed:
            args = cli.parser().parse_args(["executive", "project-gaps"])
            self.assertEqual(cli._dispatch_executive(args), 0)
        output = json.loads(printed.call_args.args[0])
        self.assertEqual([gap["id"] for gap in output["gaps"]], [
            "project-gap:alpha:goal", "project-gap:alpha:next_action", "project-gap:alpha:blockers",
        ])
        self.assertIn("ask", output)
        self.assertEqual(output["errors"], [])
        self.assertNotIn("enqueued", output)

    def test_project_gaps_enqueue_is_idempotent(self):
        from agent_os.executive.window.gap_store import GapStore

        with tempfile.TemporaryDirectory() as temp_dir:
            store = GapStore(temp_dir)
            with patch("agent_os.registry.canonical_projects", return_value=[{"id": "alpha", "state_file": "x"}]), \
                 patch("agent_os.registry.load_state", return_value={"project": "alpha", "status": "active"}), \
                 patch("agent_os.executive.window.gap_store.GapStore", side_effect=lambda: store), \
                 patch("builtins.print") as printed:
                args = cli.parser().parse_args(["executive", "project-gaps", "--enqueue"])
                self.assertEqual(cli._dispatch_executive(args), 0)
                first = json.loads(printed.call_args.args[0])
                self.assertEqual(cli._dispatch_executive(args), 0)
                second = json.loads(printed.call_args.args[0])
            ids = ["project-gap:alpha:goal", "project-gap:alpha:next_action", "project-gap:alpha:blockers"]
            self.assertEqual(first["enqueued"], ids)
            self.assertEqual(store.get("project-gap:alpha:goal")["status"], "open")
            self.assertEqual(second["enqueued"], [])

    def test_project_gaps_reports_load_errors(self):
        with patch("agent_os.registry.canonical_projects", return_value=[{"id": "alpha", "state_file": "x"}]), \
             patch("agent_os.registry.load_state", side_effect=ValueError("bad state")), \
             patch("builtins.print") as printed:
            args = cli.parser().parse_args(["executive", "project-gaps"])
            self.assertEqual(cli._dispatch_executive(args), 0)
        output = json.loads(printed.call_args.args[0])
        self.assertEqual(output["errors"], [{"project": "alpha", "error": "bad state"}])


if __name__ == "__main__":
    unittest.main()
