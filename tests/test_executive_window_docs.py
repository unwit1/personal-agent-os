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
        self.assertTrue(
            self.doc_path.exists(),
            f"Missing {self.doc_path.relative_to(Path.cwd())}"
        )

    def test_doc_content(self):
        """The document must cover the required topics."""
        if not self.doc_path.exists():
            self.skipTest("executive-window.md does not exist")

        content = self.doc_path.read_text()
        required_terms = {
            "register_provider": "provider registration pattern",
            "register_action": "action registration pattern",
            "executive_window.run": "MCP tool for actions",
            "Confirm": "confirmation requirement for consequential actions",
            "audit.jsonl": "audit log file",
            "127.0.0.1": "loopback binding address",
            "claude -p": "Claude CLI invocation for headless mode",
        }

        missing = []
        for term, context in required_terms.items():
            if term not in content:
                missing.append(f"{term} ({context})")

        self.assertEqual(
            [],
            missing,
            f"Missing required terms in executive-window.md: {'; '.join(missing)}"
        )

    def test_doc_mentions_provider_handler(self):
        """Document should explain that providers return items locally."""
        if not self.doc_path.exists():
            self.skipTest("executive-window.md does not exist")

        content = self.doc_path.read_text()
        self.assertIn(
            "Providers are called each time the window refreshes",
            content,
            "Doc should explain when providers are called"
        )

    def test_doc_mentions_action_handler(self):
        """Document should explain how actions are exposed to the model."""
        if not self.doc_path.exists():
            self.skipTest("executive-window.md does not exist")

        content = self.doc_path.read_text()
        self.assertIn(
            "Appears as a button option",
            content,
            "Doc should explain that actions appear as UI buttons"
        )
        self.assertIn(
            "MCP tool",
            content,
            "Doc should explain that actions are MCP tools"
        )

    def test_doc_explains_consequential_flow(self):
        """Document must explain the preview -> Confirm -> execute flow."""
        if not self.doc_path.exists():
            self.skipTest("executive-window.md does not exist")

        content = self.doc_path.read_text()
        self.assertIn(
            "preview",
            content,
            "Doc should explain preview-mode execution"
        )
        self.assertIn(
            "PendingStore",
            content,
            "Doc should mention where previews are stored"
        )

    def test_doc_covers_privacy(self):
        """Document must cover applicant data privacy rules."""
        if not self.doc_path.exists():
            self.skipTest("executive-window.md does not exist")

        content = self.doc_path.read_text()
        self.assertIn(
            "_VIEW_FIELDS",
            content,
            "Doc should reference the applicant allowlist"
        )
        self.assertIn(
            "Forbidden",
            content,
            "Doc should list forbidden applicant fields"
        )

    def test_doc_covers_launch_methods(self):
        """Document should explain how to launch the window."""
        if not self.doc_path.exists():
            self.skipTest("executive-window.md does not exist")

        content = self.doc_path.read_text()
        self.assertIn(
            "agent.py executive window",
            content,
            "Doc should mention the CLI command to launch"
        )
        self.assertIn(
            "Edge",
            content,
            "Doc should mention the browser/app launcher"
        )

    def test_doc_covers_session_token(self):
        """Document should explain session token management."""
        if not self.doc_path.exists():
            self.skipTest("executive-window.md does not exist")

        content = self.doc_path.read_text()
        self.assertIn(
            "session",
            content,
            "Doc should mention session management"
        )

    def test_doc_mentions_email_send_limitation(self):
        """Document should note that email.send saves a draft, not sending."""
        if not self.doc_path.exists():
            self.skipTest("executive-window.md does not exist")

        content = self.doc_path.read_text()
        self.assertIn(
            "email.send",
            content,
            "Doc should mention email.send"
        )
        self.assertIn(
            "draft",
            content,
            "Doc should mention that email.send saves drafts"
        )


if __name__ == "__main__":
    unittest.main()
