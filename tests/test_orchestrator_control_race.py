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

    def test_driver_save_keeps_an_override_set_during_its_tick(self) -> None:
        driver = self.store.load("run-x")
        operator = self.store.load("run-x")
        operator["overrides"] = {"run": {"provider": "alpha"}, "roles": {}, "nodes": {}}
        engine_mod._operator_changed(operator)
        self.store.save(operator)
        self.store.save(driver)  # used to drop the override
        self.assertEqual(self.store.load("run-x")["overrides"]["run"], {"provider": "alpha"})

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
    def test_snapshot_copies_history_without_raw_logs_into_the_worktree(self) -> None:
        home = Path(tempfile.mkdtemp())
        worker = home / "runs" / "run-a" / "workers" / "n-1"
        worker.mkdir(parents=True)
        (home / "runs" / "run-a" / "state.json").write_text("{}", encoding="utf-8")
        (home / "runs" / "run-a" / "driver.json").write_text("{}", encoding="utf-8")
        (worker / "prompt.md").write_text("p", encoding="utf-8")
        (worker / "stdout.log").write_text("huge", encoding="utf-8")
        worktree = Path(tempfile.mkdtemp())
        snapshot = engine_mod._snapshot_run_history(home, worktree)
        self.assertEqual(snapshot, worktree / ".agent-local" / "orchestrator")
        self.assertTrue((snapshot / "runs" / "run-a" / "state.json").is_file())
        self.assertTrue((snapshot / "runs" / "run-a" / "workers" / "n-1" / "prompt.md").is_file())
        self.assertFalse((snapshot / "runs" / "run-a" / "workers" / "n-1" / "stdout.log").exists())
        self.assertFalse((snapshot / "runs" / "run-a" / "driver.json").exists(), "a copied driver.json would look like a live driver")
        engine_mod._snapshot_run_history(home, worktree)  # a second launch refreshes in place
        text = engine_mod._run_history_note(snapshot)
        self.assertIn(".agent-local/orchestrator/runs", text)
        self.assertIn(f"AGENT_OS_ORCHESTRATOR_HOME={snapshot}", text)

    def test_the_snapshot_is_git_ignored(self) -> None:
        import subprocess

        root = Path(__file__).resolve().parents[1]
        probe = subprocess.run(["git", "check-ignore", "-q", ".agent-local/orchestrator/runs/x/state.json"], cwd=root)
        self.assertEqual(probe.returncode, 0)

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



class DriverAcquireTests(unittest.TestCase):
    def test_concurrent_processes_get_exactly_one_driver(self) -> None:
        import subprocess
        import sys

        tmp = Path(tempfile.mkdtemp())
        store = RunStore(tmp / "home")
        store.run_dir("run-x").mkdir(parents=True, exist_ok=True)
        code = ("import sys,time;from pathlib import Path;from agent_os.orchestrator.store import RunStore;"
                "s=RunStore(Path(sys.argv[1]));ok=s.acquire_driver('run-x','t');print(ok,flush=True);time.sleep(3 if ok else 0)")
        procs = [subprocess.Popen([sys.executable, "-c", code, str(tmp / "home")], stdout=subprocess.PIPE, text=True) for _ in range(6)]
        results = [proc.communicate(timeout=60)[0].strip() for proc in procs]
        self.assertEqual(results.count("True"), 1, results)
        self.assertFalse((store.run_dir("run-x") / "driver.lock").exists())


if __name__ == "__main__":
    unittest.main()
