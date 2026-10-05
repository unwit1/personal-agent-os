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
from agent_os.executive.event_bus import EventBus


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = cli.main(["executive", *argv])
    return code, json.loads(out.getvalue())


class ExecutiveRouteCli(unittest.TestCase):
    def test_route_dispatch_is_idempotent_and_reasons_are_queryable(self):
        with tempfile.TemporaryDirectory() as tmp:
            bus = EventBus(tmp)
            events = [
                bus.publish("task.created", "test", "one", {"title": "one"})[0],
                bus.publish("task.completed", "test", "two", {"title": "two"})[0],
            ]
            with patch.object(cli, "_executive_event_bus", return_value=bus):
                code, output = run("route")
                self.assertEqual(code, 0)
                self.assertEqual(len(output["dispatched"]), len(events))
                self.assertEqual(output["consumer"], "router")
                code, repeated = run("route")
                self.assertEqual(code, 0)
                self.assertEqual(repeated["dispatched"], [])
                code, reason = run("route-reason", events[0]["id"])
                self.assertEqual(code, 0)
                self.assertEqual(reason["route"], output["dispatched"][0])
                code, unknown = run("route-reason", "missing-event")
                self.assertEqual(code, 0)
                self.assertIsNone(unknown["route"])

    def test_route_rules_override_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            bus = EventBus(tmp)
            bus.publish("task.created", "test", "one", {"title": "one"})
            with patch.object(cli, "_executive_event_bus", return_value=bus):
                code, output = run("route", "--rules", '{"task.created": "ignore"}')
            self.assertEqual(code, 0)
            self.assertEqual(output["dispatched"][0]["disposition"], "ignore")
            self.assertEqual(output["dispatched"][0]["rule"], "override")

    def test_route_rules_must_be_object(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            cli, "_executive_event_bus", return_value=EventBus(tmp)
        ):
            code, output = run("route", "--rules", "[]")
        self.assertEqual(code, 2)
        self.assertEqual(output["error"], "--rules must be a JSON object")


if __name__ == "__main__":
    unittest.main()
