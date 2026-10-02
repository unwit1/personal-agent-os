import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import unittest
from agent_os.orchestrator.model import PolicyError, merge_policy


class SharedPrefixPolicyTest(unittest.TestCase):
    def test_shared_prefix_defaults_to_false(self) -> None:
        """merge_policy() with no overrides should have shared_prefix as False."""
        policy = merge_policy()
        self.assertIs(policy["shared_prefix"], False)

    def test_shared_prefix_accepts_true(self) -> None:
        """merge_policy({'shared_prefix': True}) should be accepted."""
        policy = merge_policy({"shared_prefix": True})
        self.assertIs(policy["shared_prefix"], True)

    def test_shared_prefix_rejects_string(self) -> None:
        """merge_policy({'shared_prefix': 'yes'}) should raise PolicyError."""
        with self.assertRaises(PolicyError):
            merge_policy({"shared_prefix": "yes"})


if __name__ == "__main__":
    unittest.main()
