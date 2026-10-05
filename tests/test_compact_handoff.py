from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.compiler import _compact_handoff


class CompactHandoffTests(unittest.TestCase):
    def test_none_and_empty_mapping_return_none(self) -> None:
        self.assertIsNone(_compact_handoff(None))
        self.assertIsNone(_compact_handoff({}))

    def test_non_whitelisted_keys_are_dropped(self) -> None:
        self.assertEqual(
            _compact_handoff({"transcript_excerpt": "large", "notes": "extra"}),
            {},
        )

    def test_remaining_strings_are_normalized_and_deduplicated(self) -> None:
        self.assertEqual(
            _compact_handoff({"remaining": ["  do   x ", "do x", "", None, "do y"]}),
            {"remaining": ["do x", "do y"]},
        )

    def test_created_at_string_is_whitespace_normalized(self) -> None:
        self.assertEqual(_compact_handoff({"created_at": "  today   at noon "}), {"created_at": "today at noon"})

    def test_empty_values_are_omitted(self) -> None:
        self.assertEqual(_compact_handoff({"completed": [], "decisions": "   "}), {})

    def test_dict_list_items_are_deduplicated_and_preserved(self) -> None:
        first = {"b": 2, "a": 1}
        duplicate = {"a": 1, "b": 2}
        other = {"a": 3}
        result = _compact_handoff({"decisions": [first, duplicate, other]})
        self.assertEqual(result, {"decisions": [first, other]})
        self.assertIs(result["decisions"][0], first)

    def test_already_compact_handoff_is_unchanged(self) -> None:
        handoff = {"created_at": "today", "completed": ["done"], "remaining": ["next"]}
        self.assertEqual(_compact_handoff(handoff), handoff)


if __name__ == "__main__":
    unittest.main()
