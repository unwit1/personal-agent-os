import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "apply_runtime_observation",
    ROOT/"apply_runtime_observation.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

TOKEN="a"*64

def session():
    return {
        "schema_version":"skyrim-runtime-session-result-v1",
        "run_id":"run-1",
        "test_id":"smoke",
        "project_id":"fixture",
        "worker_id":"worker",
        "build_id":"build-1",
        "session_token":TOKEN,
        "status":"needs-review",
        "prepared_at":"2026-09-25T12:00:00+00:00",
        "started_at":"2026-09-25T12:01:00+00:00",
        "finished_at":"2026-09-25T12:02:00+00:00",
        "profile":{
            "template_dir":"C:/template",
            "disposable_dir":"C:/disposable",
            "profile_name":"AgentOS-smoke-run-1",
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
        "steps":[{
            "id":"launch",
            "status":"needs-review",
            "issues":["pending observer"],
        }],
        "assertions":[{
            "id":"alive",
            "status":"needs-review",
            "severity":"BLOCKER",
            "expected":True,
            "observed":None,
            "issues":["pending observer"],
        }],
        "evidence":{
            "session_dir":"C:/evidence/run-1",
            "artifacts":[],
            "log_delta":[],
            "crash_delta":[],
            "screenshots":[],
            "frame_traces":[],
        },
        "cleanup":{
            "attempted":True,
            "status":"passed",
            "issues":[],
        },
        "gates":[
            {"gate":"G19","status":"needs-review","evidence":[],"issues":[]},
            {"gate":"G20","status":"needs-review","evidence":[],"issues":[]},
            {"gate":"G21","status":"needs-review","evidence":[],"issues":[]},
            {"gate":"G26","status":"needs-review","evidence":[],"issues":[]},
        ],
        "issues":[],
    }

def observation(*,token=TOKEN,captured="2026-09-25T12:01:30+00:00",
                assertion_status="pass",include_assertion=True):
    assertions=[]
    if include_assertion:
        assertions=[{
            "id":"alive",
            "status":assertion_status,
            "observed":assertion_status=="pass",
            "issues":[],
            "evidence":["observer://health/alive"],
        }]
    return {
        "schema_version":"skyrim-runtime-observation-v1",
        "run_id":"run-1",
        "session_token":token,
        "observer_id":"fixture-observer",
        "observer_version":"1.0",
        "transport":"fixture",
        "captured_at":captured,
        "steps":[{
            "id":"launch",
            "status":"passed",
            "issues":[],
            "evidence":["observer://step/launch"],
        }],
        "assertions":assertions,
        "gates":[
            {
                "gate":"G19",
                "status":"pass",
                "evidence":["observer://logs/clean"],
                "issues":[],
            },
            {
                "gate":"G20",
                "status":"not-applicable",
                "evidence":[],
                "issues":[],
            },
            {
                "gate":"G21",
                "status":"not-applicable",
                "evidence":[],
                "issues":[],
            },
        ],
        "artifacts":[],
        "issues":[],
    }

class ApplyRuntimeObservationTests(unittest.TestCase):
    def test_fresh_complete_observation_can_prove_session(self):
        merged=MOD.merge_observation(session(),observation())
        self.assertEqual(merged["status"],"passed")
        gates={x["gate"]:x for x in merged["gates"]}
        self.assertEqual(gates["G26"]["status"],"pass")
        self.assertIn("alive: pass",gates["G26"]["evidence"])
        self.assertEqual(merged["assertions"][0]["observed"],True)

    def test_stale_session_token_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"session_token"):
            MOD.merge_observation(
                session(),
                observation(token="b"*64),
            )

    def test_observation_before_session_start_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"predates session start"):
            MOD.merge_observation(
                session(),
                observation(captured="2026-09-25T12:00:30+00:00"),
            )

    def test_missing_assertion_coverage_stays_needs_review(self):
        merged=MOD.merge_observation(
            session(),
            observation(include_assertion=False),
        )
        self.assertEqual(merged["status"],"needs-review")
        gates={x["gate"]:x for x in merged["gates"]}
        self.assertEqual(gates["G26"]["status"],"needs-review")

    def test_blocking_assertion_failure_fails_g26_and_session(self):
        merged=MOD.merge_observation(
            session(),
            observation(assertion_status="fail"),
        )
        self.assertEqual(merged["status"],"failed")
        gates={x["gate"]:x for x in merged["gates"]}
        self.assertEqual(gates["G26"]["status"],"fail")

    def test_nonzero_launch_cannot_be_upgraded_by_passing_observer(self):
        value=session()
        value["launch"]["exit_code"]=7
        merged=MOD.merge_observation(value,observation())
        self.assertEqual(merged["status"],"failed")

    def test_observer_cannot_directly_set_g26(self):
        value=observation()
        value["gates"].append({
            "gate":"G26",
            "status":"pass",
            "evidence":["self-declared"],
            "issues":[],
        })
        with self.assertRaisesRegex(ValueError,"runtime observation failed schema"):
            MOD.merge_observation(session(),value)

    def test_screenshot_artifact_is_promoted_to_session_evidence(self):
        value=observation()
        value["artifacts"].append({
            "kind":"screenshot",
            "path":"Data/SKSE/Plugins/devbench/captures/checkpoint.png",
            "sha256":None,
            "provider":"d3d11",
            "inconclusive":False,
            "ssim":0.99,
            "threshold":0.98,
            "passed":True,
        })
        merged=MOD.merge_observation(session(),value)
        self.assertIn(
            "Data/SKSE/Plugins/devbench/captures/checkpoint.png",
            merged["evidence"]["screenshots"],
        )
        self.assertTrue(any(
            row.get("kind")=="screenshot"
            for row in merged["evidence"]["artifacts"]
        ))


if __name__=="__main__":
    unittest.main()
