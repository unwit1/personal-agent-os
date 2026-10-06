"""Tests for executive capture and rescue documentation."""

from __future__ import annotations

import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXEC_CAPTURE_RESCUE_DOC = PROJECT_ROOT / "docs" / "orchestrator-os" / "executive-capture-rescue.md"


class TestExecutiveCaptureRescueDocumentation(unittest.TestCase):
    """Validate required coverage in executive-capture-rescue.md."""

    def test_doc_exists(self):
        self.assertTrue(EXEC_CAPTURE_RESCUE_DOC.exists(), f"Documentation file not found: {EXEC_CAPTURE_RESCUE_DOC}")

    def test_doc_mentions_required_commands_and_flows(self):
        content = EXEC_CAPTURE_RESCUE_DOC.read_text(encoding="utf-8")
        for command in ("brain-dump", "gaps", "rescue", "resume"):
            with self.subTest(command=command):
                self.assertIn(command, content)
        self.assertIn("resumption-packet@1", content)
        self.assertIn("clarification", content)
        self.assertIn("stage_candidates", content)


if __name__ == "__main__":
    unittest.main()
