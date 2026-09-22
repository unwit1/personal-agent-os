import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import candidates, changes, improvements  # noqa: E402
from agent_os.normalization import normalise_text  # noqa: E402


class NormalizationTests(unittest.TestCase):
    def test_synthetic_punctuation_and_case_normalize_to_stable_tokens(self) -> None:
        self.assertEqual(normalise_text("  Alpha, BETA-2!  "), "alpha beta 2")
        self.assertEqual(normalise_text("Alpha/Beta 2"), normalise_text("alpha beta 2"))

    def test_empty_or_non_token_text_is_deterministic(self) -> None:
        self.assertEqual(normalise_text("... ---"), "")
        self.assertEqual(normalise_text("Fixture 17"), "fixture 17")

    def test_existing_fingerprint_and_dedupe_callers_keep_equivalent_identity(self) -> None:
        self.assertEqual(
            candidates._fingerprint("fixture", "lesson_candidate", "Alpha/Beta 2"),
            candidates._fingerprint("fixture", "lesson_candidate", "alpha beta 2"),
        )
        self.assertEqual(
            changes._fingerprint("fixture", "bug", "Alpha/Beta 2", "Same request", [], []),
            changes._fingerprint("fixture", "bug", "alpha beta 2", "Same request", [], []),
        )
        self.assertEqual(
            improvements._dedupe_key("fixture", "bug", None, "Alpha/Beta 2", "Same observation", None),
            improvements._dedupe_key("fixture", "bug", None, "alpha beta 2", "Same observation", None),
        )


if __name__ == "__main__":
    unittest.main()
