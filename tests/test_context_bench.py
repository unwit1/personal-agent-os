from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator.context_bench import SCHEMA, build, compare


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

    def test_compare_identical_reports_are_unchanged(self) -> None:
        fixtures = Path(__file__).resolve().parent / "fixtures"
        result = build(fixtures / "economy-corpus.json", fixtures / "economy-handoffs.json")

        compared = compare(result, result)

        self.assertFalse(compared["regressed"])
        self.assertEqual(compared["regressions"], [])
        self.assertTrue(all(item["status"] == "unchanged" for item in compared["metrics"]))

    def test_compare_reports_regressions_and_missing_values(self) -> None:
        baseline = {
            "schema": SCHEMA,
            "compiler": {"totals": {"selective_tokens": 10, "tokens_avoided": 5, "all_within_budget": True}},
            "prompts": {"totals": {"total_tokens": 20, "cacheable_prefix_tokens": 4}, "roles": {"planner": {"total_tokens": 8}}},
            "handoffs": {"compacted_tokens": 3, "tokens_avoided": 2},
        }
        current = {
            "compiler": {"totals": {"selective_tokens": 11, "tokens_avoided": 6, "all_within_budget": False}},
            "prompts": {"totals": {"total_tokens": 19, "cacheable_prefix_tokens": 3}, "roles": {"reviewer": {"total_tokens": 7}}},
            "handoffs": {"compacted_tokens": 3, "tokens_avoided": 2},
        }

        compared = compare(baseline, current)

        self.assertTrue(compared["regressed"])
        self.assertEqual(compared["regressions"], [
            "compiler.totals.selective_tokens",
            "prompts.totals.cacheable_prefix_tokens",
            "compiler.totals.all_within_budget",
        ])
        self.assertEqual(compared["metrics"][2]["metric"], "prompts.roles.planner.total_tokens")
        self.assertEqual(compared["metrics"][2]["status"], "missing")
        self.assertEqual(compared["metrics"][3]["metric"], "prompts.roles.reviewer.total_tokens")
        self.assertEqual(compared["metrics"][3]["status"], "missing")

    def test_compare_requires_baseline_schema(self) -> None:
        with self.assertRaisesRegex(ValueError, SCHEMA):
            compare({"schema": "wrong"}, {})


if __name__ == "__main__":
    unittest.main()
