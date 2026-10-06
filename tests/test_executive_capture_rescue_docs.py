"""Tests for executive capture and rescue documentation."""

from __future__ import annotations

import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from agent_os.executive.resumption import PACKET_SCHEMA
from agent_os.mcp_server import CAPTURE_TOOL_SCHEMAS

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
        self.assertIn(PACKET_SCHEMA, content)
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

    def test_doc_mentions_project_state_knowledge_gaps(self):
        content = EXEC_CAPTURE_RESCUE_DOC.read_text(encoding="utf-8")
        section = content.split("## Knowledge gaps from project state", 1)[1].split("\n## ", 1)[0]
        for term in ("executive project-gaps", "project-gap:<project>:<field>", "--enqueue"):
            with self.subTest(term=term):
                self.assertIn(term, section)

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

    def test_doc_mentions_cli_gap_answer_flow(self):
        content = EXEC_CAPTURE_RESCUE_DOC.read_text(encoding="utf-8")
        self.assertIn("gap-answer", content)
        self.assertIn("--confirm", content)
        self.assertNotIn("Staging knowledge-gap answers directly from the CLI", content)

    def test_doc_mentions_candidate_review_window_flow(self):
        content = EXEC_CAPTURE_RESCUE_DOC.read_text(encoding="utf-8")
        for term in ("memory_candidates", "memory_candidate", "candidate.accept", "candidate.reject", "curate_candidates"):
            with self.subTest(term=term):
                self.assertIn(term, content)

    def test_doc_mcp_tools_match_capture_tool_schemas(self):
        content = EXEC_CAPTURE_RESCUE_DOC.read_text(encoding="utf-8")
        tool_names = (
            "executive_capture.brain_dump",
            "executive_capture.gaps",
            "executive_capture.rescue",
            "executive_capture.resume",
            "executive_capture.brain_dump_capture",
            "executive_capture.gaps_enqueue",
        )
        for tool_name in tool_names:
            with self.subTest(tool_name=tool_name):
                self.assertIn(tool_name, content)

        mentioned_tools = {
            name for name in CAPTURE_TOOL_SCHEMAS if name in content
        }
        self.assertEqual(mentioned_tools, set(tool_names))

    def test_doc_mentions_preview_only_mcp_write_tools(self):
        content = EXEC_CAPTURE_RESCUE_DOC.read_text(encoding="utf-8")
        for term in (
            "executive_capture.brain_dump_capture",
            "executive_capture.gaps_enqueue",
            "brain_dump.capture",
            "knowledge_gap.enqueue",
            "Confirm",
        ):
            with self.subTest(term=term):
                self.assertIn(term, content)


if __name__ == "__main__":
    unittest.main()
