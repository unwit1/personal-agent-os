"""Tests for executive next action ranking and selection."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive import window_queue
from agent_os.executive.next_action import RANKING, explain, next_item, rank


class TestRank(unittest.TestCase):
    def test_rank_empty_list(self):
        result = rank([])
        self.assertEqual(result, [])

    def test_rank_filters_non_dicts(self):
        items = [
            {"id": "qi-1", "priority": 10, "window_item": {"id": "w1", "age_days": 5}},
            "not a dict",
            None,
            42,
            {"id": "qi-2", "priority": 5, "window_item": {"id": "w2", "age_days": 3}},
        ]
        result = rank(items)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "qi-1")
        self.assertEqual(result[1]["id"], "qi-2")

    def test_rank_by_priority_descending(self):
        items = [
            {"id": "qi-1", "priority": 5, "window_item": {"id": "w1"}},
            {"id": "qi-2", "priority": 10, "window_item": {"id": "w2"}},
            {"id": "qi-3", "priority": 1, "window_item": {"id": "w3"}},
        ]
        result = rank(items)
        self.assertEqual(result[0]["id"], "qi-2")  # highest priority
        self.assertEqual(result[1]["id"], "qi-1")
        self.assertEqual(result[2]["id"], "qi-3")  # lowest priority

    def test_rank_default_priority_zero(self):
        items = [
            {"id": "qi-1", "priority": 5, "window_item": {"id": "w1"}},
            {"id": "qi-2", "window_item": {"id": "w2"}},  # no priority
        ]
        result = rank(items)
        self.assertEqual(result[0]["id"], "qi-1")  # priority 5
        self.assertEqual(result[1]["id"], "qi-2")  # priority 0 (default)

    def test_rank_ignore_bool_priority(self):
        items = [
            {"id": "qi-1", "priority": True, "window_item": {"id": "w1"}},
            {"id": "qi-2", "priority": 5, "window_item": {"id": "w2"}},
        ]
        result = rank(items)
        # bool should be treated as 0, so qi-2 (priority 5) comes first
        self.assertEqual(result[0]["id"], "qi-2")
        self.assertEqual(result[1]["id"], "qi-1")

    def test_rank_tiebreak_by_age_days_descending(self):
        items = [
            {"id": "qi-1", "priority": 5, "window_item": {"id": "w1", "age_days": 3}},
            {"id": "qi-2", "priority": 5, "window_item": {"id": "w2", "age_days": 10}},
            {"id": "qi-3", "priority": 5, "window_item": {"id": "w3", "age_days": 1}},
        ]
        result = rank(items)
        # Same priority, so sort by age_days descending
        self.assertEqual(result[0]["id"], "qi-2")  # age_days 10
        self.assertEqual(result[1]["id"], "qi-1")  # age_days 3
        self.assertEqual(result[2]["id"], "qi-3")  # age_days 1

    def test_rank_default_age_days_zero(self):
        items = [
            {"id": "qi-1", "priority": 5, "window_item": {"id": "w1", "age_days": 10}},
            {"id": "qi-2", "priority": 5, "window_item": {"id": "w2"}},  # no age_days
        ]
        result = rank(items)
        self.assertEqual(result[0]["id"], "qi-1")  # age_days 10
        self.assertEqual(result[1]["id"], "qi-2")  # age_days 0

    def test_rank_ignore_bool_age_days(self):
        items = [
            {"id": "qi-1", "priority": 5, "window_item": {"id": "w1", "age_days": True}},
            {"id": "qi-2", "priority": 5, "window_item": {"id": "w2", "age_days": 10}},
        ]
        result = rank(items)
        # bool should be treated as 0
        self.assertEqual(result[0]["id"], "qi-2")  # age_days 10
        self.assertEqual(result[1]["id"], "qi-1")  # age_days 0 (bool converted)

    def test_rank_full_tiebreak_by_id(self):
        items = [
            {"id": "qi-c", "priority": 5, "window_item": {"id": "w1", "age_days": 10}},
            {"id": "qi-a", "priority": 5, "window_item": {"id": "w2", "age_days": 10}},
            {"id": "qi-b", "priority": 5, "window_item": {"id": "w3", "age_days": 10}},
        ]
        result = rank(items)
        # All same priority and age_days, so sort by id ascending
        self.assertEqual(result[0]["id"], "qi-a")
        self.assertEqual(result[1]["id"], "qi-b")
        self.assertEqual(result[2]["id"], "qi-c")

    def test_rank_does_not_mutate_input(self):
        items = [
            {"id": "qi-1", "priority": 5, "window_item": {"id": "w1"}},
            {"id": "qi-2", "priority": 10, "window_item": {"id": "w2"}},
        ]
        original_order = [item["id"] for item in items]
        result = rank(items)
        # Input should be unchanged
        self.assertEqual([item["id"] for item in items], original_order)
        # Result should be different order
        result_order = [item["id"] for item in result]
        self.assertEqual(result_order, ["qi-2", "qi-1"])

    def test_rank_with_window_queue_generated_items(self):
        # Test with real queue items from window_queue.queue_item_from_window_item
        w1 = {"id": "w1", "title": "First", "kind": "task", "tab": "inbox", "score": 10}
        w2 = {"id": "w2", "title": "Second", "kind": "task", "tab": "inbox", "score": 5}

        qi1 = window_queue.queue_item_from_window_item(w1, "provider1", "2026-10-05T00:00:00+00:00")
        qi2 = window_queue.queue_item_from_window_item(w2, "provider1", "2026-10-05T00:00:00+00:00")

        # Set age_days for ranking test
        qi1["window_item"]["age_days"] = 5
        qi2["window_item"]["age_days"] = 3

        result = rank([qi2, qi1])
        self.assertEqual(result[0]["id"], qi1["id"])
        self.assertEqual(result[1]["id"], qi2["id"])


class TestExplain(unittest.TestCase):
    def test_explain_unknown_id_returns_none(self):
        items = [
            {"id": "qi-1", "entity_id": "ex-task-abc", "provider": "p1", "source": "s1",
             "window_item": {"id": "w1", "kind": "task", "tab": "inbox"}},
        ]
        result = explain(items, "unknown-id")
        self.assertIsNone(result)

    def test_explain_by_queue_item_id(self):
        items = [
            {"id": "qi-1", "entity_id": "ex-task-abc", "provider": "p1", "source": "s1",
             "reason": "urgent", "priority": 5,
             "window_item": {"id": "w1", "kind": "task", "tab": "inbox", "age_days": 3}},
        ]
        result = explain(items, "qi-1")
        self.assertIsNotNone(result)
        self.assertEqual(result["queue_item_id"], "qi-1")
        self.assertEqual(result["entity_id"], "ex-task-abc")
        self.assertEqual(result["provider"], "p1")
        self.assertEqual(result["reason"], "urgent")
        self.assertEqual(result["priority"], 5)
        self.assertEqual(result["age_days"], 3)
        self.assertEqual(result["rank"], 1)
        self.assertEqual(result["of"], 1)

    def test_explain_by_window_item_id(self):
        items = [
            {"id": "qi-1", "entity_id": "ex-task-abc", "provider": "p1", "source": "s1",
             "window_item": {"id": "w1", "kind": "task", "tab": "inbox"}},
        ]
        result = explain(items, "w1")
        self.assertIsNotNone(result)
        self.assertEqual(result["item_id"], "w1")
        self.assertEqual(result["queue_item_id"], "qi-1")

    def test_explain_by_window_item_id_as_int(self):
        items = [
            {"id": "qi-1", "entity_id": "ex-task-abc", "provider": "p1", "source": "s1",
             "window_item": {"id": 123, "kind": "task", "tab": "inbox"}},
        ]
        result = explain(items, 123)
        self.assertIsNotNone(result)
        self.assertEqual(result["item_id"], "123")

    def test_explain_respects_ranking(self):
        items = [
            {"id": "qi-1", "entity_id": "ex-task-a", "provider": "p1", "source": "s1",
             "priority": 5, "window_item": {"id": "w1", "age_days": 3}},
            {"id": "qi-2", "entity_id": "ex-task-b", "provider": "p1", "source": "s1",
             "priority": 10, "window_item": {"id": "w2", "age_days": 2}},
            {"id": "qi-3", "entity_id": "ex-task-c", "provider": "p1", "source": "s1",
             "priority": 1, "window_item": {"id": "w3", "age_days": 1}},
        ]
        result = explain(items, "w1")
        self.assertIsNotNone(result)
        self.assertEqual(result["rank"], 2)
        self.assertEqual(result["of"], 3)

    def test_explain_no_title_in_output(self):
        items = [
            {"id": "qi-1", "entity_id": "ex-task-abc", "provider": "p1", "source": "s1",
             "window_item": {"id": "w1", "title": "This is a secret title", "kind": "task"}},
        ]
        result = explain(items, "qi-1")
        self.assertIsNotNone(result)
        self.assertNotIn("title", result)
        self.assertNotIn("This is a secret title", str(result))

    def test_explain_missing_optional_fields(self):
        items = [
            {"id": "qi-1", "entity_id": "ex-task-abc", "provider": "p1", "source": "s1",
             "window_item": {"id": "w1"}},
        ]
        result = explain(items, "qi-1")
        self.assertIsNotNone(result)
        self.assertIsNone(result["reason"])
        self.assertIsNone(result["priority"])
        self.assertIsNone(result["age_days"])
        self.assertIsNone(result["kind"])
        self.assertIsNone(result["tab"])

    def test_explain_bool_priority_returns_none(self):
        items = [
            {"id": "qi-1", "entity_id": "ex-task-abc", "provider": "p1", "source": "s1",
             "priority": True, "window_item": {"id": "w1"}},
        ]
        result = explain(items, "qi-1")
        self.assertIsNotNone(result)
        self.assertIsNone(result["priority"])

    def test_explain_bool_age_days_returns_none(self):
        items = [
            {"id": "qi-1", "entity_id": "ex-task-abc", "provider": "p1", "source": "s1",
             "window_item": {"id": "w1", "age_days": False}},
        ]
        result = explain(items, "qi-1")
        self.assertIsNotNone(result)
        self.assertIsNone(result["age_days"])

    def test_explain_contains_ranking_string(self):
        items = [
            {"id": "qi-1", "entity_id": "ex-task-abc", "provider": "p1", "source": "s1",
             "window_item": {"id": "w1"}},
        ]
        result = explain(items, "qi-1")
        self.assertIsNotNone(result)
        self.assertEqual(result["ranking"], RANKING)


class TestNextItem(unittest.TestCase):
    def test_next_item_empty_list(self):
        result = next_item([])
        self.assertIsNone(result["next"])
        self.assertEqual(result["considered"], 0)
        self.assertIsNone(result["why"])

    def test_next_item_returns_top_ranked(self):
        items = [
            {"id": "qi-1", "entity_id": "ex-task-a", "provider": "p1", "source": "s1",
             "priority": 5, "window_item": {"id": "w1"}},
            {"id": "qi-2", "entity_id": "ex-task-b", "provider": "p1", "source": "s1",
             "priority": 10, "window_item": {"id": "w2"}},
        ]
        result = next_item(items)
        self.assertIsNotNone(result["next"])
        self.assertEqual(result["next"]["id"], "qi-2")
        self.assertEqual(result["considered"], 2)

    def test_next_item_why_contains_explain_result(self):
        items = [
            {"id": "qi-1", "entity_id": "ex-task-a", "provider": "p1", "source": "s1",
             "priority": 5, "window_item": {"id": "w1"}},
            {"id": "qi-2", "entity_id": "ex-task-b", "provider": "p1", "source": "s1",
             "priority": 10, "window_item": {"id": "w2"}},
        ]
        result = next_item(items)
        self.assertIsNotNone(result["why"])
        self.assertEqual(result["why"]["queue_item_id"], "qi-2")
        self.assertEqual(result["why"]["rank"], 1)
        self.assertEqual(result["why"]["of"], 2)

    def test_next_item_single_item(self):
        items = [
            {"id": "qi-1", "entity_id": "ex-task-a", "provider": "p1", "source": "s1",
             "window_item": {"id": "w1"}},
        ]
        result = next_item(items)
        self.assertEqual(result["next"]["id"], "qi-1")
        self.assertEqual(result["considered"], 1)
        self.assertEqual(result["why"]["rank"], 1)
        self.assertEqual(result["why"]["of"], 1)

    def test_next_item_does_not_mutate_input(self):
        items = [
            {"id": "qi-1", "entity_id": "ex-task-a", "provider": "p1", "source": "s1",
             "priority": 5, "window_item": {"id": "w1"}},
            {"id": "qi-2", "entity_id": "ex-task-b", "provider": "p1", "source": "s1",
             "priority": 10, "window_item": {"id": "w2"}},
        ]
        original_order = [item["id"] for item in items]
        next_item(items)
        # Input should be unchanged
        self.assertEqual([item["id"] for item in items], original_order)

    def test_next_item_with_non_dict_items(self):
        items = [
            "not a dict",
            {"id": "qi-1", "entity_id": "ex-task-a", "provider": "p1", "source": "s1",
             "priority": 10, "window_item": {"id": "w1"}},
            None,
        ]
        result = next_item(items)
        self.assertEqual(result["next"]["id"], "qi-1")
        self.assertEqual(result["considered"], 1)


class TestRankingConstant(unittest.TestCase):
    def test_ranking_constant_value(self):
        self.assertEqual(RANKING, "priority desc, then age_days desc, then queue item id asc")


class TestWithRealQueueItems(unittest.TestCase):
    def test_rank_with_real_queue_items(self):
        # Create real queue items using window_queue
        w1 = {"id": "item1", "title": "High priority", "kind": "task", "tab": "inbox", "score": 10}
        w2 = {"id": "item2", "title": "Low priority", "kind": "task", "tab": "inbox", "score": 5}

        qi1 = window_queue.queue_item_from_window_item(w1, "provider1", "2026-10-05T00:00:00+00:00")
        qi2 = window_queue.queue_item_from_window_item(w2, "provider2", "2026-10-05T00:00:00+00:00")

        # Set age_days
        qi1["window_item"]["age_days"] = 2
        qi2["window_item"]["age_days"] = 5

        result = rank([qi2, qi1])
        # qi1 has higher priority (10 vs 5), so comes first despite lower age_days
        self.assertEqual(result[0]["id"], qi1["id"])
        self.assertEqual(result[0]["provider"], "provider1")

    def test_explain_with_real_queue_items(self):
        w1 = {"id": "item1", "title": "Important task", "kind": "decision", "tab": "today", "score": 8}

        qi1 = window_queue.queue_item_from_window_item(w1, "test_provider", "2026-10-05T10:00:00+00:00")
        qi1["window_item"]["age_days"] = 1

        result = explain([qi1], qi1["id"])
        self.assertIsNotNone(result)
        self.assertEqual(result["provider"], "test_provider")
        self.assertEqual(result["kind"], "decision")
        self.assertEqual(result["tab"], "today")
        self.assertEqual(result["priority"], 8)
        self.assertEqual(result["age_days"], 1)
        self.assertNotIn("Important task", str(result))  # title never included


if __name__ == "__main__":
    unittest.main()
