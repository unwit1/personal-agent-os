import tempfile
import unittest
from pathlib import Path

from agent_os.orchestrator import engine as engine_mod
from agent_os.orchestrator.prompts import build
from agent_os.orchestrator.store import RUN_SCHEMA, RunStore
from agent_os.storage import write_json


def _finding(fid: str, severity: str, disposition: str = "open", round_: int = 1) -> dict:
    return {"id": fid, "severity": severity, "path": "docs/x.md", "summary": f"problem {fid}", "disposition": disposition, "round": round_}


class ControlRaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.store = RunStore(self.tmp / "home")
        record = {"schema": RUN_SCHEMA, "run_id": "run-x", "state": "RUNNING", "nodes": {},
                  "control": {"started": True, "paused": False, "stop_requested": False}, "operator_messages": []}
        path = self.store.state_path("run-x")
        path.parent.mkdir(parents=True, exist_ok=True)
        write_json(path, record)

    def test_driver_save_keeps_a_pause_sent_during_its_tick(self) -> None:
        driver = self.store.load("run-x")  # the driver's tick starts
        operator = self.store.load("run-x")  # the GUI/CLI pauses meanwhile
        operator["control"]["paused"] = True
        operator.setdefault("operator_messages", []).append({"at": "t", "text": "hold on"})
        engine_mod._operator_changed(operator)
        self.store.save(operator)
        driver["state"] = "REVIEWING"  # the driver's own progress
        self.store.save(driver)  # used to overwrite the pause
        final = self.store.load("run-x")
        self.assertTrue(final["control"]["paused"])
        self.assertEqual(final["operator_messages"][-1]["text"], "hold on")
        self.assertEqual(final["state"], "REVIEWING")

    def test_the_driver_own_control_changes_still_save(self) -> None:
        driver = self.store.load("run-x")
        driver["control"]["stop_requested"] = True
        self.store.save(driver)
        self.assertTrue(self.store.load("run-x")["control"]["stop_requested"])
        self.assertFalse(self.store.refresh_control(self.store.load("run-x")))


class RetryContextTests(unittest.TestCase):
    def test_retry_after_rejected_review_names_the_open_findings(self) -> None:
        node = {"role": "implementer", "failures": [{"kind": "cancelled", "detail": "stopped by user"}], "decisions": [],
                "review": {"findings": [_finding("R3-1", "medium"), _finding("R3-2", "low"), _finding("R1-1", "medium", "fixed")]}}
        text = engine_mod._prior_attempts(node, ["critical", "high", "medium"])
        self.assertIn("[R3-1]", text)
        self.assertNotIn("[R3-2]", text)  # not material
        self.assertNotIn("[R1-1]", text)  # already fixed
        self.assertIn("Do not report already_done", text)

    def test_no_findings_no_extra_context(self) -> None:
        self.assertEqual(engine_mod._prior_attempts({"role": "implementer", "failures": [], "decisions": [], "review": {"findings": []}}), "")

    def test_reviewer_is_shown_findings_left_open(self) -> None:
        run = {"run_id": "r", "goal": "g", "nodes": {}, "policy": {}}
        node = {"id": "n.review4", "role": "reviewer", "goal": "review", "subject": "n", "scope": [], "validators": []}
        text = build(run, node, diff="+x", findings=[_finding("R3-1", "medium")])
        self.assertIn("Earlier review rounds left these findings unresolved", text)
        self.assertIn("[R3-1]", text)


class RunHistoryTests(unittest.TestCase):
    def test_note_names_the_store_and_is_read_only(self) -> None:
        text = engine_mod._run_history_note(Path("/x/home"))
        self.assertIn(str(Path("/x/home") / "runs"), text)
        self.assertIn("AGENT_OS_ORCHESTRATOR_HOME", text)
        self.assertIn("never write there", text)

    def test_policy_is_off_by_default_and_boolean(self) -> None:
        from agent_os.orchestrator.model import PolicyError, merge_policy

        self.assertFalse(merge_policy({})["share_run_history"])
        self.assertTrue(merge_policy({"share_run_history": True})["share_run_history"])
        with self.assertRaises(PolicyError):
            merge_policy({"share_run_history": "yes"})



class ReadOnlyUsageReportTests(unittest.TestCase):
    def test_report_survives_an_unwritable_store(self) -> None:
        from unittest import mock

        from agent_os.orchestrator import usage_report

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(Path, "write_text", side_effect=PermissionError("denied")):
            result = usage_report.report(home=Path(tmp))
        self.assertIsNone(result["file"])
        self.assertIn("PermissionError", result["file_error"])


if __name__ == "__main__":
    unittest.main()
