from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import watcher
from agent_os.executive.event_bus import EventBus


class FakeDashboard:
    def __init__(self, events, fail_ack=()):
        self.pending = list(events)
        self.acked = []
        self.fail_ack = set(fail_ack)

    def pending_events(self, limit=100):
        return {"count": len(self.pending), "results": list(self.pending)}

    def acknowledge_event(self, event_id):
        if event_id in self.fail_ack:
            raise RuntimeError("ack failed")
        self.acked.append(event_id)
        self.pending = [e for e in self.pending if e["event_id"] != event_id]
        return {"acknowledged": True, "event_id": event_id}


def raw(event_id, event_type="reply_received"):
    return {"event_id": event_id, "applicant_ref": "ref-" + event_id, "event_type": event_type,
            "source_component": "dash", "created_at": "2026-10-16T10:00:00+00:00", "payload": {}, "sensitivity": "sensitive"}


class WatcherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.bus = EventBus(base / "events")
        self.home = base / "home"
        self.kb = base / "kb"
        self.kb.mkdir()
        (self.kb / "policy.md").write_text("a", encoding="utf-8")

    def sweep(self, dash, **kw):
        return watcher.sweep_once(self.bus, pending_events=dash.pending_events,
                                  acknowledge_event=dash.acknowledge_event,
                                  knowledge_root=self.kb, home=self.home, **kw)

    def test_published_and_acked_exactly_once(self):
        dash = FakeDashboard([raw("e1"), raw("e2", "status_changed")])
        state = self.sweep(dash)
        again = self.sweep(dash)
        self.assertEqual(dash.acked, ["e1", "e2"])
        self.assertEqual(len(self.bus.events()), 2)
        self.assertEqual(state["counts"]["applicant_events_published"], 2)
        self.assertEqual(state["counts"]["routed"], 2)
        self.assertEqual(again["counts"]["applicant_events_seen"], 0)
        self.assertEqual(state["errors"], [])

    def test_ack_not_called_when_publish_fails(self):
        dash = FakeDashboard([{**raw("e1"), "event_id": ""}, raw("e2")])
        state = self.sweep(dash)
        self.assertEqual(dash.acked, ["e2"])
        self.assertEqual(len(state["errors"]), 1)

        class BrokenBus(EventBus):
            def publish(self, *a, **k):
                raise OSError("disk full")

        dash2 = FakeDashboard([raw("e3")])
        broken = BrokenBus(Path(self.tmp.name) / "broken")
        watcher.sweep_once(broken, pending_events=dash2.pending_events, acknowledge_event=dash2.acknowledge_event,
                           knowledge_root=self.kb, home=self.home)
        self.assertEqual(dash2.acked, [])

    def test_ack_failure_is_recorded_and_retry_does_not_duplicate(self):
        dash = FakeDashboard([raw("e1")], fail_ack={"e1"})
        state = self.sweep(dash)
        self.assertTrue(state["errors"])
        dash.fail_ack.clear()
        self.sweep(dash)
        self.assertEqual(dash.acked, ["e1"])
        self.assertEqual(len(self.bus.events()), 1)

    def test_missing_sources_tolerated(self):
        def missing(limit=100):
            raise FileNotFoundError("no database")

        state = watcher.sweep_once(self.bus, pending_events=missing, acknowledge_event=lambda i: {},
                                   knowledge_root=Path(self.tmp.name) / "nope", home=self.home)
        self.assertTrue(state["sources"]["applicants"].startswith("unavailable"))
        self.assertEqual(state["sources"]["knowledge"], "unavailable")
        self.assertEqual(state["errors"], [])

    def test_state_written(self):
        self.sweep(FakeDashboard([raw("e1")]))
        state = watcher.load_state(self.home)
        self.assertIn("last_sweep", state)
        self.assertEqual(state["counts"]["applicant_events_acked"], 1)
        self.assertTrue((self.home / "watcher-state.json").is_file())

    def test_knowledge_change_records_event_only_after_baseline(self):
        dash = FakeDashboard([])
        self.sweep(dash)
        self.assertEqual(self.bus.events(), [])
        f = self.kb / "policy.md"
        f.write_text("b", encoding="utf-8")
        os.utime(f, ns=(1, f.stat().st_mtime_ns + 5_000_000_000))
        state = self.sweep(dash)
        events = self.bus.events()
        self.assertEqual(state["counts"]["knowledge_refresh_events"], 1)
        self.assertEqual(events[0]["payload"]["kind"], "knowledge_refresh_needed")
        self.sweep(dash)
        self.assertEqual(len(self.bus.events()), 1)

    def test_watcher_items_only_with_errors_or_new_events(self):
        self.sweep(FakeDashboard([]))
        self.assertEqual(watcher.watcher_items(self.home), [])
        self.sweep(FakeDashboard([raw("e9")]))
        items = watcher.watcher_items(self.home)
        self.assertEqual(items[0]["id"], "watcher_status")


if __name__ == "__main__":
    unittest.main()
