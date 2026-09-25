import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

REPAIR=load_module("execute_repair",ROOT/"execute_repair.py")
PLAN=load_module("plan_repair",ROOT/"plan_repair.py")

RULE_ID="SKYRIM-GENERATED-OUTPUT-STALE"
HANDLER={
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

def make_plan():
    bug={
        "schema_version":"skyrim-bug-regression-v1",
        "bug_id":"BUG-STALE",
        "project_id":"fixture",
        "build_id":"build-1",
        "status":"root-caused",
        "symptom":"stale generated output",
        "environment":{},
        "evidence":[],
        "layer":"generated-output",
        "root_cause":"input hash changed",
        "failing_task":"generate.records",
        "regression":{"analyzer_rule_id":RULE_ID},
    }
    return PLAN.plan(
        bug,
        {"rules":[RULE]},
        handler_registry=HANDLER,
    )

def node_state(name):
    return {
        "fingerprint":(name[0] if name else "a")*64,
        "status":"passed",
        "updated_at":"2026-09-24T00:00:00+00:00",
        "step_record":{"id":name,"status":"passed","issues":[]},
        "output_fingerprints":[],
    }

def make_state():
    return {
        "schema_version":"skyrim-execution-state-v1",
        "project_id":"fixture",
        "build_id":"build-1",
        "updated_at":"2026-09-24T00:00:00+00:00",
        "nodes":{
            "preflight.manifest":node_state("preflight.manifest"),
            "generate.records":node_state("generate.records"),
            "validate.records":node_state("validate.records"),
            "package.staging":node_state("package.staging"),
        },
    }

DAG={
    "schema_version":"skyrim-build-dag-v1",
    "project_id":"fixture",
    "nodes":[
        {
            "id":"preflight.manifest","phase":"preflight","action":"preflight",
            "depends_on":[],"adapters":[],"gates":[],"invalidated_by":[],
        },
        {
            "id":"generate.records","phase":"generate","action":"generate",
            "depends_on":["preflight.manifest"],"adapters":[],"gates":[],"invalidated_by":[],
        },
        {
            "id":"validate.records","phase":"validate","action":"validate",
            "depends_on":["generate.records"],"adapters":[],"gates":[],"invalidated_by":[],
        },
        {
            "id":"package.staging","phase":"package","action":"package",
            "depends_on":["validate.records"],"adapters":[],"gates":[],"invalidated_by":[],
        },
    ],
}

class ExecuteRepairTests(unittest.TestCase):
    def test_downstream_closure_is_minimal(self):
        self.assertEqual(
            REPAIR.downstream_closure(DAG,"generate.records"),
            ["generate.records","validate.records","package.staging"],
        )

    def test_dry_run_does_not_mutate_state(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            state=make_state()
            before=set(state["nodes"])
            updated,checkpoint=REPAIR.execute(
                make_plan(),DAG,state,HANDLER,
                state_path=root/"state.json",
                checkpoint_dir=root/"checkpoints",
                execute_mutation=False,
            )
            self.assertEqual(before,set(state["nodes"]))
            self.assertIsNone(checkpoint)
            self.assertEqual(updated["result"]["status"],"planned")
            self.assertIn("dry-run",updated["result"]["evidence"][-1])

    def test_execute_checkpoints_then_invalidates_only_downstream(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            state_path=root/"state.json"
            state=make_state()
            REPAIR.EXEC.save_execution_state(state_path,state)

            updated,checkpoint=REPAIR.execute(
                make_plan(),DAG,state,HANDLER,
                state_path=state_path,
                checkpoint_dir=root/"checkpoints",
                execute_mutation=True,
            )

            self.assertEqual(updated["result"]["status"],"testing")
            self.assertIsNotNone(checkpoint)
            self.assertEqual(
                checkpoint["invalidated_nodes"],
                ["generate.records","validate.records","package.staging"],
            )
            self.assertIn("preflight.manifest",state["nodes"])
            self.assertNotIn("generate.records",state["nodes"])
            self.assertNotIn("validate.records",state["nodes"])
            self.assertNotIn("package.staging",state["nodes"])

            cp_path=Path(updated["rollback"]["checkpoint"])
            self.assertTrue(cp_path.exists())
            self.assertTrue((root/"state.json").exists())
            restored_on_disk=REPAIR.load(state_path)
            self.assertEqual(set(restored_on_disk["nodes"]),{"preflight.manifest"})

    def test_nonautomatic_plan_is_rejected(self):
        plan=make_plan()
        plan["policy"]["mode"]="proposal"
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                REPAIR.execute(
                    plan,DAG,make_state(),HANDLER,
                    state_path=Path(td)/"state.json",
                    checkpoint_dir=Path(td)/"checkpoints",
                    execute_mutation=True,
                )

    def test_execute_backs_up_allowlisted_generated_output(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            generated=root/"generated"
            generated.mkdir()
            artifact=generated/"patch.esp"
            artifact.write_text("old",encoding="utf-8")

            state=make_state()
            state["nodes"]["generate.records"]["output_fingerprints"]=[
                REPAIR.EXEC.path_fingerprint(str(artifact))
            ]
            state_path=root/"state.json"
            REPAIR.EXEC.save_execution_state(state_path,state)

            updated,checkpoint=REPAIR.execute(
                make_plan(),DAG,state,HANDLER,
                state_path=state_path,
                checkpoint_dir=root/"checkpoints",
                execute_mutation=True,
                allowed_output_roots=[generated],
            )
            self.assertEqual(len(checkpoint["output_backups"]),1)
            backup=checkpoint["output_backups"][0]
            self.assertEqual(backup["path"],str(artifact))
            backup_path=Path(backup["backup_path"])
            self.assertTrue(backup_path.exists())
            self.assertEqual(backup_path.read_text(encoding="utf-8"),"old")
            self.assertEqual(backup["sha256"],REPAIR.EXEC.sha256(artifact))
            self.assertTrue(Path(updated["rollback"]["checkpoint"]).exists())

    def test_execute_refuses_output_outside_allowed_root_before_state_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            allowed=root/"allowed"
            allowed.mkdir()
            outside=root/"outside.esp"
            outside.write_text("old",encoding="utf-8")
            state=make_state()
            state["nodes"]["generate.records"]["output_fingerprints"]=[
                REPAIR.EXEC.path_fingerprint(str(outside))
            ]
            before=set(state["nodes"])
            with self.assertRaises(ValueError):
                REPAIR.execute(
                    make_plan(),DAG,state,HANDLER,
                    state_path=root/"state.json",
                    checkpoint_dir=root/"checkpoints",
                    execute_mutation=True,
                    allowed_output_roots=[allowed],
                )
            self.assertEqual(before,set(state["nodes"]))

    def test_restore_checkpoint_restores_state_and_existing_output(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            generated=root/"generated"
            generated.mkdir()
            artifact=generated/"patch.esp"
            artifact.write_text("old",encoding="utf-8")

            state=make_state()
            state["nodes"]["generate.records"]["output_fingerprints"]=[
                REPAIR.EXEC.path_fingerprint(str(artifact))
            ]
            state_path=root/"state.json"
            REPAIR.EXEC.save_execution_state(state_path,state)
            _,checkpoint=REPAIR.execute(
                make_plan(),DAG,state,HANDLER,
                state_path=state_path,
                checkpoint_dir=root/"checkpoints",
                execute_mutation=True,
                allowed_output_roots=[generated],
            )
            artifact.write_text("bad-repair",encoding="utf-8")
            mutated=REPAIR.load(state_path)
            mutated["nodes"]["generate.records"]=node_state("generate.records")
            REPAIR.EXEC.save_execution_state(state_path,mutated)

            result=REPAIR.restore_checkpoint(
                checkpoint,
                state_path=state_path,
                allowed_output_roots=[generated],
            )
            self.assertEqual(artifact.read_text(encoding="utf-8"),"old")
            restored=REPAIR.load(state_path)
            self.assertEqual(
                set(restored["nodes"]),
                {"preflight.manifest","generate.records","validate.records","package.staging"},
            )
            self.assertEqual(result["restored_outputs"][0]["action"],"restored")

    def test_restore_checkpoint_removes_output_that_was_absent_before_repair(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            generated=root/"generated"
            generated.mkdir()
            artifact=generated/"new.esp"

            state=make_state()
            state["nodes"]["generate.records"]["output_fingerprints"]=[
                REPAIR.EXEC.path_fingerprint(str(artifact))
            ]
            state_path=root/"state.json"
            REPAIR.EXEC.save_execution_state(state_path,state)
            _,checkpoint=REPAIR.execute(
                make_plan(),DAG,state,HANDLER,
                state_path=state_path,
                checkpoint_dir=root/"checkpoints",
                execute_mutation=True,
                allowed_output_roots=[generated],
            )
            artifact.write_text("bad-new-output",encoding="utf-8")
            self.assertTrue(artifact.exists())

            result=REPAIR.restore_checkpoint(
                checkpoint,
                state_path=state_path,
                allowed_output_roots=[generated],
            )
            self.assertFalse(artifact.exists())
            self.assertEqual(result["restored_outputs"][0]["action"],"removed")


    def test_finalize_repair_marks_clean_rerun_repaired(self):
        plan=make_plan()
        report={
            "status":"passed",
            "steps":[{"id":"generate.records","status":"passed","issue_codes":[]}],
            "gates":[],
        }
        finalized=REPAIR.finalize_repair(plan,report,execute_rollback=False)
        self.assertEqual(finalized["result"]["status"],"repaired")
        self.assertEqual(finalized["result"]["new_issue_codes"],[])

    def test_finalize_repair_rolls_back_failed_rerun(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            generated=root/"generated"
            generated.mkdir()
            artifact=generated/"patch.esp"
            artifact.write_text("old",encoding="utf-8")
            state=make_state()
            state["nodes"]["generate.records"]["output_fingerprints"]=[
                REPAIR.EXEC.path_fingerprint(str(artifact))
            ]
            state_path=root/"state.json"
            REPAIR.EXEC.save_execution_state(state_path,state)
            active,checkpoint=REPAIR.execute(
                make_plan(),DAG,state,HANDLER,
                state_path=state_path,
                checkpoint_dir=root/"checkpoints",
                execute_mutation=True,
                allowed_output_roots=[generated],
            )
            artifact.write_text("bad-repair",encoding="utf-8")
            failed_report={
                "status":"failed",
                "steps":[{
                    "id":"generate.records",
                    "status":"failed",
                    "issue_codes":["SKYRIM-NEW-FAILURE"],
                }],
                "gates":[],
            }
            finalized=REPAIR.finalize_repair(
                active,
                failed_report,
                checkpoint=checkpoint,
                state_path=state_path,
                allowed_output_roots=[generated],
                execute_rollback=True,
            )
            self.assertEqual(finalized["result"]["status"],"rolled-back")
            self.assertEqual(
                finalized["result"]["new_issue_codes"],
                ["SKYRIM-NEW-FAILURE"],
            )
            self.assertEqual(artifact.read_text(encoding="utf-8"),"old")
            restored=REPAIR.load(state_path)
            self.assertIn("generate.records",restored["nodes"])

    def test_finalize_repair_escalates_unproven_warning(self):
        plan=make_plan()
        report={
            "status":"needs-review",
            "steps":[{"id":"generate.records","status":"passed","issue_codes":[]}],
            "gates":[{"gate":"G19","status":"warning"}],
        }
        finalized=REPAIR.finalize_repair(plan,report,execute_rollback=False)
        self.assertEqual(finalized["result"]["status"],"escalated")


    def test_finalize_repair_promotes_eligible_validated_bug(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            bug={
                "schema_version":"skyrim-bug-regression-v1",
                "bug_id":"BUG-STALE",
                "project_id":"fixture",
                "build_id":"build-1",
                "status":"root-caused",
                "symptom":"stale generated output",
                "environment":{},
                "reproduction":[{"step":"change source input"}],
                "evidence":["SKYRIM-GENERATED-OUTPUT-STALE"],
                "root_cause":"cached generated artifact survived input change",
                "layer":"generated-output",
                "regression":{"analyzer_rule_id":RULE_ID},
                "failing_task":"generate.records",
            }
            report={
                "status":"passed",
                "steps":[{"id":"generate.records","status":"passed","issue_codes":[]}],
                "gates":[],
            }
            finalized=REPAIR.finalize_repair(
                make_plan(),
                report,
                state_path=root/"execution-state.json",
                execute_rollback=False,
                bug=bug,
            )
            self.assertEqual(finalized["result"]["status"],"repaired")
            self.assertTrue(finalized["result"]["regression_promoted"])
            candidate=root/"regression-candidates"/"BUG-STALE.json"
            self.assertTrue(candidate.exists())
            packet=REPAIR.load(candidate)
            self.assertEqual(packet["schema_version"],"skyrim-regression-candidate-v1")
            self.assertEqual(packet["bug_id"],"BUG-STALE")


if __name__=="__main__":
    unittest.main()
