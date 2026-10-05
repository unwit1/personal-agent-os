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

    def test_scope_maps_adds_tokens_to_relevant_roles(self) -> None:
        scope_maps = {
            "node-implementer-1": "Files in your scope (local map; lines, top-level names):\n- src/x.py (10 lines)"
        }
        result_without = measure(self.run, self.nodes, repo_map="synthetic map", diff="synthetic diff")
        result_with = measure(self.run, self.nodes, repo_map="synthetic map", diff="synthetic diff", scope_maps=scope_maps)

        self.assertGreater(
            result_with["roles"]["implementer"]["total_tokens"],
            result_without["roles"]["implementer"]["total_tokens"]
        )
        self.assertGreater(result_with["roles"]["implementer"]["scope_map_tokens"], 0)
        self.assertEqual(result_without["roles"]["implementer"]["scope_map_tokens"], 0)

    def test_scope_maps_with_shared_prefix_preserves_prefix_tokens(self) -> None:
        self.run["policy"]["shared_prefix"] = True
        scope_maps = {
            "node-implementer-1": "Files in your scope (local map; lines, top-level names):\n- src/x.py (10 lines)"
        }
        result_without = measure(self.run, self.nodes, repo_map="synthetic map", diff="synthetic diff")
        result_with = measure(self.run, self.nodes, repo_map="synthetic map", diff="synthetic diff", scope_maps=scope_maps)

        self.assertEqual(
            result_without["roles"]["implementer"]["prefix_tokens"],
            result_with["roles"]["implementer"]["prefix_tokens"]
        )
        self.assertGreater(result_with["roles"]["implementer"]["scope_map_tokens"], 0)

    def test_scope_maps_ignored_for_planner(self) -> None:
        scope_maps = {
            "node-planner": "Files in your scope (local map; lines, top-level names):\n- src/x.py (10 lines)"
        }
        result = measure(self.run, self.nodes, repo_map="synthetic map", diff="synthetic diff", scope_maps=scope_maps)
        self.assertEqual(result["roles"]["planner"]["scope_map_tokens"], 0)

    def test_scope_map_tokens_zero_without_scope_maps(self) -> None:
        result = measure(self.run, self.nodes, repo_map="synthetic map", diff="synthetic diff")
        for role, stats in result["roles"].items():
            self.assertEqual(stats["scope_map_tokens"], 0)
        self.assertEqual(result["totals"]["scope_map_tokens"], 0)


if __name__ == "__main__":
    unittest.main()
