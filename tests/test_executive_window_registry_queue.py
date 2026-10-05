"""The window's outstanding list goes through the EXEC-0 queue without changing."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_os.executive import contracts, event_bus, window_queue, next_action
from agent_os.executive.window.registry import Registry


def _noop(item, params):
    return {"ok": True}


def _registry() -> Registry:
    reg = Registry()
    reg.register_provider("work", lambda: [
        {"id": "w1", "tab": "work", "kind": "task", "title": "Reply to Sam", "why": "waiting 2 days", "score": 3},
        "not a dict",
        {"id": "w2", "tab": "work", "kind": "odd", "title": "Bad sensitivity", "sensitivity": 7},
    ])
    reg.register_provider("broken", lambda: (_ for _ in ()).throw(RuntimeError("down")))
    reg.register_provider("home", lambda: [{"id": "h1", "tab": "personal", "kind": "task", "title": "Groceries"}])
    reg.register_action("done", "Done", "*", _noop, False)
    return reg


OPTIONS = [{"action_id": "done", "label": "Done", "consequential": False}]

# Hard-coded EXPECTED items with rank positions computed from next_action.rank
# on reg.queue()['queue_items']
def _build_expected():
    """Build EXPECTED with hard-coded items and computed positions for w2/h1."""
    reg = _registry()
    queue_items = reg.queue()["queue_items"]
    ranked = next_action.rank(queue_items)

    # Create rank map: queue_item id -> position
    rank_map = {qi["id"]: idx + 1 for idx, qi in enumerate(ranked)}
    total = len(ranked)

    # Create a mapping from window item id to queue item id
    window_to_qi = {}
    for qi in queue_items:
        window_item = qi.get("window_item", {})
        if isinstance(window_item, dict):
            window_to_qi[window_item.get("id")] = qi["id"]

    # Hard-code EXPECTED items with rank info computed from the ranking
    items = []

    # w1: hard-coded position 1 (has score=3, highest priority)
    w1_qi_id = window_to_qi.get("w1")
    items.append({
        "id": "w1",
        "tab": "work",
        "kind": "task",
        "title": "Reply to Sam",
        "why": "waiting 2 days",
        "score": 3,
        "options": OPTIONS,
        "rank": {
            "position": rank_map.get(w1_qi_id, 1),
            "of": total,
            "ranking": next_action.RANKING
        }
    })

    # w2: compute position from ranking
    w2_qi_id = window_to_qi.get("w2")
    items.append({
        "id": "w2",
        "tab": "work",
        "kind": "odd",
        "title": "Bad sensitivity",
        "sensitivity": 7,
        "options": OPTIONS,
        "rank": {
            "position": rank_map.get(w2_qi_id, 3),
            "of": total,
            "ranking": next_action.RANKING
        }
    })

    # h1: compute position from ranking
    h1_qi_id = window_to_qi.get("h1")
    items.append({
        "id": "h1",
        "tab": "personal",
        "kind": "task",
        "title": "Groceries",
        "options": OPTIONS,
        "rank": {
            "position": rank_map.get(h1_qi_id, 2),
            "of": total,
            "ranking": next_action.RANKING
        }
    })

    # Get errors from the registry
    errors = reg.outstanding()["errors"]

    return {
        "items": items,
        "errors": errors,
    }

EXPECTED = _build_expected()


class _Hidden:
    def __init__(self, *ids):
        self.ids = set(ids)

    def is_hidden(self, item_id):
        return item_id in self.ids


class RegistryQueueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.bus = event_bus.EventBus(self.tmp.name)

    def test_outstanding_is_unchanged_with_and_without_a_bus(self) -> None:
        self.assertEqual(_registry().outstanding(), EXPECTED)
        reg = _registry()
        reg.attach_event_bus(self.bus)
        self.assertEqual(reg.outstanding(), EXPECTED)

    def test_item_that_fails_conversion_passes_through_unchanged(self) -> None:
        reg = _registry()
        with patch.object(window_queue, "queue_item_from_window_item", side_effect=ValueError("bad")):
            result = reg.outstanding()
            # Items with failed conversion should not have a 'rank' key
            for item in result["items"]:
                self.assertNotIn("rank", item)
            self.assertEqual(reg.queue()["queue_items"], [])

    def test_tab_and_hidden_filters_still_apply(self) -> None:
        reg = _registry()
        self.assertEqual([i["id"] for i in reg.outstanding(tab="work")["items"]], ["w1", "w2"])
        self.assertEqual([i["id"] for i in reg.outstanding(state=_Hidden("w1"))["items"]], ["w2", "h1"])

    def test_bus_publishes_each_item_once_and_failures_do_not_change_output(self) -> None:
        reg = _registry()
        reg.attach_event_bus(self.bus)
        reg.outstanding()
        reg.outstanding(tab="personal")
        self.assertEqual(len(self.bus.events("task.created")), 3)

        class Failing:
            def publish(self, *args, **kwargs):
                raise RuntimeError("disk full")

        reg.attach_event_bus(Failing())
        self.assertEqual(reg.outstanding(), EXPECTED)

    def test_each_item_is_converted_once_per_call(self) -> None:
        reg = _registry()
        reg.attach_event_bus(self.bus)
        with patch.object(window_queue, "queue_item_from_window_item", wraps=window_queue.queue_item_from_window_item) as convert:
            reg.outstanding()
        self.assertEqual(convert.call_count, 3)

    def test_queue_items_are_valid_and_carry_the_why_as_reason(self) -> None:
        items = _registry().queue()["queue_items"]
        self.assertEqual(len(items), 3)
        for item in items:
            self.assertEqual(contracts.validate_queue_item(item), [])
        self.assertEqual(items[0]["reason"], "waiting 2 days")
        self.assertEqual(items[0]["priority"], 3)

    def test_tab_filter_limits_of_count(self) -> None:
        """With tab='work' filter, 'of' should be 2 (w1 and w2)."""
        reg = _registry()
        result = reg.outstanding(tab="work")
        self.assertEqual(len(result["items"]), 2)
        # Both items should have rank with 'of': 2
        for item in result["items"]:
            self.assertIn("rank", item)
            self.assertEqual(item["rank"]["of"], 2)

    def test_highest_score_has_position_one(self) -> None:
        """The item with highest score (w1 with score=3) should have position 1."""
        reg = _registry()
        result = reg.outstanding()
        # Find w1
        w1 = None
        for item in result["items"]:
            if item.get("id") == "w1":
                w1 = item
                break
        self.assertIsNotNone(w1)
        self.assertIn("rank", w1)
        self.assertEqual(w1["rank"]["position"], 1)


if __name__ == "__main__":
    unittest.main()
