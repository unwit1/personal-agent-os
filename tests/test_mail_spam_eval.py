import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.mail import spam_eval  # noqa: E402


class SpamEvalTests(unittest.TestCase):
    def test_set_is_large_and_labeled(self):
        self.assertGreaterEqual(len(spam_eval.SYNTHETIC), 40)
        self.assertEqual({m["label"] for m in spam_eval.SYNTHETIC}, {"human", "filtered"})

    def test_precision_recall(self):
        result = spam_eval.evaluate()
        self.assertGreaterEqual(result["precision"], 0.9, result)
        self.assertGreaterEqual(result["recall"], 0.9, result)
        total = sum(result[k] for k in ("tp", "fp", "fn", "tn"))
        self.assertEqual(total, len(spam_eval.SYNTHETIC))

    def test_review_queue(self):
        queue = spam_eval.evaluate()["review_queue"]
        self.assertTrue(queue)
        for entry in queue:
            self.assertTrue(entry["reasons"])
            self.assertIn("subject", entry)
            self.assertIn("sender", entry)

    def test_deterministic(self):
        self.assertEqual(spam_eval.evaluate(), spam_eval.evaluate())


if __name__ == "__main__":
    unittest.main()
