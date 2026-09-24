from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import rtec_applicants as ra
from agent_os.mcp_server import TOOL_SCHEMAS, methods


class RTECApplicantAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "Config").mkdir()
        self.db = self.root / "dashboard.db"

        conn = sqlite3.connect(self.db)
        conn.execute(
            """
            CREATE TABLE applicants (
                applicant_key TEXT PRIMARY KEY,
                name TEXT,
                position TEXT,
                submitted TEXT,
                email TEXT,
                county TEXT,
                city TEXT,
                county_preference TEXT,
                pdf_path TEXT,
                resume_path TEXT,
                aa_pdf_path TEXT,
                status TEXT,
                note TEXT,
                flagged INTEGER,
                flag_reasons TEXT,
                denial_email_drafted_at TEXT,
                denial_email_sent_at TEXT,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            """
            INSERT INTO applicants VALUES (
                'synthetic-key',
                'Synthetic Applicant',
                'Transit Driver',
                '2026-09-23 10:00',
                'synthetic@example.invalid',
                'Pulaski',
                'Somerset',
                'Pulaski',
                'private/application.pdf',
                'private/resume.pdf',
                'private/restricted-aa.pdf',
                'Interview Requested',
                'PRIVATE NOTE MUST NOT LEAK',
                1,
                'PRIVATE SCREENING TEXT MUST NOT LEAK',
                '2026-09-23T11:00:00',
                '',
                '2026-09-23T11:01:00'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE agent_events (
                event_id TEXT PRIMARY KEY,
                applicant_key TEXT,
                event_type TEXT NOT NULL,
                source_component TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL DEFAULT '{}',
                sensitivity TEXT NOT NULL DEFAULT 'work_hr_restricted',
                acknowledged_at TEXT DEFAULT ''
            )
            """
        )
        conn.execute(
            """
            INSERT INTO agent_events VALUES (
                'evt-1', 'synthetic-key', 'submission_processed', 'test',
                '2026-09-23T10:01:00-04:00',
                '{"initial_status":"New"}', 'work_hr_restricted', ''
            )
            """
        )
        conn.commit()
        conn.close()

        (self.root / "Config" / "fillout_sync_health.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "provider": "fillout_via_google_bridge",
                    "status": "healthy",
                    "last_check_at": "2026-09-23T12:00:00-04:00",
                    "last_success_at": "2026-09-23T12:00:00-04:00",
                    "processed_count": 1,
                    "warning_count": 0,
                    "error_class": None,
                    "source_row_count": 20,
                    "header_column_count": 154,
                    "header_sha256": "a" * 64,
                    "source_config_sha256": "b" * 64,
                }
            ),
            encoding="utf-8",
        )

        self.project_patch = patch.object(
            ra,
            "get_project",
            return_value={"id": "job-applicant-dashboard", "path": str(self.root)},
        )
        self.project_patch.start()

    def tearDown(self):
        self.project_patch.stop()
        self.tmp.cleanup()

    def test_list_is_chronological_admin_projection(self):
        result = ra.list_applicants()
        self.assertEqual(result["count"], 1)
        row = result["results"][0]
        self.assertEqual(row["name"], "Synthetic Applicant")
        self.assertNotIn("note", row)
        self.assertNotIn("flagged", row)
        self.assertNotIn("flag_reasons", row)
        self.assertNotIn("pdf_path", row)
        self.assertNotIn("aa_pdf_path", row)

    def test_summary_reduces_paths_to_presence_booleans(self):
        summary = ra.get_summary("synthetic-key")
        self.assertIsNotNone(summary)
        self.assertEqual(summary["status"], "Interview Requested")
        self.assertTrue(summary["documents"]["application_present"])
        self.assertTrue(summary["documents"]["resume_present"])
        self.assertTrue(summary["documents"]["restricted_compliance_form_present"])
        encoded = json.dumps(summary)
        self.assertNotIn("private/application.pdf", encoded)
        self.assertNotIn("private/restricted-aa.pdf", encoded)
        self.assertNotIn("PRIVATE NOTE", encoded)
        self.assertNotIn("PRIVATE SCREENING", encoded)

    def test_search_does_not_rank_or_search_private_notes(self):
        visible = ra.search_applicants("Pulaski")
        self.assertEqual(visible["count"], 1)
        hidden = ra.search_applicants("PRIVATE NOTE")
        self.assertEqual(hidden["count"], 0)

    def test_pending_actions_reflects_workflow_state_only(self):
        result = ra.pending_actions()
        self.assertEqual(result["count"], 1)
        self.assertEqual(
            result["results"][0]["administrative_action"],
            "interview_request_outstanding",
        )

    def test_sync_status_contains_health_and_outbox_counts(self):
        result = ra.sync_status()
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["header_column_count"], 154)
        self.assertEqual(result["applicant_record_count"], 1)
        self.assertEqual(result["outbox"]["pending_count"], 1)
        encoded = json.dumps(result)
        self.assertNotIn("Synthetic Applicant", encoded)
        self.assertNotIn("synthetic@example.invalid", encoded)

    def test_event_ack_is_bookkeeping_only(self):
        before = ra.pending_events()
        self.assertEqual(before["count"], 1)
        self.assertTrue(ra.acknowledge_event("evt-1")["acknowledged"])
        self.assertEqual(ra.pending_events()["count"], 0)

        conn = sqlite3.connect(self.db)
        status = conn.execute(
            "SELECT status FROM applicants WHERE applicant_key = 'synthetic-key'"
        ).fetchone()[0]
        conn.close()
        self.assertEqual(status, "Interview Requested")

    def test_mcp_surface_exposes_only_admin_adapter_tools(self):
        available = methods()
        for name in (
            "applicant.list",
            "applicant.search",
            "applicant.get_summary",
            "applicant.get_status",
            "applicant.pending_actions",
            "applicant.sync_status",
            "applicant.events",
            "applicant.event_ack",
        ):
            self.assertIn(name, TOOL_SCHEMAS)
            self.assertIn(name, available)
        self.assertNotIn("applicant.rank", TOOL_SCHEMAS)
        self.assertNotIn("applicant.recommend", TOOL_SCHEMAS)


if __name__ == "__main__":
    unittest.main()
