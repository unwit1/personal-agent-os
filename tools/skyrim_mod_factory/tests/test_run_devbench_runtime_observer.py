import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "run_devbench_runtime_observer",
    ROOT/"run_devbench_runtime_observer.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

TOKEN="a"*64

def runtime_test(*,performance=False):
    assertions=[{
        "id":"player-loaded",
        "kind":"health",
        "expected":True,
        "operator":"eq",
        "severity":"BLOCKER",
        "probe":{
            "adapter":"devbench",
            "tool":"inspect",
            "arguments":{"kind":"state"},
            "json_path":"playerLoaded",
        },
    }]
    if performance:
        assertions.append({
            "id":"frame-budget",
            "kind":"performance",
            "expected":20.0,
            "operator":"lte",
            "severity":"ERROR",
            "probe":{
                "adapter":"devbench",
                "tool":"inspect",
                "arguments":{"kind":"fixture.performance"},
                "json_path":"frameMs",
            },
        })
    return {
        "schema_version":"skyrim-runtime-test-v1",
        "test_id":"smoke",
        "project_id":"fixture",
        "adapter":"devbench",
        "fixture":{"kind":"new-game","destructive_copy_only":True},
        "steps":[
            {
                "id":"load",
                "action":"load fixture save",
                "driver":{
                    "adapter":"devbench",
                    "kind":"tool",
                    "tool":"game",
                    "arguments":{"action":"load","name":"Fixture"},
                },
            },
            {
                "id":"loaded",
                "action":"wait for post load",
                "timeout_seconds":60,
                "driver":{
                    "adapter":"devbench",
                    "kind":"wait-for",
                    "event":"postLoadGame",
                },
            },
            {
                "id":"ready",
                "action":"wait until player loaded",
                "driver":{
                    "adapter":"devbench",
                    "kind":"wait-until",
                    "condition":"playerLoaded",
                    "timeout_ms":30000,
                },
            },
        ],
        "assertions":assertions,
    }

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
        "fixture":{"kind":"new-game","source":None,"destination":None,"sha256":None},
        "launch":{
            "command":["ModOrganizer.exe"],
            "attempted":True,
            "exit_code":0,
            "timed_out":False,
            "stdout_path":"stdout.log",
            "stderr_path":"stderr.log",
        },
        "steps":[
            {"id":"load","status":"needs-review","issues":[]},
            {"id":"loaded","status":"needs-review","issues":[]},
            {"id":"ready","status":"needs-review","issues":[]},
        ],
        "assertions":[
            {
                "id":"player-loaded",
                "status":"needs-review",
                "severity":"BLOCKER",
                "expected":True,
                "observed":None,
                "issues":[],
            }
        ],
        "evidence":{
            "session_dir":"C:/evidence/run-1",
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
            {"gate":"G26","status":"needs-review","evidence":[],"issues":[]},
        ],
        "issues":[],
    }

HEALTH={"ok":True,"pid":42,"port":8920,"exe":"SkyrimSE.exe","vr":False,"frame":100}

