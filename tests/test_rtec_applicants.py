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
                agent_ref TEXT,
                source_key TEXT,
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
                'app-syntheticref',
                'fillout-submission:synthetic-source',
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
                    "last_transition_at": "2026-09-23T11:55:00-04:00",
                    "processed_count": 1,
                    "warning_count": 0,
                    "error_class": None,
                    "source_row_count": 20,
                    "source_modified_at": "2026-09-24T12:34:56.000Z",
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
            return_value={
                "id": "job-applicant-dashboard",
                "path": str(self.root),
                "path_source": "discovered",
            },
        )
        self.project_patch.start()
        self._old_audit_path = ra._AUDIT_PATH
        ra._AUDIT_PATH = self.root / ".agent-local" / "rtec-applicant-access.jsonl"

    def tearDown(self):
        ra._AUDIT_PATH = self._old_audit_path
        self.project_patch.stop()
        self.tmp.cleanup()

    def _audit_entries(self):
        if not ra._AUDIT_PATH.exists():
            return []
        return [
            json.loads(line)
            for line in ra._AUDIT_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_access_audit_excludes_search_text_and_applicant_pii(self):
        ra.search_applicants("Synthetic Applicant")
        entries = self._audit_entries()
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["action"], "applicant.search")
        self.assertEqual(entry["metadata"]["query_present"], True)
        self.assertEqual(entry["metadata"]["query_length"], len("Synthetic Applicant"))
        encoded = json.dumps(entry)
        self.assertNotIn("Synthetic Applicant", encoded)
        self.assertNotIn("synthetic@example.invalid", encoded)
        self.assertNotIn("private/application.pdf", encoded)
        self.assertNotIn("fillout-submission:synthetic-source", encoded)

    def test_audit_helper_drops_unapproved_metadata_keys(self):
        ra._audit_access(
            "synthetic.audit",
            applicant_ref="app-syntheticref",
            metadata={
                "found": True,
                "unsafe_name": "Synthetic Applicant",
                "unsafe_query": "private search text",
            },
        )
        entry = self._audit_entries()[0]
        self.assertEqual(entry["metadata"], {"found": True})
        encoded = json.dumps(entry)
        self.assertNotIn("Synthetic Applicant", encoded)
        self.assertNotIn("private search text", encoded)

    def test_applicant_read_fails_closed_if_audit_cannot_be_written(self):
        with patch.object(ra, "_audit_access", side_effect=RuntimeError("audit unavailable")):
            with self.assertRaisesRegex(RuntimeError, "audit unavailable"):
                ra.list_applicants()

    def test_list_is_chronological_admin_projection(self):
        result = ra.list_applicants()
        self.assertEqual(result["count"], 1)
        row = result["results"][0]
        self.assertEqual(row["name"], "Synthetic Applicant")
        self.assertNotIn("note", row)
        self.assertNotIn("flagged", row)
        self.assertNotIn("flag_reasons", row)
        self.assertNotIn("pdf_path", row)
        self.assertNotIn("applicant_key", row)
        self.assertEqual(row["agent_ref"], "app-syntheticref")
        self.assertNotIn("aa_pdf_path", row)

    def test_summary_reduces_paths_to_presence_booleans(self):
        summary = ra.get_summary("app-syntheticref")
        self.assertIsNotNone(summary)
        self.assertEqual(summary["applicant_ref"], "app-syntheticref")
        self.assertEqual(summary["status"], "Interview Requested")
        self.assertTrue(summary["documents"]["application_present"])
        self.assertTrue(summary["documents"]["resume_present"])
        self.assertTrue(summary["documents"]["restricted_compliance_form_present"])
        encoded = json.dumps(summary)
        self.assertNotIn("private/application.pdf", encoded)
        self.assertNotIn("private/restricted-aa.pdf", encoded)
        self.assertNotIn("PRIVATE NOTE", encoded)
        self.assertNotIn("PRIVATE SCREENING", encoded)

    def test_document_metadata_hides_paths_and_restricted_details(self):
        # Synthetic files live under a fake configured applications/AAP tree.
        apps = self.root / "Applications"
        aap = self.root / "AAP"
        apps.mkdir()
        aap.mkdir()
        (apps / "application.pdf").write_bytes(b"synthetic application")
        (apps / "resume.pdf").write_bytes(b"synthetic resume")
        (aap / "restricted-aa.pdf").write_bytes(b"synthetic restricted")
        (self.root / "Config" / "paths_settings.json").write_text(
            json.dumps({
                "applications_dir": str(apps),
                "aap_forms_dir": str(aap),
            }),
            encoding="utf-8",
        )

        conn = sqlite3.connect(self.db)
        conn.execute(
            "UPDATE applicants SET pdf_path=?, resume_path=?, aa_pdf_path=? "
            "WHERE agent_ref='app-syntheticref'",
            ("application.pdf", "resume.pdf", str(aap / "restricted-aa.pdf")),
        )
        conn.commit()
        conn.close()

        result = ra.get_document_metadata("app-syntheticref")
        self.assertTrue(result["application"]["exists"])
        self.assertTrue(result["resume"]["exists"])
        self.assertEqual(result["application"]["extension"], ".pdf")
        self.assertNotIn("extension", result["restricted_compliance_form"])
        encoded = json.dumps(result)
        self.assertNotIn(str(apps), encoded)
        self.assertNotIn(str(aap), encoded)
        self.assertNotIn("restricted-aa.pdf", encoded)

    def test_timeline_uses_opaque_ref_and_metadata_only(self):
        result = ra.get_timeline("app-syntheticref")
        self.assertEqual(result["applicant_ref"], "app-syntheticref")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["events"][0]["event_type"], "submission_processed")
        encoded = json.dumps(result)
        self.assertNotIn("synthetic-key", encoded)
        self.assertNotIn("PRIVATE NOTE", encoded)

    def test_openings_reads_organization_config_only(self):
        (self.root / "Config" / "openings_settings.json").write_text(
            json.dumps({
                "transit_driver_groups": ["Pulaski", "Bell", "Pulaski"],
                "office_positions": {"Dispatcher": True, "CSR": False},
                "max_drive_minutes": 30,
                "nearby_offer_minutes": 25,
                "unexpected_private_field": "must not leak",
            }),
            encoding="utf-8",
        )
        result = ra.openings_status()
        self.assertEqual(result["transit_driver_groups"], ["Bell", "Pulaski"])
        self.assertEqual(result["office_positions"], {"Dispatcher": True, "CSR": False})
        self.assertEqual(result["max_drive_minutes"], 30)
        self.assertNotIn("unexpected_private_field", json.dumps(result))

    def test_openings_reads_config_from_runtime_root_when_roots_differ(self):
        with tempfile.TemporaryDirectory() as project_dir:
            (Path(project_dir) / "Config").mkdir()
            (self.root / "Config" / "openings_settings.json").write_text(
                json.dumps({"transit_driver_groups": ["Bell"]}),
                encoding="utf-8",
            )
            with patch.object(
                ra,
                "get_project",
                return_value={"id": "job-applicant-dashboard", "path": project_dir, "path_source": "discovered"},
            ), patch.dict(
                "os.environ",
                {
                    "RTEC_DASHBOARD_RUNTIME_DIR": str(self.root),
                    "RTEC_HR_AUTOMATION_HOME": str(Path(project_dir) / "no-home"),
                },
            ):
                result = ra.openings_status()
        self.assertTrue(result["configured"])
        self.assertEqual(result["transit_driver_groups"], ["Bell"])

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
        self.assertEqual(result["last_transition_at"], "2026-09-23T11:55:00-04:00")
        self.assertEqual(result["source_modified_at"], "2026-09-24T12:34:56.000Z")
        self.assertEqual(result["applicant_record_count"], 1)
        self.assertEqual(result["outbox"]["pending_count"], 1)
        encoded = json.dumps(result)
        self.assertNotIn("Synthetic Applicant", encoded)
        self.assertNotIn("synthetic@example.invalid", encoded)

    def test_event_ack_is_bookkeeping_only(self):
        before = ra.pending_events()
        self.assertEqual(before["count"], 1)
        self.assertEqual(before["results"][0]["applicant_ref"], "app-syntheticref")
        self.assertNotIn("applicant_key", before["results"][0])
        self.assertTrue(ra.acknowledge_event("evt-1")["acknowledged"])
        self.assertEqual(ra.pending_events()["count"], 0)

        conn = sqlite3.connect(self.db)
        status = conn.execute(
            "SELECT status FROM applicants WHERE applicant_key = 'synthetic-key'"
        ).fetchone()[0]
        conn.close()
        self.assertEqual(status, "Interview Requested")

    def test_applicant_reads_fail_closed_before_agent_ref_migration(self):
        conn = sqlite3.connect(self.db)
        conn.execute("ALTER TABLE applicants RENAME TO applicants_new")
        conn.execute(
            "CREATE TABLE applicants (applicant_key TEXT PRIMARY KEY, name TEXT, status TEXT)"
        )
        conn.execute(
            "INSERT INTO applicants VALUES ('filename-with-name.pdf','Synthetic','New')"
        )
        conn.execute("DROP TABLE applicants_new")
        conn.commit()
        conn.close()

        with self.assertRaisesRegex(RuntimeError, "opaque agent_ref migration"):
            ra.list_applicants()

        status = ra.sync_status()
        self.assertFalse(status["agent_ref_schema_ready"])
        self.assertEqual(status["applicant_record_count"], 1)

    def test_acknowledge_handles_legacy_db_without_outbox(self):
        conn = sqlite3.connect(self.db)
        conn.execute("DROP TABLE agent_events")
        conn.commit()
        conn.close()
        self.assertEqual(
            ra.acknowledge_event("evt-1"),
            {"acknowledged": False, "reason": "outbox_schema_unavailable"},
        )
        self.assertEqual(
            ra.pending_events(),
            {"count": 0, "results": [], "schema_ready": False},
        )

    def test_runtime_readiness_healthy_only_when_all_local_gates_pass(self):
        result = ra.readiness()
        self.assertEqual(result["status"], "healthy")
        self.assertTrue(result["ready_for_restricted_reads"])
        self.assertTrue(result["project_path_resolved"])
        self.assertTrue(result["dashboard_database_present"])
        self.assertTrue(result["agent_ref_schema_ready"])
        self.assertTrue(result["outbox_schema_ready"])
        self.assertTrue(result["audit_write_ready"])
        self.assertEqual(result["source_health"], "healthy")
        encoded = json.dumps(result)
        self.assertNotIn("Synthetic Applicant", encoded)
        self.assertNotIn("synthetic@example.invalid", encoded)

    def test_runtime_readiness_degrades_before_opaque_ref_migration(self):
        conn = sqlite3.connect(self.db)
        conn.execute("ALTER TABLE applicants RENAME TO applicants_new")
        conn.execute(
            "CREATE TABLE applicants (applicant_key TEXT PRIMARY KEY, name TEXT, status TEXT)"
        )
        conn.execute(
            "INSERT INTO applicants VALUES ('legacy-name.pdf','Synthetic','New')"
        )
        conn.execute("DROP TABLE applicants_new")
        conn.commit()
        conn.close()

        result = ra.readiness()
        self.assertEqual(result["status"], "degraded")
        self.assertFalse(result["ready_for_restricted_reads"])
        self.assertFalse(result["agent_ref_schema_ready"])
        self.assertTrue(result["outbox_schema_ready"])

    def test_runtime_readiness_unavailable_without_dashboard_database(self):
        self.db.unlink()
        result = ra.readiness()
        self.assertEqual(result["status"], "unavailable")
        self.assertFalse(result["ready_for_restricted_reads"])
        self.assertFalse(result["dashboard_database_present"])

    def test_audit_status_returns_aggregate_health_only(self):
        ra.search_applicants("Synthetic Applicant")
        ra.get_summary("app-syntheticref")
        status = ra.audit_status()
        self.assertTrue(status["present"])
        self.assertEqual(status["record_count"], 2)
        self.assertEqual(status["recent_action_counts"]["applicant.search"], 1)
        self.assertEqual(status["recent_action_counts"]["applicant.get_summary"], 1)
        encoded = json.dumps(status)
        self.assertNotIn("app-syntheticref", encoded)
        self.assertNotIn("Synthetic Applicant", encoded)
        self.assertNotIn("synthetic@example.invalid", encoded)

    def test_mcp_surface_exposes_only_admin_adapter_tools(self):
        available = methods()
        for name in (
            "applicant.list",
            "applicant.search",
            "applicant.get_summary",
            "applicant.get_status",
            "applicant.get_document_metadata",
            "applicant.get_timeline",
            "applicant.openings",
            "applicant.pending_actions",
            "applicant.sync_status",
            "applicant.events",
            "applicant.readiness",
            "applicant.audit_status",
            "applicant.event_ack",
        ):
            self.assertIn(name, TOOL_SCHEMAS)
            self.assertIn(name, available)
        self.assertEqual(
            TOOL_SCHEMAS["applicant.get_status"]["inputSchema"]["required"],
            ["applicant_ref"],
        )
        self.assertIn(
            "applicant_ref",
            TOOL_SCHEMAS["applicant.get_status"]["inputSchema"]["properties"],
        )
        self.assertNotIn("applicant.rank", TOOL_SCHEMAS)
        self.assertNotIn("applicant.recommend", TOOL_SCHEMAS)


if __name__ == "__main__":
    unittest.main()
