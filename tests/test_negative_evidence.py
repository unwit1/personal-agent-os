"""MIE-0006: negative evidence is append-only (supersede, never erase)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_os.orchestrator import control_plane  # noqa: E402
from agent_os.orchestrator.validators import run_all  # noqa: E402

FAIL = "projects/personal-agent-os/orchestrator-os/records/failures/FAIL-9001.json"
EVR = "projects/personal-agent-os/orchestrator-os/records/evaluations/EVR-9001.json"
EVR_OK = "projects/personal-agent-os/orchestrator-os/records/evaluations/EVR-9002.json"
BASE_FAIL = {"id": "FAIL-9001", "type": "FAIL", "status": "open", "summary": "Worker crashed.", "links": [{"rel": "relates_to", "ref": "x"}], "recurrence": 1, "updated_at": "t0"}


class NegativeEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.git("init", "-q")
        self.write(FAIL, BASE_FAIL)
        self.write(EVR, {"id": "EVR-9001", "type": "EVR", "outcome": "rejected", "summary": "Candidate regressed."})
        self.write(EVR_OK, {"id": "EVR-9002", "type": "EVR", "outcome": "improved", "summary": "Better."})
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "base")
        self.base = self.git("rev-parse", "HEAD").strip()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def git(self, *args: str) -> str:
        return subprocess.run(["git", "-c", "user.name=f", "-c", "user.email=f@x", *args], cwd=self.repo, check=True, capture_output=True, text=True).stdout

    def write(self, path: str, data: dict) -> None:
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data), encoding="utf-8")

    def problems(self, paths: list[str], allowed=()) -> list[str]:
        return control_plane.negative_evidence_changes(self.repo, self.base, paths, allowed)

    def test_appending_and_status_changes_are_allowed(self) -> None:
        self.write(FAIL, {**BASE_FAIL, "status": "resolved", "updated_at": "t1", "summary": BASE_FAIL["summary"] + " CORRECTION: root cause found.",
                          "links": BASE_FAIL["links"] + [{"rel": "evidence_for", "ref": "DEC-1"}], "new_field": 1})
        self.assertEqual(self.problems([FAIL]), [])

    def test_rewrites_removals_and_deletions_are_rejected(self) -> None:
        cases = {
            "rewritten": {**BASE_FAIL, "summary": "Nothing happened."},
            "removed": {key: value for key, value in BASE_FAIL.items() if key != "recurrence"},
            "lost": {**BASE_FAIL, "links": []},
            "decreased": {**BASE_FAIL, "recurrence": 0},
            "summary_type": {**BASE_FAIL, "summary": 5},
        }
        for label, data in cases.items():
            with self.subTest(label):
                self.write(FAIL, data)
                self.assertTrue(self.problems([FAIL]), label)
        (self.repo / FAIL).unlink()
        self.assertTrue(any("deleted" in item for item in self.problems([FAIL])))

    def test_negative_outcomes_are_protected_positive_ones_are_not(self) -> None:
        self.write(EVR, {"id": "EVR-9001", "type": "EVR", "outcome": "improved", "summary": "Actually fine."})
        self.write(EVR_OK, {"id": "EVR-9002", "type": "EVR", "outcome": "improved", "summary": "Rewritten freely."})
        found = self.problems([EVR, EVR_OK])
        self.assertTrue(any("EVR-9001" in item for item in found))
        self.assertFalse(any("EVR-9002" in item for item in found))

    def test_recurrence_may_grow(self) -> None:
        self.write(FAIL, {**BASE_FAIL, "recurrence": 3})
        self.assertEqual(self.problems([FAIL]), [])

    def test_new_records_and_operator_grants(self) -> None:
        self.write("projects/personal-agent-os/orchestrator-os/records/failures/FAIL-9002.json", {"id": "FAIL-9002"})
        self.assertEqual(self.problems(["projects/personal-agent-os/orchestrator-os/records/failures/FAIL-9002.json"]), [])
        self.write(FAIL, {**BASE_FAIL, "summary": "Rewritten."})
        self.assertEqual(self.problems([FAIL], allowed=[FAIL]), [])

    def test_validator_step_reports_it(self) -> None:
        (self.repo / FAIL).unlink()
        result = run_all([], self.repo, changed=[FAIL], scope=["projects"], control_plane={"allowed": [], "base_commit": self.base})
        self.assertFalse(result["passed"])
        self.assertIn("negative-evidence", [item["name"] for item in result["evidence"]])

    def test_repository_history_complies(self) -> None:
        """Dogfood: the real FAIL-0001 correction (appended text, status change)
        satisfies the rule against its original commit."""
        path = "projects/personal-agent-os/orchestrator-os/records/failures/FAIL-0001.json"
        first = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", path], cwd=ROOT, capture_output=True, text=True).stdout.split()
        if not first:
            self.skipTest("FAIL-0001 not in history")
        self.assertEqual(control_plane.negative_evidence_changes(ROOT, first[-1], [path]), [])


if __name__ == "__main__":
    unittest.main()
