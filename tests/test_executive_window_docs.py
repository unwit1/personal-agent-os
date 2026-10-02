from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class TestExecutiveWindowDocs(unittest.TestCase):
    """Validate that executive-window.md documents the required concepts."""

    def setUp(self):
        self.doc_path = Path(__file__).resolve().parents[1] / "docs" / "orchestrator-os" / "executive-window.md"

    def test_doc_file_exists(self):
        """The executive-window.md file must exist."""
        self.assertTrue(self.doc_path.is_file(), str(self.doc_path))

    def test_doc_content(self):
        """The document must cover all required terms."""
        content = self.doc_path.read_text(encoding="utf-8")
        required_terms = [
            "register_provider",
            "register_action",
            "executive_window.run",
            "Confirm",
            "audit.jsonl",
            "127.0.0.1",
            "claude -p",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, content)


if __name__ == "__main__":
    unittest.main()
