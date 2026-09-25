import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("run_repair_loop",ROOT/"run_repair_loop.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

RULE_ID="SKYRIM-GENERATED-OUTPUT-STALE"
RULE={
    "schema_version":"skyrim-analyzer-rule-v1",
    "rule_id":RULE_ID,
    "title":"Generated output is stale",
    "scope":["generated-output"],
    "severity":"ERROR",
    "detection":{"kind":"generated-output","algorithm":"detect stale output"},
    "fix_policy":{
        "mode":"automatic",
        "algorithm":"invalidate and regenerate",
        "postconditions":["input hashes match","generator passes"],
    },
    "evidence":[{"source":"test","type":"repro-test"}],
}
HANDLERS={
    "schema_version":"skyrim-repair-handler-registry-v1",
    "handlers":[{
        "handler_id":"generated-output.invalidate-and-regenerate",
        "rule_id":RULE_ID,
        "automatic":True,
        "implementation":{
            "kind":"executor-native",
            "entrypoint":"invalidate_and_regenerate_generated_node",
        },
        "reversible":True,
        "checkpoint_required":True,
        "mutation_scope":["execution-state","generated-output"],
        "postconditions":["rerun generator","validate output"],
    }],
}

def write(path,value):
    path.write_text(json.dumps(value),encoding="utf-8")

def node_state(name):
    return {
        "fingerprint":"a"*64,
        "status":"passed",
        "updated_at":"2026-09-24T00:00:00+00:00",
        "step_record":{"id":name,"status":"passed","issues":[]},
        "output_fingerprints":[],
    }

def args_for(root,rule_pack,handlers):
    run_dir=root/"run"
    run_dir.mkdir()
    manifest=root/"manifest.json"
    quality=root/"quality.json"
    dag=root/"dag.json"
    report=root/"failed.json"
    state=run_dir/"execution-state.json"
    write(manifest,{"project_id":"fixture"})
    write(quality,{"gates":[]})
    write(dag,{
        "schema_version":"skyrim-build-dag-v1",
        "project_id":"fixture",
        "nodes":[{
            "id":"generate.records",
            "phase":"generate",
            "action":"generate",
            "depends_on":[],
            "adapters":[],
            "gates":[],
            "invalidated_by":[],
        }],
    })
    write(report,{
        "schema_version":"skyrim-mod-build-report-v1",
        "project_id":"fixture",
        "build_id":"build-1",
        "started_at":"2026-09-24T00:00:00+00:00",
        "finished_at":"2026-09-24T00:01:00+00:00",
        "status":"failed",
        "steps":[{
            "id":"generate.records",
            "status":"failed",
            "issues":["stale output"],
            "issue_codes":[RULE_ID],
            "analyzer_rule_ids":[RULE_ID],
        }],
        "gates":[],
    })
    MOD.EXEC.save_execution_state(state,{
        "schema_version":"skyrim-execution-state-v1",
        "project_id":"fixture",
        "build_id":"build-1",
        "updated_at":"2026-09-24T00:00:00+00:00",
        "nodes":{"generate.records":node_state("generate.records")},
    })
    return argparse.Namespace(
        failed_report=report,
        manifest=manifest,
        quality_plan=quality,
        build_dag=dag,
        run_dir=run_dir,
        work_dir=None,
        state=state,
        toolchain_lock=None,
        context=None,
        capabilities=None,
        adapter_dir=None,
        gate_registry=None,
        rule_pack=rule_pack,
        handler_registry=handlers,
        allowed_output_root=[],
        git_commit=None,
        execute=True,
        output=None,
    )

class RunRepairLoopTests(unittest.TestCase):
    def test_proposal_only_failure_stops_before_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            rule_pack=root/"rules.json"
            handlers=root/"handlers.json"
            proposal=dict(RULE)
            proposal["fix_policy"]={
                "mode":"proposal",
                "algorithm":"review manually",
                "postconditions":["reviewed"],
            }
            write(rule_pack,{"rules":[proposal]})
            write(handlers,HANDLERS)
            args=args_for(root,rule_pack,handlers)
            result=MOD.run_cycle(args)
            self.assertEqual(result["result_status"],"escalated")
            self.assertFalse(result["executed"])
            state=MOD.load(args.state)
            self.assertIn("generate.records",state["nodes"])

    def test_automatic_failure_reruns_and_finalizes_repaired(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            rule_pack=root/"rules.json"
            handlers=root/"handlers.json"
            write(rule_pack,{"rules":[RULE]})
            write(handlers,HANDLERS)
            args=args_for(root,rule_pack,handlers)

            def fake_run(cmd,check=False):
                write(args.run_dir/"build-report.json",{
                    "schema_version":"skyrim-mod-build-report-v1",
                    "project_id":"fixture",
                    "build_id":"build-1",
                    "started_at":"2026-09-24T00:02:00+00:00",
                    "finished_at":"2026-09-24T00:03:00+00:00",
                    "status":"passed",
                    "steps":[{
                        "id":"generate.records",
                        "status":"passed",
                        "issues":[],
                        "issue_codes":[],
                    }],
                    "gates":[],
                })
                class Result:
                    returncode=0
                return Result()

            with patch.object(MOD.subprocess,"run",side_effect=fake_run):
                result=MOD.run_cycle(args)

            self.assertEqual(result["result_status"],"repaired")
            self.assertTrue(result["executed"])
            self.assertEqual(result["rerun_exit_code"],0)
            final_plan=MOD.load(Path(result["repair_plan"]))
            self.assertEqual(final_plan["result"]["status"],"repaired")
            self.assertTrue(Path(result["original_report"]).exists())
            self.assertTrue(Path(result["post_repair_report"]).exists())

if __name__=="__main__":
    unittest.main()
