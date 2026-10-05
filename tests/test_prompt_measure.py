from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator.prompt_measure import measure


class PromptMeasureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.run = {
            "run_id": "run-20261001T000000Z-aaaaaa",
            "goal": "synthetic goal",
            "project": None,
            "policy": {"shared_prefix": False},
        }
        self.nodes = [
            {"id": "node-implementer-1", "role": "implementer", "goal": "implement goal", "scope": ["a.py"], "validators": []},
            {"id": "node-implementer-2", "role": "implementer", "goal": "implement goal two", "scope": ["b.py"], "validators": []},
            {"id": "node-reviewer", "role": "reviewer", "goal": "review goal", "scope": [], "validators": []},
            {"id": "node-planner", "role": "planner", "goal": "plan goal", "scope": [], "validators": []},
        ]

    def test_measures_deterministically_and_omits_prompt_contents(self) -> None:
        result = measure(self.run, self.nodes, repo_map="synthetic map", diff="synthetic diff")
        self.assertEqual(result, measure(self.run, self.nodes, repo_map="synthetic map", diff="synthetic diff"))
        self.assertEqual(result["model_calls"], 0)
        self.assertEqual({role: item["count"] for role, item in result["roles"].items()}, {
            "implementer": 2, "reviewer": 1, "planner": 1,
        })
        self.assertEqual(result["totals"]["cacheable_prefix_tokens"], 0)
        encoded = json.dumps(result)
        for node in self.nodes:
            self.assertNotIn(node["id"], encoded)
            self.assertNotIn(node["goal"], encoded)
        self.assertNotIn(self.run["goal"], encoded)

    def test_shared_prefix_reports_reusable_tokens(self) -> None:
        self.run["policy"]["shared_prefix"] = True
        result = measure(self.run, self.nodes, repo_map="synthetic map", diff="synthetic diff")
        self.assertGreater(result["totals"]["cacheable_prefix_tokens"], 0)
        self.assertGreater(result["roles"]["implementer"]["prefix_tokens"], 0)


if __name__ == "__main__":
    unittest.main()
