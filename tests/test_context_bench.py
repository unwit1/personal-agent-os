from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator.context_bench import build


class ContextBenchTests(unittest.TestCase):
    def test_build_is_deterministic_and_omits_task_text(self) -> None:
        fixtures = Path(__file__).resolve().parent / "fixtures"
        corpus_path = fixtures / "economy-corpus.json"
        handoffs_path = fixtures / "economy-handoffs.json"
        corpus = json.loads(corpus_path.read_text(encoding="utf-8"))

        result = build(corpus_path, handoffs_path)

        self.assertEqual(result, build(corpus_path, handoffs_path))
        self.assertEqual(result["model_calls"], 0)
        self.assertEqual(result["compiler"]["totals"]["cases"], len(corpus))
        self.assertGreater(result["compiler"]["totals"]["naive_tokens"], result["compiler"]["totals"]["selective_tokens"])
        self.assertGreater(result["prompts"]["totals"]["cacheable_prefix_tokens"], 0)
        self.assertGreater(result["handoffs"]["tokens_avoided"], 0)
        self.assertIsNone(result["telemetry"])
        encoded = json.dumps(result)
        for case in corpus:
            self.assertNotIn(case["task"], encoded)


if __name__ == "__main__":
    unittest.main()
