import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import socket
import tempfile
import unittest
from unittest import mock

from agent_os.orchestrator import context_anatomy, shared_prefix_compare


def _no_network(*args, **kwargs):
    raise AssertionError("network access attempted")


class SharedPrefixCompareTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.repo = self.root / "repo"
        (self.repo / "src").mkdir(parents=True)

    def run_compare(self, name):
        with mock.patch.object(socket, "socket", side_effect=_no_network):
            return shared_prefix_compare.compare(self.repo, self.root / name)

    def test_reduces_uncached_input_and_raises_cache_share(self):
        result = self.run_compare("a")
        before, after = result["before"], result["after"]
        self.assertGreater(before["eligible_calls"], 0)
        self.assertEqual(before["eligible_calls"], before["calls"])
        self.assertLess(after["worker_uncached_input_tokens"], before["worker_uncached_input_tokens"])
        self.assertLess(after["uncached_input_tokens"], before["uncached_input_tokens"])
        self.assertGreater(after["cache_read_share"], before["cache_read_share"])
        self.assertLess(result["delta"]["worker_uncached_input_tokens"], 0)
        self.assertGreater(result["delta"]["cache_read_share"], 0)
        self.assertTrue((self.root / "a" / "runs" / shared_prefix_compare.RUN_IDS["after"] / "telemetry.jsonl").is_file())

    def test_deterministic(self):
        first = self.run_compare("a")
        second = self.run_compare("b")
        self.assertEqual(first["delta"], second["delta"])
        self.assertEqual(first["before"]["total_input_tokens"], second["before"]["total_input_tokens"])
        self.assertEqual(first["after"]["cache_read_tokens"], second["after"]["cache_read_tokens"])

    def test_parity_required_sections(self):
        """Verify all required prompt sections present in both before and after variants."""
        before_calls = context_anatomy.build_run(
            shared_prefix_compare.GOAL, shared_prefix_compare.PLAN, self.repo,
            project=None, policy={"shared_prefix": False, "planner_repo_map": False}
        )
        after_calls = context_anatomy.build_run(
            shared_prefix_compare.GOAL, shared_prefix_compare.PLAN, self.repo,
            project=None, policy={"shared_prefix": True, "planner_repo_map": False}
        )
        self.assertEqual(len(before_calls), len(after_calls), "call count mismatch between variants")
        for before, after in zip(before_calls, after_calls):
            self.assertEqual(before["role"], after["role"], f"role mismatch for node {before['node']}")
            self.assertEqual(before["node"], after["node"], "node mismatch")
            before_sections = context_anatomy.sections(before["prompt"])
            after_sections = context_anatomy.sections(after["prompt"])
            self.assertEqual(set(before_sections.keys()), set(after_sections.keys()),
                           f"section mismatch for {before['role']} {before['node']}: "
                           f"before={sorted(before_sections.keys())} after={sorted(after_sections.keys())}")


if __name__ == "__main__":
    unittest.main()
