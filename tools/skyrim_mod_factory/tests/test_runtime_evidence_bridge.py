import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "execute_build_dag",
    ROOT/"execute_build_dag.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

TOKEN="a"*64

def session(*,test_id="smoke",status="passed",g26="pass"):
    return {
        "schema_version":"skyrim-runtime-session-result-v1",
        "run_id":"run-"+test_id,
        "test_id":test_id,
        "project_id":"fixture",
        "worker_id":"worker",
        "build_id":"build-1",
        "session_token":TOKEN,
        "status":status,
        "prepared_at":"2026-09-25T12:00:00+00:00",
        "started_at":"2026-09-25T12:01:00+00:00",
        "finished_at":"2026-09-25T12:02:00+00:00",
        "profile":{
            "template_dir":"C:/template",
            "disposable_dir":"C:/disposable",
            "profile_name":"fixture",
            "before_manifest":[],
            "after_manifest":[],
            "restored":True,
            "fresh_copy":True,
            "retained":False,
        },
        "fixture":None,
        "launch":{
            "command":["ModOrganizer.exe"],
            "attempted":True,
            "exit_code":0,
            "timed_out":False,
            "stdout_path":"stdout.log",
            "stderr_path":"stderr.log",
        },
        "steps":[{"id":"ready","status":"passed","issues":[]}],
        "assertions":[{
            "id":"alive",
            "status":"pass" if g26=="pass" else "fail",
            "severity":"BLOCKER",
            "expected":True,
            "observed":g26=="pass",
            "issues":[],
        }],
        "evidence":{
            "session_dir":"C:/evidence",
            "artifacts":[],
            "log_delta":[],
            "crash_delta":[],
            "screenshots":[],
            "frame_traces":[],
        },
        "cleanup":{"attempted":True,"status":"passed","issues":[]},
        "gates":[
            {"gate":"G19","status":"pass","evidence":["clean"],"issues":[]},
            {"gate":"G20","status":"not-applicable","evidence":[],"issues":[]},
            {"gate":"G21","status":"not-applicable","evidence":[],"issues":[]},
            {
                "gate":"G26",
                "status":g26,
                "evidence":["alive"],
                "issues":[] if g26=="pass" else ["alive failed"],
            },
        ],
        "issues":[],
    }

REGISTRY={
    "gates":[
        {"gate":"G19","severity":"BLOCKER"},
        {"gate":"G20","severity":"ERROR"},
        {"gate":"G21","severity":"BLOCKER"},
        {"gate":"G26","severity":"BLOCKER"},
    ]
}

class RuntimeEvidenceBridgeTests(unittest.TestCase):
    def test_runtime_session_summary_is_build_report_compatible(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"runtime.json"
            path.write_text(json.dumps(session()),encoding="utf-8")
            summary=MOD.runtime_session_summary(path)
            self.assertEqual(summary["status"],"pass")
            self.assertEqual(summary["assertions_total"],1)
            self.assertEqual(summary["assertions_passed"],1)
            self.assertEqual(summary["assertions_failed"],0)
            self.assertEqual(summary["adapter"],"mo2-devbench-runtime")

    def test_runtime_gate_failure_dominates_later_pass(self):
        fail_summary={
            **MOD.runtime_session_summary_from_value_for_test(session(
                test_id="first",g26="fail",status="failed"
            ))
        } if hasattr(MOD,"runtime_session_summary_from_value_for_test") else None
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            first=root/"first.json"
            second=root/"second.json"
            first.write_text(json.dumps(session(
                test_id="first",g26="fail",status="failed"
            )),encoding="utf-8")
            second.write_text(json.dumps(session(
                test_id="second",g26="pass",status="passed"
            )),encoding="utf-8")
            rows=MOD.combine_runtime_gate_rows(
                [
                    MOD.runtime_session_summary(first),
                    MOD.runtime_session_summary(second),
                ],
                REGISTRY,
            )
            gates={x["gate"]:x for x in rows}
            self.assertEqual(gates["G26"]["status"],"fail")
            self.assertIn("first: alive failed",gates["G26"]["issues"])

    def test_needs_review_runtime_gate_maps_to_build_warning(self):
        value=session(status="needs-review")
        value["gates"][0]={
            "gate":"G19",
            "status":"needs-review",
            "evidence":[],
            "issues":["coverage incomplete"],
        }
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"runtime.json"
            path.write_text(json.dumps(value),encoding="utf-8")
            rows=MOD.combine_runtime_gate_rows(
                [MOD.runtime_session_summary(path)],
                REGISTRY,
            )
            gates={x["gate"]:x for x in rows}
            self.assertEqual(gates["G19"]["status"],"warning")
            self.assertIn("smoke: coverage incomplete",gates["G19"]["issues"])

    def test_collect_runtime_report_evidence_reads_step_summaries(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"runtime.json"
            path.write_text(json.dumps(session()),encoding="utf-8")
            summary=MOD.runtime_session_summary(path)
            tests,gates=MOD.collect_runtime_report_evidence(
                [{
                    "id":"runtime.smoke",
                    "status":"passed",
                    "evidence":{"runtime_sessions":[summary]},
                }],
                REGISTRY,
            )
            self.assertEqual(tests[0]["test_id"],"smoke")
            self.assertEqual(tests[0]["status"],"pass")
            self.assertEqual(
                {x["gate"]:x["status"] for x in gates}["G26"],
                "pass",
            )

if __name__=="__main__":
    unittest.main()
