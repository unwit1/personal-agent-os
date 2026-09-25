import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "build_runtime_execution_context",
    ROOT/"build_runtime_execution_context.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

def worker(root):
    managed=root/"managed"
    return {
        "schema_version":"skyrim-runtime-worker-config-v1",
        "worker_id":"fixture",
        "platform":"windows",
        "mo2":{
            "executable":"C:/MO2/ModOrganizer.exe",
            "configured_executable":"SKSE",
        },
        "profiles":{
            "template_dir":"C:/MO2/profiles/Template",
            "disposable_root":str(managed/"profiles"),
            "profile_name_prefix":"AgentOS",
        },
        "workspace":{
            "run_root":str(managed/"runs"),
            "evidence_root":str(managed/"evidence"),
            "allowed_mutation_roots":[str(managed)],
        },
        "process_policy":{
            "exclusive_process_names":["ModOrganizer.exe","SkyrimSE.exe"],
        },
        "timeouts":{
            "launch_seconds":30,
            "scenario_seconds":60,
            "shutdown_seconds":30,
        },
    }

def runtime_test(project_id="fixture"):
    return {
        "schema_version":"skyrim-runtime-test-v1",
        "test_id":project_id+".smoke",
        "project_id":project_id,
        "adapter":"mo2-devbench-runtime",
        "fixture":{
            "kind":"new-game",
            "destructive_copy_only":True,
        },
        "steps":[{
            "id":"health",
            "action":"probe runtime health",
            "driver":{
                "adapter":"devbench",
                "kind":"tool",
                "tool":"inspect",
                "arguments":{"kind":"health"},
            },
        }],
        "assertions":[{
            "id":"pid",
            "kind":"health",
            "expected":True,
            "operator":"exists",
            "severity":"BLOCKER",
            "probe":{
                "adapter":"devbench",
                "tool":"inspect",
                "arguments":{"kind":"health"},
                "json_path":"pid",
            },
        }],
    }

def dag():
    return {
        "schema_version":"skyrim-build-dag-v1",
        "project_id":"fixture",
        "nodes":[
            {"id":"runtime.smoke","phase":"runtime"},
            {"id":"runtime.regression","phase":"runtime"},
        ],
    }

class BuildRuntimeExecutionContextTests(unittest.TestCase):
    def test_smoke_binding_sets_adapter_variables_io_and_contract(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            worker_path=root/"worker.json"
            smoke_path=root/"smoke.json"
            worker_path.write_text(json.dumps(worker(root)),encoding="utf-8")
            smoke_path.write_text(json.dumps(runtime_test()),encoding="utf-8")
            context=MOD.build_context(
                project_id="fixture",
                dag=dag(),
                worker_config_path=worker_path,
                run_root=root/"run",
                smoke_test=smoke_path,
                run_nonce="abc123",
            )
            node=context["nodes"]["runtime.smoke"]
            self.assertEqual(node["adapter_order"],["mo2-devbench-runtime"])
            self.assertEqual(node["variables"]["runtime_run_id"],"fixture-runtime.smoke-abc123")
            self.assertEqual(node["variables"]["runtime_test"],str(smoke_path.resolve()))
            self.assertEqual(
                node["variables"]["runtime_worker_config"],
                str(worker_path.resolve()),
            )
            result=Path(node["variables"]["runtime_result"])
            self.assertEqual(node["outputs"],[str(result)])
            self.assertEqual(
                node["artifact_contracts"][0]["schema"],
                "skyrim-runtime-session-result-v1.schema.json",
            )
            self.assertIn("python_executable",context["variables"])
            self.assertEqual(context["variables"]["repo_root"],str(MOD.REPO))
            self.assertEqual(
                MOD.schema_errors(context,MOD.CONTEXT_SCHEMA),
                [],
            )

    def test_unbound_regression_node_is_not_fabricated(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            worker_path=root/"worker.json"
            smoke_path=root/"smoke.json"
            worker_path.write_text(json.dumps(worker(root)),encoding="utf-8")
            smoke_path.write_text(json.dumps(runtime_test()),encoding="utf-8")
            context=MOD.build_context(
                project_id="fixture",
                dag=dag(),
                worker_config_path=worker_path,
                run_root=root/"run",
                smoke_test=smoke_path,
                run_nonce="abc123",
            )
            self.assertNotIn("runtime.regression",context["nodes"])

    def test_invalid_runtime_test_fails_before_context_is_emitted(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            worker_path=root/"worker.json"
            bad_path=root/"bad.json"
            worker_path.write_text(json.dumps(worker(root)),encoding="utf-8")
            bad_path.write_text(json.dumps({"schema_version":"wrong"}),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"runtime test"):
                MOD.build_context(
                    project_id="fixture",
                    dag=dag(),
                    worker_config_path=worker_path,
                    run_root=root/"run",
                    smoke_test=bad_path,
                )

    def test_non_runtime_adapter_test_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            worker_path=root/"worker.json"
            test_path=root/"test.json"
            worker_path.write_text(json.dumps(worker(root)),encoding="utf-8")
            value=runtime_test()
            value["adapter"]="skytest"
            test_path.write_text(json.dumps(value),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"adapter must be"):
                MOD.build_context(
                    project_id="fixture",
                    dag=dag(),
                    worker_config_path=worker_path,
                    run_root=root/"run",
                    smoke_test=test_path,
                )

if __name__=="__main__":
    unittest.main()
