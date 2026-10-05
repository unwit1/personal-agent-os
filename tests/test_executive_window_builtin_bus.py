import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import unittest

from agent_os.executive.window import builtin
from agent_os.executive import event_bus


class TestExecutiveWindowBuiltinBus(unittest.TestCase):
    """Tests for event bus attachment in builtin provider and action registration."""

    def test_default_registry_has_event_bus(self):
        """Test that default_registry() attaches an EventBus instance."""
        reg = builtin.default_registry()
        self.assertIsInstance(reg.event_bus, event_bus.EventBus)

    def test_event_bus_directory_equals_default_dir(self):
        """Test that the attached EventBus uses event_bus.DEFAULT_DIR."""
        reg = builtin.default_registry()
        self.assertEqual(reg.event_bus.directory, event_bus.DEFAULT_DIR)

    def test_default_registry_idempotent_same_bus_object(self):
        """Test that calling default_registry twice returns the same registry with the same bus object."""
        reg1 = builtin.default_registry()
        bus1 = reg1.event_bus

        reg2 = builtin.default_registry()
        bus2 = reg2.event_bus

        # Should be the same registry
        self.assertIs(reg1, reg2)
        # Should be the same bus object
        self.assertIs(bus1, bus2)


if __name__ == "__main__":
    unittest.main()
