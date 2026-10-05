import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import tempfile
import unittest

from agent_os.executive.event_bus import EventBus
from agent_os.executive.window.confirm import ItemState
from agent_os.executive.window.registry import Registry
from agent_os.executive import contracts


def item(i, tab="work", kind="note", why=None, score=None):
    d = {"id": i, "tab": tab, "kind": kind, "title": i, "source": "test"}
    if why is not None:
        d["why"] = why
    if score is not None:
        d["score"] = score
    return d


class RegistryQueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = ItemState(self.tmp.name)

    def test_outstanding_without_bus_unchanged(self):
        """outstanding() with no bus attached returns same format as before."""
        reg = Registry()
        reg.register_provider("p1", lambda: [item("a", why="test why", score=10)])
        reg.register_action("act1", "Action 1", "*", lambda i, p, *, confirm: {}, False)

        out = reg.outstanding()
        self.assertEqual(len(out["items"]), 1)
        self.assertEqual(out["items"][0]["id"], "a")
        self.assertEqual(out["items"][0]["why"], "test why")
        self.assertIn("options", out["items"][0])
        self.assertEqual(out["errors"], [])

    def test_queue_with_two_providers_and_actions(self):
        """queue() with two providers returns items in provider order."""
        reg = Registry()
        reg.register_provider("p1", lambda: [item("a", tab="work", why="w1", score=10)])
        reg.register_provider("p2", lambda: [item("b", tab="personal")])
        reg.register_action("act1", "Action 1", "*", lambda i, p, *, confirm: {}, False)

        result = reg.queue()
        self.assertEqual(len(result["queue_items"]), 2)
        self.assertEqual(result["queue_items"][0]["window_item"]["id"], "a")
        self.assertEqual(result["queue_items"][1]["window_item"]["id"], "b")
        self.assertEqual(result["errors"], [])

    def test_queue_tab_filtering(self):
        """queue() with tab filter returns only items in that tab."""
        reg = Registry()
        reg.register_provider("p", lambda: [
            item("a", tab="work"),
            item("b", tab="personal")
        ])

        result = reg.queue(tab="work")
        self.assertEqual(len(result["queue_items"]), 1)
        self.assertEqual(result["queue_items"][0]["window_item"]["id"], "a")

        result = reg.queue(tab="personal")
        self.assertEqual(len(result["queue_items"]), 1)
        self.assertEqual(result["queue_items"][0]["window_item"]["id"], "b")

    def test_queue_state_hiding(self):
        """queue() with state hides dismissed items."""
        reg = Registry()
        reg.register_provider("p", lambda: [
            item("a"),
            item("b")
        ])

        state = ItemState(self.tmp.name)
        state.dismiss("a")

        result = reg.queue(state=state)
        self.assertEqual(len(result["queue_items"]), 1)
        self.assertEqual(result["queue_items"][0]["window_item"]["id"], "b")

    def test_queue_failing_provider_error_reported(self):
        """queue() reports errors from failing providers."""
        reg = Registry()
        def boom():
            raise RuntimeError("provider failed")
        reg.register_provider("boom", boom)
        reg.register_provider("p", lambda: [item("a")])

        result = reg.queue()
        self.assertEqual(len(result["queue_items"]), 1)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["provider"], "boom")
        self.assertIn("RuntimeError", result["errors"][0]["error"])
        self.assertIn("provider failed", result["errors"][0]["error"])

    def test_queue_non_dict_item_skipped(self):
        """queue() skips non-dict items from providers."""
        reg = Registry()
        reg.register_provider("p", lambda: [
            item("a"),
            "not a dict",
            123,
            None
        ])

        result = reg.queue()
        self.assertEqual(len(result["queue_items"]), 1)
        self.assertEqual(result["queue_items"][0]["window_item"]["id"], "a")

    def test_queue_item_validation(self):
        """queue() produces items that pass validate_queue_item."""
        reg = Registry()
        reg.register_provider("p", lambda: [
            item("a", why="test", score=5),
            item("b", why="another", score=0)
        ])

        result = reg.queue()
        for qi in result["queue_items"]:
            errors = contracts.validate_queue_item(qi)
            self.assertEqual(errors, [], f"Queue item validation failed: {errors}")

    def test_queue_item_reason_from_why(self):
        """queue() item reason equals the why from window item."""
        reg = Registry()
        reg.register_provider("p", lambda: [item("a", why="because")])

        result = reg.queue()
        qi = result["queue_items"][0]
        self.assertEqual(qi.get("reason"), "because")

    def test_queue_item_priority_from_score(self):
        """queue() item priority equals the score from window item."""
        reg = Registry()
        reg.register_provider("p", lambda: [
            item("a", score=10),
            item("b", score=0),
            item("c")  # no score
        ])

        result = reg.queue()
        by_id = {qi["window_item"]["id"]: qi for qi in result["queue_items"]}
        self.assertEqual(by_id["a"].get("priority"), 10)
        self.assertEqual(by_id["b"].get("priority"), 0)
        self.assertNotIn("priority", by_id["c"])

    def test_attach_and_publish_with_bus(self):
        """outstanding() publishes items to bus when attached."""
        reg = Registry()
        reg.register_provider("p", lambda: [
            item("a", tab="work", why="work item"),
            item("b", tab="personal")
        ])

        bus = EventBus(self.tmp.name)
        reg.attach_event_bus(bus)

        # Call outstanding to publish
        out = reg.outstanding()
        self.assertEqual(len(out["items"]), 2)

        # Check bus has the events
        events = bus.events("task.created")
        self.assertEqual(len(events), 2)

    def test_bus_publish_failure_does_not_change_output(self):
        """Bus publish failures don't affect outstanding() output."""
        reg = Registry()
        reg.register_provider("p", lambda: [item("a"), item("b")])

        class FailingBus:
            def publish(self, *args, **kwargs):
                raise RuntimeError("bus error")

        reg.attach_event_bus(FailingBus())

        out = reg.outstanding()
        self.assertEqual(len(out["items"]), 2)
        self.assertEqual(out["errors"], [])

    def test_multiple_outstanding_calls_publish_same_items(self):
        """Multiple outstanding() calls publish each item once (dedup)."""
        reg = Registry()
        reg.register_provider("p", lambda: [
            item("a", why="first"),
            item("b", why="second")
        ])

        bus = EventBus(self.tmp.name)
        reg.attach_event_bus(bus)

        # First call
        reg.outstanding()
        events1 = bus.events("task.created")
        self.assertEqual(len(events1), 2)

        # Second call (items are static)
        reg.outstanding()
        events2 = bus.events("task.created")
        self.assertEqual(len(events2), 2)  # no new events due to dedup

    def test_provider_order_preserved_in_queue(self):
        """queue() preserves provider order."""
        reg = Registry()
        reg.register_provider("third", lambda: [item("c")])
        reg.register_provider("first", lambda: [item("a")])
        reg.register_provider("second", lambda: [item("b")])

        result = reg.queue()
        ids = [qi["window_item"]["id"] for qi in result["queue_items"]]
        self.assertEqual(ids, ["c", "a", "b"])

    def test_outstanding_with_bus_and_tab_filter(self):
        """outstanding() with bus and tab filter publishes all but returns filtered."""
        reg = Registry()
        reg.register_provider("p", lambda: [
            item("a", tab="work"),
            item("b", tab="personal")
        ])

        bus = EventBus(self.tmp.name)
        reg.attach_event_bus(bus)

        # Get work items
        out = reg.outstanding(tab="work")
        self.assertEqual(len(out["items"]), 1)
        self.assertEqual(out["items"][0]["id"], "a")

        # But bus still got both items
        events = bus.events("task.created")
        self.assertEqual(len(events), 2)

    def test_outstanding_window_item_from_queue_preserves_why(self):
        """outstanding() items preserve why from window_item via queue conversion."""
        reg = Registry()
        reg.register_provider("p", lambda: [item("a", why="original why")])

        out = reg.outstanding()
        self.assertEqual(out["items"][0]["why"], "original why")

    def test_queue_with_sensitivity_local_only(self):
        """queue() respects sensitivity field for local_only enforcement."""
        reg = Registry()
        def sensitive_provider():
            return [
                {**item("secret"), "sensitivity": "secret"},
                {**item("sensitive"), "sensitivity": "sensitive"},
                {**item("personal"), "sensitivity": "personal"},
            ]
        reg.register_provider("p", sensitive_provider)

        result = reg.queue()
        by_id = {qi["window_item"]["id"]: qi for qi in result["queue_items"]}

        # Secret and sensitive should have local_only=true
        self.assertTrue(by_id["secret"].get("local_only"))
        self.assertTrue(by_id["sensitive"].get("local_only"))
        # Personal should not have local_only (or False)
        self.assertNotIn("local_only", by_id["personal"])

    def test_outstanding_options_applied_to_converted_items(self):
        """outstanding() applies options to items converted from queue."""
        reg = Registry()
        reg.register_provider("p", lambda: [item("a", kind="note")])
        reg.register_action("note_action", "Note Action", ["note"], lambda i, p, *, confirm: {}, False)
        reg.register_action("all_action", "All Action", "*", lambda i, p, *, confirm: {}, False)

        out = reg.outstanding()
        options_ids = [o["action_id"] for o in out["items"][0]["options"]]
        self.assertIn("note_action", options_ids)
        self.assertIn("all_action", options_ids)


if __name__ == "__main__":
    unittest.main()