class DevBenchRuntimeObserverTests(unittest.TestCase):
    def test_compile_scenario_uses_event_and_state_waits(self):
        payload=MOD.compile_scenario(runtime_test())
        self.assertEqual(
            payload["steps"],
            [
                {"tool":"game","args":{"action":"load","name":"Fixture"}},
                {"waitFor":"postLoadGame","timeoutMs":60000},
                {"waitUntil":"playerLoaded","timeoutMs":30000},
            ],
        )

    def test_compile_rejects_untyped_or_non_devbench_steps(self):
        value=runtime_test()
        value["steps"][0].pop("driver")
        with self.assertRaisesRegex(ValueError,"no typed driver"):
            MOD.compile_scenario(value)
        value=runtime_test()
        value["steps"][0]["driver"]["adapter"]="skylink-ai"
        with self.assertRaisesRegex(ValueError,"not devbench"):
            MOD.compile_scenario(value)

    def test_operator_evaluation_is_deterministic(self):
        self.assertTrue(MOD.evaluate_operator(10,9,"gt"))
        self.assertTrue(MOD.evaluate_operator("abcdef","bcd","contains"))
        self.assertTrue(MOD.evaluate_operator("abc123",r"^abc","matches"))
        self.assertTrue(MOD.evaluate_operator(10.05,10.0,"eq",0.1))
        self.assertIsNone(MOD.evaluate_operator({},1,"gt"))

    def test_run_observer_emits_passed_steps_and_assertion(self):
        def fake_post(base,name,args,timeout_seconds=30.0):
            if name=="scenario":
                return {
                    "ok":True,
                    "results":[
                        {"index":0,"kind":"tool","ok":True},
                        {"index":1,"kind":"waitFor","satisfied":True},
                        {"index":2,"kind":"waitUntil","satisfied":True},
                    ],
                }
            if name=="inspect":
                return {"playerLoaded":True}
            raise AssertionError(name)

        with patch.object(MOD,"wait_for_health",return_value=dict(HEALTH)),              patch.object(MOD,"health",return_value=dict(HEALTH)),              patch.object(MOD,"post_tool",side_effect=fake_post):
            obs=MOD.run_observer(runtime_test(),session())

        self.assertTrue(all(x["status"]=="passed" for x in obs["steps"]))
        self.assertEqual(obs["assertions"][0]["status"],"pass")
        self.assertEqual(MOD.schema_errors(obs,MOD.OBS_SCHEMA),[])

    def test_instance_identity_change_invalidates_positive_evidence(self):
        after=dict(HEALTH)
        after["pid"]=99

        def fake_post(base,name,args,timeout_seconds=30.0):
            if name=="scenario":
                return {
                    "ok":True,
                    "results":[
                        {"index":0,"ok":True},
                        {"index":1,"satisfied":True},
                        {"index":2,"satisfied":True},
                    ],
                }
            return {"playerLoaded":True}

        with patch.object(MOD,"wait_for_health",return_value=dict(HEALTH)),              patch.object(MOD,"health",return_value=after),              patch.object(MOD,"post_tool",side_effect=fake_post):
            obs=MOD.run_observer(runtime_test(),session())

        self.assertTrue(obs["issues"])
        self.assertTrue(all(x["status"]=="needs-review" for x in obs["steps"]))
        self.assertEqual(obs["assertions"][0]["status"],"needs-review")

    def test_performance_assertion_emits_g20(self):
        value=runtime_test(performance=True)
        sess=session()
        sess["assertions"].append({
            "id":"frame-budget",
            "status":"needs-review",
            "severity":"ERROR",
            "expected":20.0,
            "observed":None,
            "issues":[],
        })
        sess["gates"][1]={
            "gate":"G20","status":"needs-review","evidence":[],"issues":[]
        }

        def fake_post(base,name,args,timeout_seconds=30.0):
            if name=="scenario":
                return {
                    "ok":True,
                    "results":[
                        {"index":0,"ok":True},
                        {"index":1,"satisfied":True},
                        {"index":2,"satisfied":True},
                    ],
                }
            if args.get("kind")=="state":
                return {"playerLoaded":True}
            return {"frameMs":16.5}

        with patch.object(MOD,"wait_for_health",return_value=dict(HEALTH)),              patch.object(MOD,"health",return_value=dict(HEALTH)),              patch.object(MOD,"post_tool",side_effect=fake_post):
            obs=MOD.run_observer(value,sess)

        gates={x["gate"]:x for x in obs["gates"]}
        self.assertEqual(gates["G20"]["status"],"pass")

    def test_assertion_probe_can_select_from_array_tool_result(self):
        assertion={
            "id":"first-item",
            "kind":"value",
            "expected":"alpha",
            "operator":"eq",
            "severity":"ERROR",
            "probe":{
                "adapter":"devbench",
                "tool":"fixture-array",
                "arguments":{},
                "json_path":"0.name",
            },
        }
        with patch.object(
            MOD,
            "post_tool",
            return_value=[{"name":"alpha"},{"name":"beta"}],
        ):
            row,raw=MOD.assertion_observation(
                assertion,
                base_url="http://127.0.0.1:8920",
                timeout_seconds=1.0,
            )
        self.assertEqual(row["status"],"pass")
        self.assertEqual(row["observed"],"alpha")
        self.assertEqual(raw[1]["name"],"beta")


    def test_gate_scoped_save_migration_assertion_emits_g21(self):
        value=runtime_test()
        value["fixture"]={
            "kind":"save",
            "save_path":"Fixture.ess",
            "destructive_copy_only":True,
        }
        value["assertions"].append({
            "id":"schema-upgraded",
            "kind":"value",
            "expected":2,
            "operator":"eq",
            "severity":"BLOCKER",
            "gates":["G21","G26"],
            "probe":{
                "adapter":"devbench",
                "tool":"inspect",
                "arguments":{"kind":"fixture.persistence"},
                "json_path":"schemaVersion",
            },
        })
        sess=session()
        sess["assertions"].append({
            "id":"schema-upgraded",
            "status":"needs-review",
            "severity":"BLOCKER",
            "expected":2,
            "observed":None,
            "issues":[],
        })
        sess["gates"][2]={
            "gate":"G21","status":"needs-review","evidence":[],"issues":[]
        }

        def fake_post(base,name,args,timeout_seconds=30.0):
            if name=="scenario":
                return {
                    "ok":True,
                    "results":[
                        {"index":0,"ok":True},
                        {"index":1,"satisfied":True},
                        {"index":2,"satisfied":True},
                    ],
                }
            if args.get("kind")=="state":
                return {"playerLoaded":True}
            return {"schemaVersion":2}

        with patch.object(MOD,"wait_for_health",return_value=dict(HEALTH)), \
             patch.object(MOD,"health",return_value=dict(HEALTH)), \
             patch.object(MOD,"post_tool",side_effect=fake_post):
            obs=MOD.run_observer(value,sess)

        gates={x["gate"]:x for x in obs["gates"]}
        self.assertEqual(gates["G21"]["status"],"pass")
        self.assertIn("schema-upgraded: pass",gates["G21"]["evidence"])


    def test_provider_visual_ssim_pass_can_be_deterministic(self):
        assertion={
            "id":"visual-checkpoint",
            "kind":"screenshot",
            "expected":True,
            "operator":"eq",
            "severity":"ERROR",
            "probe":{
                "adapter":"devbench",
                "tool":"capture",
                "arguments":{
                    "kind":"d3d11",
                    "checkpointId":"main-menu",
                    "golden":"Data/AgentOS/goldens/main-menu.png",
                    "threshold":0.98,
                },
                "json_path":"passed",
            },
        }
        raw={
            "ok":True,
            "provider":"d3d11",
            "kind":"screenshot",
            "path":"Data/SKSE/Plugins/devbench/captures/main-menu.png",
            "checkpointId":"main-menu",
            "inconclusive":False,
            "ssim":0.991,
            "threshold":0.98,
            "passed":True,
        }
        with patch.object(MOD,"post_tool",return_value=raw):
            row,result=MOD.assertion_observation(
                assertion,
                base_url="http://127.0.0.1:8920",
                timeout_seconds=1.0,
            )
        self.assertEqual(row["status"],"pass")
        artifact=MOD.capture_artifact(assertion,result)
        self.assertEqual(artifact["kind"],"screenshot")
        self.assertEqual(artifact["ssim"],0.991)
        self.assertFalse(artifact["inconclusive"])

    def test_inconclusive_capture_cannot_pass_even_when_ssim_passed(self):
        assertion={
            "id":"visual-checkpoint",
            "kind":"screenshot",
            "expected":True,
            "operator":"eq",
            "severity":"ERROR",
            "probe":{
                "adapter":"devbench",
                "tool":"capture",
                "arguments":{
                    "kind":"native",
                    "checkpointId":"main-menu",
                    "golden":"Data/AgentOS/goldens/main-menu.png",
                },
                "json_path":"passed",
            },
        }
        raw={
            "ok":True,
            "provider":"native",
            "kind":"screenshot",
            "path":"Data/SKSE/Plugins/devbench/captures/main-menu.bmp",
            "checkpointId":"main-menu",
            "inconclusive":True,
            "inconclusiveReason":"captured via the low-fidelity native fallback",
            "ssim":0.999,
            "threshold":0.98,
            "passed":True,
        }
        with patch.object(MOD,"post_tool",return_value=raw):
            row,_=MOD.assertion_observation(
                assertion,
                base_url="http://127.0.0.1:8920",
                timeout_seconds=1.0,
            )
        self.assertEqual(row["status"],"needs-review")
        self.assertTrue(any("inconclusive" in x for x in row["issues"]))

    def test_scene_mismatch_capture_cannot_pass(self):
        assertion={
            "id":"visual-checkpoint",
            "kind":"screenshot",
            "expected":True,
            "operator":"eq",
            "severity":"ERROR",
            "probe":{
                "adapter":"devbench",
                "tool":"capture",
                "arguments":{
                    "checkpointId":"main-menu",
                    "golden":"Data/AgentOS/goldens/main-menu.png",
                },
                "json_path":"passed",
            },
        }
        raw={
            "ok":True,
            "provider":"d3d11",
            "path":"capture.png",
            "inconclusive":True,
            "inconclusiveReason":"sceneMismatch",
            "passed":True,
        }
        with patch.object(MOD,"post_tool",return_value=raw):
            row,_=MOD.assertion_observation(
                assertion,
                base_url="http://127.0.0.1:8920",
                timeout_seconds=1.0,
            )
        self.assertEqual(row["status"],"needs-review")

    def test_capture_golden_error_requires_review(self):
        assertion={
            "id":"visual-checkpoint",
            "kind":"screenshot",
            "expected":True,
            "operator":"eq",
            "severity":"ERROR",
            "probe":{
                "adapter":"devbench",
                "tool":"capture",
                "arguments":{"checkpointId":"main-menu","golden":"missing.png"},
                "json_path":"passed",
            },
        }
        raw={
            "ok":True,
            "provider":"d3d11",
            "path":"capture.png",
            "inconclusive":False,
            "goldenError":"could not decode golden",
        }
        with patch.object(MOD,"post_tool",return_value=raw):
            row,_=MOD.assertion_observation(
                assertion,
                base_url="http://127.0.0.1:8920",
                timeout_seconds=1.0,
            )
        self.assertEqual(row["status"],"needs-review")
        self.assertTrue(any("golden comparison failed" in x for x in row["issues"]))


if __name__=="__main__":
    unittest.main()
