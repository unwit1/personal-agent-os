import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agent_os.executive.knowledge_gaps import answer_to_candidate, score, select_questions


def gap(gap_id, **values):
    return {"id": gap_id, "question": f"Question {gap_id}?", **values}


class KnowledgeGapTests(unittest.TestCase):
    def test_low_value_gaps_discarded(self):
        result = select_questions([gap("low")])
        self.assertEqual(result["discarded"][0]["reason"], "low_value")

    def test_budget_asks_one_and_defers_rest(self):
        items = [gap(str(i), utility=1) for i in range(3)]
        result = select_questions(items, budget=1)
        self.assertEqual(len(result["ask"]), 1)
        self.assertEqual(len(result["deferred"]), 2)
        self.assertTrue(all(item["reason"] == "over_budget" for item in result["deferred"]))

    def test_ordering_is_deterministic(self):
        items = [gap("b", utility=1), gap("a", utility=1), gap("c", urgency=1)]
        result = select_questions(items, budget=3)
        self.assertEqual([item["id"] for item in result["ask"]], ["a", "b", "c"])

    def test_asked_items_have_explanation(self):
        result = select_questions([gap("useful", utility=1)])
        self.assertTrue(result["ask"][0]["why"].strip())
        self.assertIn("score", result["ask"][0]["why"])

    def test_penalties_lower_score(self):
        base = gap("x", utility=1)
        penalized = {**base, "sensitivity": 1, "interruption_cost": 1}
        self.assertLess(score(penalized), score(base))

    def test_answer_becomes_candidate(self):
        item = answer_to_candidate(gap("style"), " concise ", source="interview")
        self.assertEqual(item, {
            "kind": "preference_candidate",
            "statement": "Question style? -> concise",
            "evidence": ["knowledge-gap:style", "interview"],
            "confidence": 0.7,
        })


if __name__ == "__main__":
    unittest.main()
