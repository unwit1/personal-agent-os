from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import cli
from agent_os.executive import event_bus, window_queue
from agent_os.executive.window import registry
from agent_os.executive.window.confirm import ENV_HOME, ItemState


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = cli.main(["executive", *argv])
    return code, json.loads(out.getvalue())


WORK = {"id": "item-work", "tab": "work", "title": "Work Item", "kind": "task", "score": 100}
PERSONAL = {"id": "item-personal", "tab": "personal", "title": "Personal Item", "kind": "task", "score": 50}


class ExecutiveNextCli(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.bus = event_bus.EventBus(self.temp_dir.name)
        self.bus_patch = patch.object(cli, "_executive_event_bus", return_value=self.bus)
        self.bus_patch.start()
        self.addCleanup(self.bus_patch.stop)

    def run_with(self, provider, *argv, name="test"):
        reg = registry.Registry()
        reg.register_provider(name, provider)
        with patch.object(cli, "_executive_window_queue", side_effect=lambda tab: reg.queue(tab)):
            return run(*argv)

    def test_next_returns_highest_score_item_with_rank(self):
        code, output = self.run_with(lambda: [WORK, PERSONAL], "next")
        self.assertEqual(code, 0)
        self.assertEqual(output["next"]["window_item"]["id"], "item-work")
        self.assertEqual(output["why"]["item_id"], "item-work")
        self.assertEqual(output["why"]["queue_item_id"], output["next"]["id"])
        self.assertEqual(output["why"]["rank"], 1)
        self.assertEqual(output["considered"], 2)
        self.assertIsInstance(output["why"]["provenance"]["event_ids"], list)

    def test_next_with_tab_filter_returns_only_tab_items(self):
        code, output = self.run_with(lambda: [WORK, PERSONAL], "next", "--tab", "personal")
        self.assertEqual(code, 0)
        self.assertEqual(output["next"]["window_item"]["id"], "item-personal")
        self.assertEqual(output["considered"], 1)

    def test_explain_returns_matching_item_with_rank(self):
        code, output = self.run_with(lambda: [WORK, PERSONAL], "explain", "item-personal")
        self.assertEqual(code, 0)
        self.assertEqual(output["explanation"]["item_id"], "item-personal")
        self.assertEqual(output["explanation"]["rank"], 2)
        self.assertEqual(output["explanation"]["of"], 2)
        self.assertEqual(output["explanation"]["provider"], "test")

    def test_explain_unknown_id_returns_null(self):
        code, output = self.run_with(lambda: [WORK], "explain", "missing-id")
        self.assertEqual(code, 0)
        self.assertIsNone(output["explanation"])

    def test_provider_error_shows_in_errors(self):
        def failing_provider():
            raise RuntimeError("provider failure")

        code, output = self.run_with(failing_provider, "next", name="failing")
        self.assertEqual(code, 0)
        self.assertEqual(len(output["errors"]), 1)
        self.assertEqual(output["errors"][0]["provider"], "failing")
        self.assertIn("RuntimeError", output["errors"][0]["error"])

    def test_explain_with_tab_filter(self):
        code, output = self.run_with(lambda: [WORK, PERSONAL], "explain", "item-work", "--tab", "work")
        self.assertEqual(code, 0)
        self.assertEqual(output["explanation"]["item_id"], "item-work")
        self.assertEqual(output["explanation"]["rank"], 1)
        self.assertEqual(output["explanation"]["of"], 1)

    def test_explain_includes_created_event_provenance(self):
        reg = registry.Registry()
        reg.register_provider("test", lambda: [WORK])
        queue_item = reg.queue()["queue_items"][0]
        event, _ = window_queue.publish_window_item(self.bus, WORK, "test", queue_item)

        with patch.object(cli, "_executive_window_queue", return_value=reg.queue()):
            code, output = run("explain", "item-work")

        self.assertEqual(code, 0)
        provenance = output["explanation"]["provenance"]
        self.assertEqual(provenance["created_event_id"], event["id"])
        self.assertEqual(provenance["provider"], "test")

    def test_real_queue_helper_uses_window_home_state(self):
        reg = registry.Registry()
        reg.register_provider("test", lambda: [WORK, PERSONAL])
        ItemState(self.temp_dir.name).dismiss("item-work")
        with patch.dict(os.environ, {ENV_HOME: self.temp_dir.name}),                 patch("agent_os.executive.window.builtin.default_registry", return_value=reg):
            queue = cli._executive_window_queue(None)
        self.assertEqual([qi["window_item"]["id"] for qi in queue["queue_items"]], ["item-personal"])


if __name__ == "__main__":
    unittest.main()
