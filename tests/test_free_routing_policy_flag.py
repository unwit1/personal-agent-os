import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import unittest

from agent_os.orchestrator.model import PolicyError, merge_policy


class TestFreeRoutingPolicyFlag(unittest.TestCase):
    def test_defaults_to_false(self):
        """merge_policy() defaults free_routing_enabled to False."""
        policy = merge_policy()
        self.assertFalse(policy["free_routing_enabled"])

    def test_can_enable(self):
        """merge_policy({'free_routing_enabled': True}) gives True."""
        policy = merge_policy({"free_routing_enabled": True})
        self.assertTrue(policy["free_routing_enabled"])

    def test_rejects_invalid_value(self):
        """merge_policy({'free_routing_enabled': 'yes'}) raises PolicyError."""
        with self.assertRaises(PolicyError) as cm:
            merge_policy({"free_routing_enabled": "yes"})
        self.assertIn("free_routing_enabled", str(cm.exception))
        self.assertIn("boolean", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
