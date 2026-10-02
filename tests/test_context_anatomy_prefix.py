"""Test shared_prefix policy and common_prefix_tokens function (IMP-0018 Phase 1)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import context_anatomy, prompts


class CommonPrefixTokensTest(unittest.TestCase):
    def test_common_prefix_tokens_basic(self) -> None:
        """common_prefix_tokens(['abc','abd']) == tokens('ab')"""
        result = context_anatomy.common_prefix_tokens(["abc", "abd"])
        expected = context_anatomy.tokens("ab")
        self.assertEqual(result, expected)

    def test_common_prefix_tokens_empty_list(self) -> None:
        """Returns 0 for empty list."""
        result = context_anatomy.common_prefix_tokens([])
        self.assertEqual(result, 0)

    def test_common_prefix_tokens_single_item(self) -> None:
        """Returns 0 for single item."""
        result = context_anatomy.common_prefix_tokens(["abc"])
        self.assertEqual(result, 0)

    def test_common_prefix_tokens_identical(self) -> None:
        """Returns tokens of full string when all are identical."""
        result = context_anatomy.common_prefix_tokens(["hello", "hello"])
        expected = context_anatomy.tokens("hello")
        self.assertEqual(result, expected)

    def test_common_prefix_tokens_no_common_prefix(self) -> None:
        """Returns 0 when no common prefix."""
        result = context_anatomy.common_prefix_tokens(["xyz", "abc"])
        self.assertEqual(result, 0)

    def test_common_prefix_tokens_multiple(self) -> None:
        """Works with multiple strings."""
        result = context_anatomy.common_prefix_tokens(["foobar", "foobaz", "fooqux"])
        expected = context_anatomy.tokens("foob")
        self.assertEqual(result, expected)


class SharedPrefixAnalysisTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        # Create minimal repo structure
        (self.repo / ".git").mkdir(exist_ok=True)
        (self.repo / "src").mkdir(exist_ok=True)
        (self.repo / "tests").mkdir(exist_ok=True)

    def test_worker_common_prefix_with_shared_prefix_policy(self) -> None:
        """Worker common prefix with shared_prefix True > False."""
        goal = "Add feature X to the system"

        # Synthetic 3-task plan in planner format (with 'tasks' key)
        plan = {
            "status": "done",
            "summary": "Planned 3 tasks",
            "tasks": [
                {
                    "id": "task1",
                    "goal": "Implement feature X",
                    "role": "implementer",
                    "scope": ["src/feature.py"],
                },
                {
                    "id": "task2",
                    "goal": "Write tests for feature X",
                    "role": "test_author",
                    "scope": ["tests/test_feature.py"],
                },
                {
                    "id": "task3",
                    "goal": "Additional work for feature X",
                    "role": "implementer",
                    "scope": ["src/feature2.py"],
                },
            ],
        }

        # Patch _context_packet to return a fixed, deterministic packet
        with patch.object(
            prompts, "_context_packet",
            return_value=("Project context: test content\n", None)
        ):
            # Test with shared_prefix=False
            calls_without_prefix = context_anatomy.build_run(
                goal,
                plan,
                self.repo,
                policy={"shared_prefix": False, "planner_repo_map": False}
            )
            analysis_without_prefix = context_anatomy.analyze(calls_without_prefix)

            # Test with shared_prefix=True
            calls_with_prefix = context_anatomy.build_run(
                goal,
                plan,
                self.repo,
                policy={"shared_prefix": True, "planner_repo_map": False}
            )
            analysis_with_prefix = context_anatomy.analyze(calls_with_prefix)

        # Verify both have the key
        self.assertIn("worker_common_prefix_tokens", analysis_without_prefix)
        self.assertIn("worker_common_prefix_tokens", analysis_with_prefix)

        # Extract implementer and test_author worker prompts for verification
        workers_without = [c for c in calls_without_prefix if c["role"] in {"implementer", "test_author"}]
        workers_with = [c for c in calls_with_prefix if c["role"] in {"implementer", "test_author"}]

        # Compute expected common prefixes
        workers_without_prompts = [c["prompt"] for c in workers_without]
        workers_with_prompts = [c["prompt"] for c in workers_with]

        expected_without = context_anatomy.common_prefix_tokens(workers_without_prompts)
        expected_with = context_anatomy.common_prefix_tokens(workers_with_prompts)

        # Verify they match the analysis
        self.assertEqual(analysis_without_prefix["worker_common_prefix_tokens"], expected_without)
        self.assertEqual(analysis_with_prefix["worker_common_prefix_tokens"], expected_with)

        # With shared_prefix=True, the common prefix should be strictly larger
        # because the run-level prefix (goal, rules) is shared across all workers
        self.assertGreater(
            analysis_with_prefix["worker_common_prefix_tokens"],
            analysis_without_prefix["worker_common_prefix_tokens"],
            f"shared_prefix=True common prefix ({analysis_with_prefix['worker_common_prefix_tokens']}) "
            f"must be > shared_prefix=False ({analysis_without_prefix['worker_common_prefix_tokens']})"
        )


if __name__ == "__main__":
    unittest.main()
