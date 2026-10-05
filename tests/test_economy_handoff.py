from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.economy import handoff_compaction_report


class HandoffEconomyTests(unittest.TestCase):
    def test_report_measures_compaction_without_exposing_handoff_values(self) -> None:
        fixture_path = Path(__file__).resolve().parent / "fixtures" / "economy-handoffs.json"
        handoffs = json.loads(fixture_path.read_text(encoding="utf-8"))
        report = handoff_compaction_report(handoffs)
        self.assertEqual(report["handoffs"], 3)
        self.assertLess(report["compacted_tokens"], report["raw_tokens"])
        self.assertEqual(report["tokens_avoided"], report["raw_tokens"] - report["compacted_tokens"])
        self.assertIn("transcript_excerpt", report["dropped_keys"])
        self.assertNotIn("remaining", report["dropped_keys"])
        serialized_report = json.dumps(report)
        for handoff in handoffs:
            for value in handoff.values():
                self.assertNotIn(str(value), serialized_report)

    def test_empty_input_has_zero_counts_and_no_ratio(self) -> None:
        report = handoff_compaction_report([])
        self.assertEqual(report["handoffs"], 0)
        self.assertEqual(report["raw_tokens"], 0)
        self.assertEqual(report["compacted_tokens"], 0)
        self.assertEqual(report["tokens_avoided"], 0)
        self.assertIsNone(report["ratio"])
        self.assertEqual(report["dropped_keys"], [])


if __name__ == "__main__":
    unittest.main()
