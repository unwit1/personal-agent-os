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


if __name__ == "__main__":
    unittest.main()
