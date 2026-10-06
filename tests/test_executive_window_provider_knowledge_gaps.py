import sys
from pathlib import Path
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.window.gap_store import GapStore
from agent_os.executive.window.providers_knowledge_gaps import (
    BUDGET,
    knowledge_gap_items,
)


class KnowledgeGapProviderTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = GapStore(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    @staticmethod
    def gap(gap_id, question, utility, **extra):
        return {
            "id": gap_id,
            "question": question,
            "utility": utility,
            **extra,
        }

    def test_items_use_window_format(self):
        self.store.add([
            self.gap("project-owner", "Who owns the project?", 0.8,
                     topic="ownership", project="alpha"),
        ], tab="work")

        self.assertEqual(knowledge_gap_items(self.store), [{
            "id": "knowledge-gap:project-owner",
            "kind": "knowledge_gap_question",
            "title": "Who owns the project?",
            "tab": "work",
            "score": 0.28,
            "source": "Knowledge gap",
            "sensitivity": "personal",
            "why": "score 0.28: utility 0.80",
            "context": {
                "gap_id": "project-owner",
                "topic": "ownership",
                "project": "alpha",
            },
        }])

    def test_budget_and_highest_score_first(self):
        gaps = [
            self.gap(f"gap-{index}", f"Question {index}?", utility)
            for index, utility in enumerate((0.7, 1.0, 0.6, 0.8, 0.9))
        ]
        self.store.add(gaps)

        items = knowledge_gap_items(self.store)

        self.assertEqual(len(items), BUDGET)
        self.assertEqual(
            [item["context"]["gap_id"] for item in items],
            ["gap-1", "gap-4", "gap-3"],
        )
        self.assertEqual(
            [item["score"] for item in items],
            sorted((item["score"] for item in items), reverse=True),
        )

    def test_low_value_and_answered_gaps_are_excluded(self):
        self.store.add([
            self.gap("low-value", "A low-value question?", 0),
            self.gap("answered", "An answered question?", 1.0),
            self.gap("useful", "A useful question?", 0.8),
        ])
        self.store.mark_answered("answered", "Already handled", {"created": []})

        items = knowledge_gap_items(self.store)

        self.assertEqual([item["context"]["gap_id"] for item in items], ["useful"])


if __name__ == "__main__":
    unittest.main()
