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

    def test_outstanding_exact_output_no_bus(self):
        """outstanding() without bus returns exact expected structure."""
        reg = Registry()
        reg.register_provider("p1", lambda: [
            item("task1", tab="work", kind="task", why="urgent", score=10)
        ])
        reg.register_action("do_it", "Do It", "*", lambda i, p, *, confirm: {}, False)

        out = reg.outstanding()

        self.assertEqual(len(out["items"]), 1)
        self.assertEqual(out["errors"], [])

        task = out["items"][0]
        self.assertEqual(task["id"], "task1")
        self.assertEqual(task["tab"], "work")
        self.assertEqual(task["kind"], "task")
        self.assertEqual(task["title"], "task1")
        self.assertEqual(task["source"], "test")
        self.assertEqual(task["why"], "urgent")
        self.assertEqual(task["score"], 10)
        self.assertEqual(len(task["options"]), 1)
        self.assertEqual(task["options"][0]["action_id"], "do_it")
        self.assertEqual(task["options"][0]["label"], "Do It")
        self.assertEqual(task["options"][0]["consequential"], False)

    def test_outstanding_exact_output_with_bus(self):
        """outstanding() with bus returns exact expected structure."""
        reg = Registry()
        reg.register_provider("p1", lambda: [
            item("task1", tab="work", kind="task", why="urgent", score=10)
        ])
        reg.register_action("do_it", "Do It", "*", lambda i, p, *, confirm: {}, False)

        bus = EventBus(self.tmp.name)
        reg.attach_event_bus(bus)

        out = reg.outstanding()

        self.assertEqual(len(out["items"]), 1)
        self.assertEqual(out["errors"], [])

        task = out["items"][0]
        self.assertEqual(task["id"], "task1")
        self.assertEqual(task["tab"], "work")
        self.assertEqual(task["why"], "urgent")

        # Verify bus received the event
        events = bus.events("task.created")
        self.assertEqual(len(events), 1)

    def test_outstanding_exact_output_tab_filtering(self):
        """outstanding(tab=...) returns exact expected structure with correct filtering."""
        reg = Registry()
        reg.register_provider("p1", lambda: [
            item("task1", tab="work", why="work item"),
            item("task2", tab="personal", why="personal item")
        ])
        reg.register_action("do_it", "Do It", "*", lambda i, p, *, confirm: {}, False)

        out_work = reg.outstanding(tab="work")
        self.assertEqual(len(out_work["items"]), 1)
        self.assertEqual(out_work["items"][0]["id"], "task1")
        self.assertEqual(out_work["items"][0]["why"], "work item")
        self.assertEqual(out_work["errors"], [])

        out_personal = reg.outstanding(tab="personal")
        self.assertEqual(len(out_personal["items"]), 1)
        self.assertEqual(out_personal["items"][0]["id"], "task2")
        self.assertEqual(out_personal["items"][0]["why"], "personal item")
        self.assertEqual(out_personal["errors"], [])

    def test_outstanding_exact_output_state_hiding(self):
        """outstanding(state=...) returns exact expected structure with correct hiding."""
        reg = Registry()
        reg.register_provider("p1", lambda: [
            item("task1"),
            item("task2")
        ])
        reg.register_action("do_it", "Do It", "*", lambda i, p, *, confirm: {}, False)

        state = ItemState(self.tmp.name)
        state.dismiss("task1")

        out = reg.outstanding(state=state)
        self.assertEqual(len(out["items"]), 1)
        self.assertEqual(out["items"][0]["id"], "task2")
        self.assertEqual(out["errors"], [])

    def test_bus_publish_failure_full_output_unchanged(self):
        """Bus publish failures don't affect any part of outstanding() output."""
        reg = Registry()
        reg.register_provider("p1", lambda: [
            item("task1", why="test", score=5),
            item("task2", why="another", score=10)
        ])
        reg.register_action("act1", "Action 1", "*", lambda i, p, *, confirm: {}, False)

        class FailingBus:
            def publish(self, *args, **kwargs):
                raise RuntimeError("bus broken")

        reg.attach_event_bus(FailingBus())

        out = reg.outstanding()

        # Full output should be identical to no-bus case
        self.assertEqual(len(out["items"]), 2)
        self.assertEqual(out["items"][0]["id"], "task1")
        self.assertEqual(out["items"][0]["why"], "test")
        self.assertEqual(out["items"][0]["score"], 5)
        self.assertEqual(out["items"][1]["id"], "task2")
        self.assertEqual(out["items"][1]["why"], "another")
        self.assertEqual(out["items"][1]["score"], 10)
        self.assertEqual(out["errors"], [])

    def test_outstanding_exact_literal_with_raising_provider_non_dict_and_actions(self):
        """Exact-literal test: raising provider + non-dict + valid items with actions, no bus vs with bus."""
        reg = Registry()

        # Provider that raises
        def boom():
            raise RuntimeError("boom")

        # Providers with mixed content
        reg.register_provider("boom", boom)
        reg.register_provider("p1", lambda: [
            item("work_item", tab="work", why="urgent", score=10)
        ])
        reg.register_provider("p2", lambda: [
            "not a dict",
            123,
            item("personal_item", tab="personal")
        ])

        # Actions
        reg.register_action("action1", "Act 1", "*", lambda i, p, *, confirm: {}, False)

        # Test without bus
        out_no_bus = reg.outstanding()

        expected_items = [
            {
                "id": "work_item",
                "tab": "work",
                "kind": "note",
                "title": "work_item",
                "source": "test",
                "why": "urgent",
                "score": 10,
                "options": [
                    {"action_id": "action1", "label": "Act 1", "consequential": False}
                ]
            },
            {
                "id": "personal_item",
                "tab": "personal",
                "kind": "note",
                "title": "personal_item",
                "source": "test",
                "options": [
                    {"action_id": "action1", "label": "Act 1", "consequential": False}
                ]
            }
        ]

        expected_errors = [
            {"provider": "boom", "error": "RuntimeError: boom"}
        ]

        self.assertEqual(len(out_no_bus["items"]), 2)
        self.assertEqual(out_no_bus["items"], expected_items)
        self.assertEqual(len(out_no_bus["errors"]), 1)
        self.assertEqual(out_no_bus["errors"][0]["provider"], "boom")
        self.assertIn("RuntimeError", out_no_bus["errors"][0]["error"])
        self.assertIn("boom", out_no_bus["errors"][0]["error"])

        # Test with bus attached
        bus = EventBus(self.tmp.name)
        reg.attach_event_bus(bus)

        out_with_bus = reg.outstanding()

        # Output should be identical
        self.assertEqual(out_with_bus["items"], expected_items)
        self.assertEqual(len(out_with_bus["errors"]), 1)
        self.assertEqual(out_with_bus["errors"][0]["provider"], "boom")
        self.assertIn("RuntimeError", out_with_bus["errors"][0]["error"])

        # Bus should have received exactly 2 events (one per valid item)
        events = bus.events("task.created")
        self.assertEqual(len(events), 2)


if __name__ == "__main__":
    unittest.main()
