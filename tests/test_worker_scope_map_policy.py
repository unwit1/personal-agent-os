import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import unittest
from agent_os.orchestrator.model import PolicyError, merge_policy


class WorkerScopeMapPolicyTest(unittest.TestCase):
    def test_worker_scope_map_defaults_to_false(self) -> None:
        self.assertIs(merge_policy()["worker_scope_map"], False)

    def test_worker_scope_map_accepts_true(self) -> None:
        self.assertIs(merge_policy({"worker_scope_map": True})["worker_scope_map"], True)

    def test_worker_scope_map_rejects_string(self) -> None:
        with self.assertRaises(PolicyError):
            merge_policy({"worker_scope_map": "yes"})


if __name__ == "__main__":
    unittest.main()
