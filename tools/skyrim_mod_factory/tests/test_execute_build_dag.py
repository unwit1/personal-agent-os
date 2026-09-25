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

    def test_main_executes_two_node_chain_with_pinned_fake_toolchain(self):
        import sys
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            adapter_dir=root/"adapters"
            adapter_dir.mkdir()
            run_dir=root/"run"
            middle=root/"middle.txt"
            final=root/"final.txt"

            manifest=root/"manifest.json"
            quality=root/"quality.json"
            dag=root/"dag.json"
            context=root/"context.json"
            capabilities=root/"capabilities.json"
            toolchain=root/"toolchain.json"

            manifest.write_text(json.dumps({
                "project_id":"fixture-chain"
            }),encoding="utf-8")
            quality.write_text(json.dumps({"gates":[]}),encoding="utf-8")
            dag.write_text(json.dumps({
                "schema_version":"skyrim-build-dag-v1",
                "project_id":"fixture-chain",
                "nodes":[
                    {
                        "id":"generate.first",
                        "phase":"generate",
                        "action":"write first fixture",
                        "depends_on":[],
                        "adapters":["fixture-write"],
                        "gates":[],
                        "invalidated_by":[],
                        "outputs":[str(middle)],
                    },
                    {
                        "id":"generate.second",
                        "phase":"generate",
                        "action":"consume first fixture",
                        "depends_on":["generate.first"],
                        "adapters":["fixture-copy"],
                        "gates":[],
                        "invalidated_by":["generate.first"],
                        "outputs":[str(final)],
                    },
                ],
            }),encoding="utf-8")
            context.write_text(json.dumps({
                "schema_version":"skyrim-execution-context-v1",
                "project_id":"fixture-chain",
                "nodes":{
                    "generate.first":{
                        "outputs":[str(middle)],
                    },
                    "generate.second":{
                        "inputs":[str(middle)],
                        "outputs":[str(final)],
                        "variables":{"input_path":str(middle)},
                    },
                },
            }),encoding="utf-8")
            capabilities.write_text(json.dumps({
                "schema_version":"skyrim-tool-capability-registry-v1",
                "snapshot_date":"2026-09-24",
                "adapters":[],
            }),encoding="utf-8")
            toolchain.write_text(json.dumps({
                "adapters":[
                    {
                        "adapter_id":"fixture-write",
                        "executable":sys.executable,
                        "version":"fixture-python",
                    },
                    {
                        "adapter_id":"fixture-copy",
                        "executable":sys.executable,
                        "version":"fixture-python",
                    },
                ]
            }),encoding="utf-8")

            (adapter_dir/"fixture-write.json").write_text(json.dumps({
                "schema_version":"skyrim-tool-adapter-v1",
                "adapter_id":"fixture-write",
                "tool":"Fixture Writer",
                "invocation":{
                    "mode":"cli",
                    "arguments_template":[
                        "-c",
                        "from pathlib import Path; Path(r'{output_path}').write_text('stage-one', encoding='utf-8')",
                    ],
                },
                "success":{"exit_codes":[0]},
                "retry":{"safe":False,"max_attempts":1,"cleanup_outputs_first":False},
            }),encoding="utf-8")
            (adapter_dir/"fixture-copy.json").write_text(json.dumps({
                "schema_version":"skyrim-tool-adapter-v1",
                "adapter_id":"fixture-copy",
                "tool":"Fixture Copier",
                "invocation":{
                    "mode":"cli",
                    "arguments_template":[
                        "-c",
                        "from pathlib import Path; src=Path(r'{input_path}'); Path(r'{output_path}').write_text(src.read_text(encoding='utf-8')+'|stage-two', encoding='utf-8')",
                    ],
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
                "--toolchain-lock",str(toolchain),
                "--run-dir",str(run_dir),
                "--execute",
            ]
            with patch("sys.argv",argv):
                MOD.main()

            report=json.loads((run_dir/"build-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"],"passed")
            self.assertEqual(
                [step["id"] for step in report["steps"]],
                ["generate.first","generate.second"],
            )
            self.assertEqual(
                [step.get("adapter_id") for step in report["steps"]],
                ["fixture-write","fixture-copy"],
            )
            self.assertEqual(final.read_text(encoding="utf-8"),"stage-one|stage-two")
            self.assertTrue(all(step["status"]=="passed" for step in report["steps"]))
            self.assertTrue(all(step["outputs_after"][0]["exists"] for step in report["steps"]))

    def test_artifact_contract_accepts_schema_valid_json(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            artifact=root/"dag.json"
            artifact.write_text(json.dumps({
                "schema_version":"skyrim-build-dag-v1",
                "project_id":"fixture",
                "nodes":[],
            }),encoding="utf-8")
            node={"id":"generate.fixture"}
            context={"nodes":{"generate.fixture":{"artifact_contracts":[{
                "path":str(artifact),
                "validator":"json-schema",
                "schema":"skyrim-build-dag-v1.schema.json",
            }]}}}
            step={"id":"generate.fixture","status":"passed","issues":[]}
            checked=MOD.enforce_artifact_contracts(step,node,context)
            self.assertEqual(checked["status"],"passed")
            self.assertEqual(
                checked["evidence"]["artifact_contracts"][0]["status"],
                "pass",
            )

    def test_artifact_contract_fails_schema_invalid_json(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            artifact=root/"dag.json"
            artifact.write_text(json.dumps({
                "schema_version":"wrong",
                "project_id":"fixture",
                "nodes":[],
            }),encoding="utf-8")
            node={"id":"generate.fixture"}
            context={"nodes":{"generate.fixture":{"artifact_contracts":[{
                "path":str(artifact),
                "validator":"json-schema",
                "schema":"skyrim-build-dag-v1.schema.json",
            }]}}}
            step={"id":"generate.fixture","status":"passed","issues":[]}
            checked=MOD.enforce_artifact_contracts(step,node,context)
            self.assertEqual(checked["status"],"failed")
            self.assertIn("artifact contract failed",checked["issues"][0])

    def test_optional_missing_artifact_contract_does_not_fail(self):
        with tempfile.TemporaryDirectory() as td:
            artifact=Path(td)/"missing.json"
            node={"id":"generate.fixture"}
            context={"nodes":{"generate.fixture":{"artifact_contracts":[{
                "path":str(artifact),
                "validator":"json-schema",
                "schema":"skyrim-build-dag-v1.schema.json",
                "required":False,
            }]}}}
            step={"id":"generate.fixture","status":"passed","issues":[]}
            checked=MOD.enforce_artifact_contracts(step,node,context)
            self.assertEqual(checked["status"],"passed")
            self.assertEqual(
                checked["evidence"]["artifact_contracts"][0]["status"],
                "not-applicable",
            )


    def test_safe_retry_checkpoints_unchanged_failed_attempt_then_succeeds(self):
        import sys
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            adapter_dir=root/"adapters"
            adapter_dir.mkdir()
            counter=root/"counter.txt"
            out=root/"out.txt"
            script=(
                "from pathlib import Path; import sys; "
                "c=Path(r'{counter_path}'); "
                "n=int(c.read_text()) if c.exists() else 0; "
                "c.write_text(str(n+1)); "
                "sys.exit(1) if n==0 else Path(r'{output_path}').write_text('ok', encoding='utf-8')"
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
                "retry":{"safe":True,"max_attempts":2,"cleanup_outputs_first":False},
            }),encoding="utf-8")
            node={
                "id":"generate.fixture","phase":"generate","action":"fixture",
                "depends_on":[],"adapters":["fixture"],"gates":[],
                "invalidated_by":[],"outputs":[str(out)],
            }
            record=MOD.execute_adapter_node(
                node,
                capability_map={},
                adapter_dir=adapter_dir,
                lock={},
                context={
                    "variables":{"counter_path":str(counter)},
                    "policy":{"allow_safe_retry":True},
                },
                log_dir=root/"logs",
                execute=True,
            )
            self.assertEqual(record["status"],"passed")
            self.assertEqual(counter.read_text(encoding="utf-8"),"2")
            attempts=record["evidence"]["attempts"]
            self.assertEqual([x["decision"] for x in attempts],["retry","return"])
            self.assertTrue(all(Path(x["checkpoint"]).exists() for x in attempts))

    def test_safe_retry_stops_when_failed_attempt_mutates_output(self):
        import sys
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            adapter_dir=root/"adapters"
            adapter_dir.mkdir()
            out=root/"out.txt"
            script=(
                "from pathlib import Path; import sys; "
                "Path(r'{output_path}').write_text('partial', encoding='utf-8'); "
                "sys.exit(1)"
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
                "retry":{"safe":True,"max_attempts":2,"cleanup_outputs_first":False},
            }),encoding="utf-8")
            node={
                "id":"generate.fixture","phase":"generate","action":"fixture",
                "depends_on":[],"adapters":["fixture"],"gates":[],
                "invalidated_by":[],"outputs":[str(out)],
            }
            record=MOD.execute_adapter_node(
                node,
                capability_map={},
                adapter_dir=adapter_dir,
                lock={},
                context={"policy":{"allow_safe_retry":True}},
                log_dir=root/"logs",
                execute=True,
            )
            self.assertEqual(record["status"],"failed")
            self.assertEqual(len(record["evidence"]["attempts"]),1)
            attempt=record["evidence"]["attempts"][0]
            self.assertTrue(attempt["output_mutated"])
            self.assertEqual(attempt["decision"],"stop-for-rollback")
            self.assertTrue(Path(attempt["checkpoint"]).exists())
            self.assertIn("rollback checkpoint",record["issues"][-1])


    def test_main_invokes_auto_repair_bridge_after_failed_execution(self):
        import sys
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            adapter_dir=root/"adapters"
            adapter_dir.mkdir()
            run_dir=root/"run"
            manifest=root/"manifest.json"
            quality=root/"quality.json"
            dag=root/"dag.json"
            context=root/"context.json"
            capabilities=root/"capabilities.json"

            manifest.write_text(json.dumps({"project_id":"fixture-auto"}),encoding="utf-8")
            quality.write_text(json.dumps({"gates":[]}),encoding="utf-8")
            dag.write_text(json.dumps({
                "schema_version":"skyrim-build-dag-v1",
                "project_id":"fixture-auto",
                "nodes":[{
                    "id":"generate.fixture",
                    "phase":"generate",
                    "action":"fail fixture",
                    "depends_on":[],
                    "adapters":["fixture"],
                    "gates":[],
                    "invalidated_by":[],
                    "outputs":[],
                }],
            }),encoding="utf-8")
            context.write_text(json.dumps({
                "schema_version":"skyrim-execution-context-v1",
                "project_id":"fixture-auto",
            }),encoding="utf-8")
            capabilities.write_text(json.dumps({
                "schema_version":"skyrim-tool-capability-registry-v1",
                "snapshot_date":"2026-09-24",
                "adapters":[],
            }),encoding="utf-8")
            (adapter_dir/"fixture.json").write_text(json.dumps({
                "schema_version":"skyrim-tool-adapter-v1",
                "adapter_id":"fixture",
                "tool":"Fixture",
                "invocation":{
                    "mode":"cli",
                    "executable":sys.executable,
                    "arguments_template":["-c","import sys; sys.exit(7)"],
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
                "--auto-repair",
            ]
            repaired={"result_status":"repaired","executed":True}
            with patch("sys.argv",argv), patch.object(
                MOD,"run_automatic_repair",return_value=repaired
            ) as bridge:
                MOD.main()

            bridge.assert_called_once()
            report=json.loads((run_dir/"build-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"],"failed")
            self.assertTrue((run_dir/"execution-state.json").exists())


if __name__=="__main__":
    unittest.main()
