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

    def test_doc_mentions_executive_window_brain_dump_flow(self):
        content = EXEC_CAPTURE_RESCUE_DOC.read_text(encoding="utf-8")
        self.assertIn("/api/brain-dump", content)
        self.assertIn("brain_dump.stage_candidate", content)
        self.assertIn("Confirm", content)

    def test_doc_mentions_knowledge_gap_window_flow(self):
        content = EXEC_CAPTURE_RESCUE_DOC.read_text(encoding="utf-8")
        self.assertIn("knowledge_gap.answer", content)
        self.assertIn("answer_to_candidate", content)
        self.assertIn("--enqueue", content)

    def test_doc_mentions_rescue_window_view(self):
        content = EXEC_CAPTURE_RESCUE_DOC.read_text(encoding="utf-8")
        self.assertIn("/api/rescue", content)
        self.assertIn("item_id", content)
        self.assertIn("Rescue mode in the Executive window", content)

    def test_doc_mentions_resumption_packets_in_executive_window(self):
        content = EXEC_CAPTURE_RESCUE_DOC.read_text(encoding="utf-8")
        self.assertIn("Resumption packets in the Executive window", content)
        self.assertIn("project.resume", content)
        self.assertIn("actions_projects", content)

    def test_doc_mentions_cli_gap_answer_staging_limitation(self):
        content = EXEC_CAPTURE_RESCUE_DOC.read_text(encoding="utf-8")
        self.assertIn("Staging knowledge-gap answers directly from the CLI", content)


if __name__ == "__main__":
    unittest.main()
