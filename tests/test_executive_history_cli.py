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
from agent_os.executive import event_bus, window_queue


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = cli.main(["executive", *argv])
    return code, json.loads(out.getvalue())


class ExecutiveHistoryCli(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.bus = event_bus.EventBus(self.temp_dir.name)
        self.item = {"id": "item-1", "tab": "work", "title": "Item", "kind": "task"}
        self.queue_item = window_queue.queue_item_from_window_item(self.item, "test")
        window_queue.publish_window_item(self.bus, self.item, "test", self.queue_item)
        window_queue.publish_deferral(
            self.bus, self.queue_item["entity_id"], self.item["id"],
            deferred_at="2026-01-01T00:00:00+00:00", until="2026-01-02T00:00:00+00:00",
        )
        self.queue = {"queue_items": [self.queue_item], "errors": []}

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_history_includes_entity_and_event_types(self):
        with patch.object(cli, "_executive_window_queue", return_value=self.queue), patch.object(
            cli, "_executive_event_bus", return_value=self.bus
        ):
            code, output = run("history", "item-1", "--tab", "work")
        self.assertEqual(code, 0)
        self.assertEqual(output["provenance"]["entity_id"], self.queue_item["entity_id"])
        self.assertEqual([e["type"] for e in output["provenance"]["history"]], ["task.created", "task.deferred"])

    def test_history_unknown_item_returns_null_provenance(self):
        with patch.object(cli, "_executive_window_queue", return_value=self.queue), patch.object(
            cli, "_executive_event_bus", return_value=self.bus
        ):
            code, output = run("history", "missing-id")
        self.assertEqual(code, 0)
        self.assertIsNone(output["provenance"])


if __name__ == "__main__":
    unittest.main()
