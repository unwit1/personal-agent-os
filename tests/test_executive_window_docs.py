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


class TestExecutiveApplicantWorkflowDoc(unittest.TestCase):
    """The applicant-workflow contract must fix the names the other tasks build against."""

    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.doc_path = root / "docs" / "orchestrator-os" / "executive-applicant-workflow.md"
        self.content = self.doc_path.read_text(encoding="utf-8") if self.doc_path.is_file() else ""

    def test_doc_file_exists(self):
        self.assertTrue(self.doc_path.is_file(), str(self.doc_path))

    def test_gateway_signatures(self):
        for term in (
            "def open_counties(self, today",
            "def manager_for_county(self, county: str)",
            "def record_applicant_sent(self, applicant_ref: str, kind: str, to_addr: str, subject: str)",
            "def set_applicant_status(self, applicant_ref: str, status: str | None, note: str)",
            "def preview_opening_change(self, county: str, change: str",
            "def apply_opening_change(self, county: str, change: str",
            "DashboardGatewayError",
            "group_label",
            "open_count",
        ):
            with self.subTest(term=term):
                self.assertIn(term, self.content)

    def test_compose_and_send_contract(self):
        for term in (
            '"compose"',
            "outreach",
            "interview",
            "manager",
            "reply",
            "applicant_ref",
            "POST /api/send",
            '"sent": true',
            "NOT SENT:",
            "message_id",
            "only after a successful send",
            "Api.__init__(self, registry, bridge, home, *, transport=None, gateway_factory=None)",
        ):
            with self.subTest(term=term):
                self.assertIn(term, self.content)

    def test_lettered_anchors(self):
        for heading in ("## 4. (a)", "## 5. (b)", "## 6. (c)", "## 7. (d)"):
            with self.subTest(heading=heading):
                self.assertIn(heading, self.content)

    def test_downstream_module_names(self):
        for term in (
            "executive/window/transport.py",
            "county_items(groups_fn=None)",
            "actions_applicant_compose",
            "actions_applicant_decisions",
            "actions_openings",
            "`applicant.review`",
            "county_openings",
        ):
            with self.subTest(term=term):
                self.assertIn(term, self.content)

    def test_unowned_infrastructure_is_only_a_follow_up(self):
        required, _, follow_ups = self.content.partition("## 12. Follow-ups")
        self.assertTrue(follow_ups)
        for term in ("ComposeStore", "HoldStore", "/api/settings", "/api/compose", "retry-record",
                     "Registry.item(", "sent.jsonl"):
            with self.subTest(term=term):
                self.assertNotIn(term, required)

    def test_provider_reads_dashboard_once(self):
        self.assertIn("def county_groups(", self.content)
        self.assertIn("`ranked = gateway.ranked(0)` exactly once", self.content)
        self.assertIn("`gateway.match_for(ref)` exactly once", self.content)

    def test_transport_contract(self):
        for term in (
            "SendTransport",
            "SendResult",
            "SmtpImapTransport",
            "FakeTransport",
            "STARTTLS",
            "587",
            "465",
            "IMAP APPEND",
            "Sent folder",
            "keyring",
            "write-capable",
        ):
            with self.subTest(term=term):
                self.assertIn(term, self.content)

    def test_no_outlook_com_in_contract_behavior(self):
        self.assertIn("No Outlook, no COM", self.content)
        self.assertIn("email_sender", self.content)
        # The superseded Outlook design must not be specified as a transport.
        self.assertNotIn("OutlookTransport", self.content)
        self.assertNotIn("CoInitialize", self.content)

    def test_dashboard_names_and_open_questions(self):
        for term in (
            "openings.load_settings",
            "evaluate",
            "open_groups_in_range",
            "area_managers.manager_for_county",
            "OPEN QUESTION",
        ):
            with self.subTest(term=term):
                self.assertIn(term, self.content)

    def test_every_new_action_is_registered(self):
        for action_id in (
            "applicant.reach_out",
            "applicant.invite_interview",
            "applicant.email_manager",
            "applicant.decline",
            "applicant.hold",
            "county.refresh",
            "county.opening_change",
        ):
            with self.subTest(action_id=action_id):
                self.assertIn(f"`{action_id}`", self.content)
        for term in ("register_action", "executive_window.run", "county_openings", "openings_console"):
            with self.subTest(term=term):
                self.assertIn(term, self.content)

    def test_events_and_privacy(self):
        for term in ("parse_opening_event", "we closed the opening in X", "a driver quit in X",
                     "we have a new opening in X", "Confirm", "top_n", "EEO", "self-ID", "Allowlist"):
            with self.subTest(term=term):
                self.assertIn(term, self.content)


if __name__ == "__main__":
    unittest.main()
