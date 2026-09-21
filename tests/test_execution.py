from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.execution import cache_artifact, select_route


class ExecutionPolicyTests(unittest.TestCase):
    def test_deterministic_route_is_never_replaced_by_a_model(self) -> None:
        result = select_route({"preferred_execution_path": "deterministic"})
        self.assertEqual(result["route"], "deterministic")

    def test_valid_cache_precedes_an_approved_skill_and_model(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "result.json").write_text("{}", encoding="utf-8")
            result = select_route({"preferred_execution_path": "model", "cache": {"path": "result.json"}, "approved_skill": "cheap-route-first"}, root)
        self.assertEqual(result["route"], "cache")

    def test_missing_cache_falls_to_explicitly_approved_skill(self) -> None:
        result = select_route({"preferred_execution_path": "model", "cache": {"path": "missing.json"}, "approved_skill": "cheap-route-first"})
        self.assertEqual(result["route"], "skill")

    def test_model_is_last_resort_and_unsafe_cache_paths_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertIsNone(cache_artifact({"cache": {"path": "../outside.json"}}, root))
            result = select_route({"preferred_execution_path": "model", "cache": {"path": "missing.json"}}, root)
        self.assertEqual(result["route"], "model")


if __name__ == "__main__":
    unittest.main()
