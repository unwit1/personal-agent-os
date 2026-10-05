from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import cli
from agent_os.executive.window import registry
from agent_os.executive.window.confirm import ItemState, window_home


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = cli.main(["executive", *argv])
    return code, json.loads(out.getvalue())


class ExecutiveNextCli(unittest.TestCase):
    def test_next_returns_highest_score_item_with_rank(self):
        reg = registry.Registry()

        def provider():
            return [
                {"id": "item-work", "tab": "work", "title": "Work Item", "kind": "task", "score": 100},
                {"id": "item-personal", "tab": "personal", "title": "Personal Item", "kind": "task", "score": 50},
            ]

        reg.register_provider("test", provider)

        def mock_queue(tab):
            return reg.queue(tab, state=ItemState(window_home()))

        with patch.object(cli, "_executive_window_queue", side_effect=mock_queue):
            code, output = run("next")
            self.assertEqual(code, 0)
            self.assertIsNotNone(output["next"])
            self.assertEqual(output["next"]["window_item"]["id"], "item-work")
            self.assertEqual(output["why"]["rank"], 1)
            self.assertEqual(output["considered"], 2)

    def test_next_with_tab_filter_returns_only_tab_items(self):
        reg = registry.Registry()

        def provider():
            return [
                {"id": "item-work", "tab": "work", "title": "Work Item", "kind": "task", "score": 100},
                {"id": "item-personal", "tab": "personal", "title": "Personal Item", "kind": "task", "score": 50},
            ]

        reg.register_provider("test", provider)

        def mock_queue(tab):
            return reg.queue(tab, state=ItemState(window_home()))

        with patch.object(cli, "_executive_window_queue", side_effect=mock_queue):
            code, output = run("next", "--tab", "personal")
            self.assertEqual(code, 0)
            self.assertIsNotNone(output["next"])
            self.assertEqual(output["next"]["window_item"]["id"], "item-personal")
            self.assertEqual(output["considered"], 1)

    def test_explain_returns_matching_item_with_rank(self):
        reg = registry.Registry()

        def provider():
            return [
                {"id": "item-work", "tab": "work", "title": "Work Item", "kind": "task", "score": 100},
                {"id": "item-personal", "tab": "personal", "title": "Personal Item", "kind": "task", "score": 50},
            ]

        reg.register_provider("test", provider)

        def mock_queue(tab):
            return reg.queue(tab, state=ItemState(window_home()))

        with patch.object(cli, "_executive_window_queue", side_effect=mock_queue):
            code, output = run("explain", "item-personal")
            self.assertEqual(code, 0)
            self.assertEqual(output["explanation"]["item_id"], "item-personal")
            self.assertEqual(output["explanation"]["rank"], 2)
            self.assertEqual(output["explanation"]["of"], 2)
            self.assertEqual(output["explanation"]["provider"], "test")

    def test_explain_unknown_id_returns_null(self):
        reg = registry.Registry()

        def provider():
            return [
                {"id": "item-work", "tab": "work", "title": "Work Item", "kind": "task", "score": 100},
            ]

        reg.register_provider("test", provider)

        def mock_queue(tab):
            return reg.queue(tab, state=ItemState(window_home()))

        with patch.object(cli, "_executive_window_queue", side_effect=mock_queue):
            code, output = run("explain", "missing-id")
            self.assertEqual(code, 0)
            self.assertIsNone(output["explanation"])

    def test_provider_error_shows_in_errors(self):
        reg = registry.Registry()

        def failing_provider():
            raise RuntimeError("provider failure")

        reg.register_provider("failing", failing_provider)

        def mock_queue(tab):
            return reg.queue(tab, state=ItemState(window_home()))

        with patch.object(cli, "_executive_window_queue", side_effect=mock_queue):
            code, output = run("next")
            self.assertEqual(code, 0)
            self.assertEqual(len(output["errors"]), 1)
            self.assertEqual(output["errors"][0]["provider"], "failing")
            self.assertIn("RuntimeError", output["errors"][0]["error"])

    def test_explain_with_tab_filter(self):
        reg = registry.Registry()

        def provider():
            return [
                {"id": "item-work", "tab": "work", "title": "Work Item", "kind": "task", "score": 100},
                {"id": "item-personal", "tab": "personal", "title": "Personal Item", "kind": "task", "score": 50},
            ]

        reg.register_provider("test", provider)

        def mock_queue(tab):
            return reg.queue(tab, state=ItemState(window_home()))

        with patch.object(cli, "_executive_window_queue", side_effect=mock_queue):
            code, output = run("explain", "item-work", "--tab", "work")
            self.assertEqual(code, 0)
            self.assertEqual(output["explanation"]["item_id"], "item-work")
            self.assertEqual(output["explanation"]["rank"], 1)
            self.assertEqual(output["explanation"]["of"], 1)


if __name__ == "__main__":
    unittest.main()
