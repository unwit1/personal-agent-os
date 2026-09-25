import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("execute_build_dag",ROOT/"execute_build_dag.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class ExecuteBuildDagTests(unittest.TestCase):
    def test_topological_order_respects_dependencies(self):
        dag={
            "nodes":[
                {"id":"b","depends_on":["a"]},
                {"id":"a","depends_on":[]},
                {"id":"c","depends_on":["b"]},
            ]
        }
        self.assertEqual([x["id"] for x in MOD.topological_order(dag)],["a","b","c"])

    def test_topological_order_rejects_missing_dependency(self):
        with self.assertRaises(ValueError):
            MOD.topological_order({"nodes":[{"id":"a","depends_on":["missing"]}]})

    def test_hydrate_adapter_uses_pinned_executable(self):
        adapter={
            "adapter_id":"fixture",
            "tool":"Fixture",
            "invocation":{"mode":"cli","arguments_template":["--version"]},
        }
        hydrated=MOD.hydrate_adapter(adapter,{
            "adapter_id":"fixture",
            "executable":"C:/Tools/fixture.exe",
            "version":"1.2.3",
        })
        self.assertEqual(hydrated["invocation"]["executable"],"C:/Tools/fixture.exe")
        self.assertEqual(hydrated["tool_version"],"1.2.3")

    def test_execute_adapter_node_dry_run_resolves_manifest_and_lock(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            adapter_dir=root/"adapters"
            adapter_dir.mkdir()
            (adapter_dir/"fixture.json").write_text(json.dumps({
                "schema_version":"skyrim-tool-adapter-v1",
                "adapter_id":"fixture",
                "tool":"Fixture",
                "invocation":{
                    "mode":"cli",
                    "arguments_template":["--input","{input_path}"],
                },
                "retry":{"safe":True,"max_attempts":2,"cleanup_outputs_first":False},
            }),encoding="utf-8")
            node={
                "id":"generate.fixture",
                "phase":"generate",
                "action":"fixture",
                "depends_on":[],
                "adapters":["fixture"],
                "gates":[],
                "invalidated_by":[],
                "outputs":[],
            }
            context={
                "variables":{"input_path":"thing.txt"},
                "policy":{"allow_safe_retry":True},
            }
            lock={
                "adapters":[{
                    "adapter_id":"fixture",
                    "executable":"python",
                    "version":"1.0",
                }]
            }
            record=MOD.execute_adapter_node(
                node,
                capability_map={},
                adapter_dir=adapter_dir,
                lock=lock,
                context=context,
                log_dir=root/"logs",
                execute=False,
            )
            self.assertEqual(record["id"],"generate.fixture")
            self.assertEqual(record["adapter_id"],"fixture")
            self.assertEqual(record["status"],"skipped")
            self.assertTrue(record["dry_run"])
            self.assertIn("adapter_manifest",record["evidence"])

    def test_execute_adapter_node_real_process_and_output_readback(self):
        import sys
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            adapter_dir=root/"adapters"
            adapter_dir.mkdir()
            out=root/"generated.txt"
            script="from pathlib import Path; Path(r'{output_path}').write_text('ok', encoding='utf-8')"
            (adapter_dir/"fixture.json").write_text(json.dumps({
                "schema_version":"skyrim-tool-adapter-v1",
                "adapter_id":"fixture",
                "tool":"Fixture",
                "invocation":{
                    "mode":"cli",
                    "executable":sys.executable,
                    "arguments_template":["-c",script],
                },
                "success":{"exit_codes":[0]},
                "retry":{"safe":True,"max_attempts":1,"cleanup_outputs_first":False},
            }),encoding="utf-8")
            node={
                "id":"generate.fixture",
                "phase":"generate",
                "action":"fixture",
                "depends_on":[],
                "adapters":["fixture"],
                "gates":[],
                "invalidated_by":[],
                "outputs":[str(out)],
            }
            record=MOD.execute_adapter_node(
                node,
                capability_map={},
                adapter_dir=adapter_dir,
                lock={},
                context={},
                log_dir=root/"logs",
                execute=True,
            )
            self.assertEqual(record["status"],"passed")
            self.assertTrue(out.exists())
            self.assertEqual(out.read_text(encoding="utf-8"),"ok")
            self.assertTrue(record["outputs_after"][0]["exists"])
            self.assertIn("sha256",record["outputs_after"][0])

    def test_unresolved_adapter_requires_review(self):
        node={
            "id":"validate.unknown",
            "phase":"validate",
            "action":"unknown",
            "depends_on":[],
            "adapters":["not-real"],
            "gates":[],
            "invalidated_by":[],
            "outputs":[],
        }
        with tempfile.TemporaryDirectory() as td:
            record=MOD.execute_adapter_node(
                node,
                capability_map={},
                adapter_dir=Path(td),
                lock={},
                context={},
                log_dir=Path(td)/"logs",
                execute=False,
            )
        self.assertEqual(record["status"],"needs-review")
        self.assertIn("no executable adapter manifest",record["issues"][0])

    def test_failed_dependency_blocks_downstream(self):
        node={"id":"b","depends_on":["a"]}
        blocked=MOD.blocked_by_dependencies(
            node,{"a":{"status":"failed"}},continue_review=False
        )
        self.assertEqual(blocked,["a=failed"])

    def test_main_resumes_passed_node_and_invalidates_on_input_change(self):
        import sys
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            adapter_dir=root/"adapters"
            adapter_dir.mkdir()
            run_dir=root/"run"
            inp=root/"input.txt"
            out=root/"output.txt"
            counter=root/"counter.txt"
            inp.write_text("one",encoding="utf-8")

            manifest=root/"manifest.json"
            quality=root/"quality.json"
            dag=root/"dag.json"
            context=root/"context.json"
            capabilities=root/"capabilities.json"

            manifest.write_text(json.dumps({
                "project_id":"fixture-project"
            }),encoding="utf-8")
            quality.write_text(json.dumps({"gates":[]}),encoding="utf-8")
            dag.write_text(json.dumps({
                "schema_version":"skyrim-build-dag-v1",
                "project_id":"fixture-project",
                "nodes":[{
                    "id":"generate.fixture",
                    "phase":"generate",
                    "action":"generate fixture",
                    "depends_on":[],
                    "adapters":["fixture"],
                    "gates":[],
                    "invalidated_by":["input"],
                    "outputs":[str(out)],
                }],
            }),encoding="utf-8")
            context.write_text(json.dumps({
                "schema_version":"skyrim-execution-context-v1",
                "project_id":"fixture-project",
                "variables":{
                    "counter_path":str(counter),
                },
                "nodes":{
                    "generate.fixture":{
                        "inputs":[str(inp)],
                        "outputs":[str(out)],
                    }
                },
            }),encoding="utf-8")
            capabilities.write_text(json.dumps({
                "schema_version":"skyrim-tool-capability-registry-v1",
                "snapshot_date":"2026-09-24",
                "adapters":[],
            }),encoding="utf-8")

            script=(
                "from pathlib import Path; "
                "c=Path(r'{counter_path}'); "
                "n=int(c.read_text() or '0') if c.exists() else 0; "
                "c.write_text(str(n+1)); "
                "Path(r'{output_path}').write_text(Path(r'"+str(inp)+"').read_text())"
            )
            (adapter_dir/"fixture.json").write_text(json.dumps({
                "schema_version":"skyrim-tool-adapter-v1",
                "adapter_id":"fixture",
                "tool":"Fixture",
                "invocation":{
                    "mode":"cli",
                    "executable":sys.executable,
                    "arguments_template":["-c",script],
                },
                "success":{"exit_codes":[0]},
                "retry":{"safe":False,"max_attempts":1,"cleanup_outputs_first":False},
            }),encoding="utf-8")

            argv=[
                "execute_build_dag.py",
                str(manifest),
                str(quality),
                str(dag),
                "--context",str(context),
                "--capabilities",str(capabilities),
                "--adapter-dir",str(adapter_dir),
                "--run-dir",str(run_dir),
                "--execute",
            ]
            with patch("sys.argv",argv):
                MOD.main()
            self.assertEqual(counter.read_text(),"1")
            first_report=json.loads((run_dir/"build-report.json").read_text())
            self.assertEqual(first_report["status"],"passed")

            with patch("sys.argv",argv):
                MOD.main()
            self.assertEqual(counter.read_text(),"1")
            second_report=json.loads((run_dir/"build-report.json").read_text())
            self.assertTrue(
                second_report["steps"][0]["evidence"]["resumed_from_state"]
            )
            self.assertEqual(
                first_report["build_id"],
                second_report["build_id"],
            )

            inp.write_text("two",encoding="utf-8")
            with patch("sys.argv",argv):
                MOD.main()
            self.assertEqual(counter.read_text(),"2")
            third_report=json.loads((run_dir/"build-report.json").read_text())
            self.assertFalse(
                bool(third_report["steps"][0].get("evidence",{}).get("resumed_from_state"))
            )
            self.assertEqual(out.read_text(encoding="utf-8"),"two")

if __name__=="__main__":
    unittest.main()
