from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import prompts  # noqa: E402


class PromptScopeMapTests(unittest.TestCase):
    def setUp(self):
        self.run = {"run_id": "r", "goal": "g", "policy": {}, "nodes": {}}

    def test_implementer_gets_scope_map_only_when_provided(self):
        node = {"id": "t1", "role": "implementer", "goal": "g", "scope": ["a.py"], "context_budget": 1200}
        header = "Map of the files in your scope (built locally, no need to re-list them; open only what you need):"
        prompt, _ = prompts.build_measured(self.run, node, scope_map="- a.py (3 lines): f")
        without_map, _ = prompts.build_measured(self.run, node)
        self.assertIn(header, prompt)
        self.assertIn("- a.py (3 lines): f", prompt)
        self.assertNotIn(header, without_map)

    def test_reviewer_does_not_get_scope_map(self):
        node = {"id": "t1", "role": "reviewer", "goal": "g"}
        prompt, _ = prompts.build_measured(self.run, node, scope_map="- a.py (3 lines): f")
        self.assertNotIn("Map of the files in your scope", prompt)

    def test_scope_map_is_per_node_with_shared_prefix(self):
        run = {**self.run, "policy": {"shared_prefix": True}}
        node = {"id": "t1", "role": "implementer", "goal": "g", "scope": ["a.py"], "context_budget": 1200}
        scope_map = "- a.py (3 lines): f"
        self.assertNotIn(scope_map, prompts.shared_prefix(run, "worker"))
        prompt, _ = prompts.build_measured(run, node, scope_map=scope_map)
        self.assertIn(scope_map, prompt)


if __name__ == "__main__":
    unittest.main()
