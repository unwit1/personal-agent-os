"""Tests for compact project resumption packets."""

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.executive.resumption import PACKET_SCHEMA, resumption_packet


class TestResumptionPacket(unittest.TestCase):
    def test_full_state_has_packet_fields(self):
        packet = resumption_packet({
            'project': 'x', 'status': 'active', 'goal': 'Ship it',
            'current_state': 'Implementation underway', 'next_action': 'Write tests',
            'blockers': ['B'], 'waiting_on': ['W'], 'decisions_needed': ['D'],
            'updated_at': '2026-10-05',
        }, today=date(2026, 10, 6))
        self.assertEqual(packet['schema'], PACKET_SCHEMA)
        self.assertEqual(packet['project'], 'x')
        self.assertEqual(packet['status'], 'active')
        self.assertEqual(packet['goal'], 'Ship it')
        self.assertEqual(packet['where_you_left_off'], 'Implementation underway')
        self.assertEqual(packet['next_action'], 'Write tests')
        self.assertEqual(packet['next_action_source'], 'next_action')
        self.assertEqual(packet['open_loops'], {'blockers': ['B'], 'waiting_on': ['W'], 'decisions_needed': ['D']})
        self.assertEqual(packet['age_days'], 1)
        self.assertEqual(packet['flags'], [])
        self.assertFalse(packet['truncated'])

    def test_vague_action_uses_suggestion(self):
        packet = resumption_packet({
            'project': 'x', 'next_action': 'continue',
            'current_priorities': ['Finish parser'],
        }, today=date(2026, 10, 6))
        self.assertEqual(packet['next_action'], 'Finish parser')
        self.assertEqual(packet['next_action_source'], 'suggested')

    def test_long_current_state_is_truncated(self):
        packet = resumption_packet({'project': 'x', 'current_state': 'abcdef'}, today=date(2026, 10, 6), max_chars=4)
        self.assertEqual(packet['where_you_left_off'], 'abc…')
        self.assertTrue(packet['truncated'])

    def test_open_loops_are_capped(self):
        packet = resumption_packet({
            'project': 'x', 'blockers': ['a', 'b'], 'waiting_on': ['c', 'd'],
            'decisions_needed': ['e', 'f'],
        }, today=date(2026, 10, 6), max_items=1)
        self.assertEqual(packet['open_loops'], {'blockers': ['a'], 'waiting_on': ['c'], 'decisions_needed': ['e']})
        self.assertTrue(packet['truncated'])

    def test_minimal_state_and_non_dict(self):
        packet = resumption_packet({'project': 'x'}, today=date(2026, 10, 6))
        self.assertEqual(packet['project'], 'x')
        self.assertIn('no_next_action', packet['flags'])
        with self.assertRaises(TypeError):
            resumption_packet(None, today=date(2026, 10, 6))


if __name__ == '__main__':
    unittest.main()
