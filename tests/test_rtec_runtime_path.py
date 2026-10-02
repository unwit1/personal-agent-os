"""The executive reads the Dashboard database where the Dashboard keeps it."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import rtec_applicants


class RuntimePathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.project = self.tmp / "checkout"
        self.project.mkdir()
        self.home = self.tmp / "HR Automation Local"
        self.runtime = self.home / "Job Applicant Dashboard"
        self.runtime.mkdir(parents=True)
        (self.runtime / "dashboard.db").write_bytes(b"")
        patcher = mock.patch.object(rtec_applicants, "_project_root", return_value=self.project)
        patcher.start()
        self.addCleanup(patcher.stop)

    def env(self, **values: str):
        clean = {k: v for k, v in os.environ.items() if k not in {"RTEC_DASHBOARD_RUNTIME_DIR", "RTEC_HR_AUTOMATION_HOME"}}
        return mock.patch.dict(os.environ, {**clean, "RTEC_HR_AUTOMATION_HOME": str(self.home), **values}, clear=True)

    def test_runtime_folder_under_the_automation_home(self) -> None:
        with self.env():
            self.assertEqual(rtec_applicants._db_path(), self.runtime / "dashboard.db")
            self.assertEqual(rtec_applicants._health_path(), self.runtime / "Config" / "fillout_sync_health.json")

    def test_runtime_path_file_and_dot(self) -> None:
        other = self.tmp / "elsewhere"
        other.mkdir()
        (other / "dashboard.db").write_bytes(b"")
        (self.runtime / "runtime-path.txt").write_text(str(other), encoding="utf-8")
        with self.env():
            self.assertEqual(rtec_applicants._db_path(), other / "dashboard.db")
        (self.runtime / "runtime-path.txt").write_text(".", encoding="utf-8")
        with self.env():
            self.assertEqual(rtec_applicants._db_path(), self.runtime / "dashboard.db")

    def test_database_in_the_project_folder_wins(self) -> None:
        (self.project / "dashboard.db").write_bytes(b"SQLite format 3")
        with self.env():
            self.assertEqual(rtec_applicants._db_path(), self.project / "dashboard.db")

    def test_empty_project_database_is_ignored(self) -> None:
        # SQLite leaves a zero-byte file when something opens a missing
        # database; it must not hide the real runtime database.
        (self.project / "dashboard.db").write_bytes(b"")
        with self.env():
            self.assertEqual(rtec_applicants._db_path(), self.runtime / "dashboard.db")

    def test_gateway_points_the_dashboard_at_the_runtime_folder(self) -> None:
        from agent_os.executive import gateway

        with self.env(), mock.patch.object(gateway.importlib, "import_module", return_value=object()) as imp:
            gateway.LocalDashboardGateway._module("candidate_review")
            self.assertEqual(os.environ["RTEC_DASHBOARD_RUNTIME_DIR"], str(self.runtime))
            imp.assert_called_once_with("candidate_review")
        sys.path[:] = [p for p in sys.path if p != str(self.project)]

    def test_no_runtime_database_falls_back_to_the_project(self) -> None:
        (self.runtime / "dashboard.db").unlink()
        with self.env():
            self.assertEqual(rtec_applicants._db_path(), self.project / "dashboard.db")


if __name__ == "__main__":
    unittest.main()
