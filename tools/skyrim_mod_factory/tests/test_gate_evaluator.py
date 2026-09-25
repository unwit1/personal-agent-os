import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("evaluate_gates",ROOT/"evaluate_gates.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

def policy(gate="G00",mode="automatic",earliest="preflight",final="preflight"):
    return {
        "schema_version":"skyrim-validation-gate-registry-v1",
        "gates":[{
            "gate":gate,
            "name":"Fixture",
            "severity":"BLOCKER",
            "blocking":True,
            "evidence_mode":mode,
            "earliest_phase":earliest,
            "final_phase":final,
            "default_on_missing":"needs-review",
            "independent_validation":True,
            "runtime_required":mode=="runtime",
            "human_required":False,
            "notes":"fixture",
        }]
    }

def dag(gate="G00",phase="preflight"):
    return {
        "schema_version":"skyrim-build-dag-v1",
        "project_id":"fixture",
        "nodes":[{
            "id":"node.fixture",
            "phase":phase,
            "action":"fixture",
            "depends_on":[],
            "adapters":[],
            "gates":[gate],
            "invalidated_by":[],
        }],
    }

def report(status="passed",gates=None):
    return {
        "schema_version":"skyrim-mod-build-report-v1",
        "project_id":"fixture",
        "build_id":"build",
        "started_at":"2026-09-24T00:00:00+00:00",
        "status":"running",
        "steps":[{"id":"node.fixture","status":status}],
        "gates":gates or [],
    }

class GateEvaluatorTests(unittest.TestCase):
    def test_automatic_gate_passes_from_passed_node(self):
        result=MOD.evaluate(
            policy(),{"gates":["G00"]},dag(),report(),through_phase="preflight"
        )
        self.assertEqual(result["status"],"passed")
        self.assertEqual(result["gates"][0]["status"],"pass")

    def test_future_runtime_gate_is_not_due_during_integrate(self):
        result=MOD.evaluate(
            policy("G26","runtime","runtime","runtime"),
            {"gates":["G26"]},
            dag("G26","runtime"),
            report(),
            through_phase="integrate",
        )
        self.assertEqual(result["status"],"passed")
        self.assertEqual(result["gates"][0]["status"],"not-applicable")

    def test_runtime_gate_without_authoritative_evidence_needs_review(self):
        result=MOD.evaluate(
            policy("G26","runtime","runtime","runtime"),
            {"gates":["G26"]},
            dag("G26","runtime"),
            report(),
            through_phase="release",
        )
        self.assertEqual(result["status"],"needs-review")
        self.assertEqual(result["gates"][0]["status"],"warning")

    def test_explicit_runtime_gate_pass_is_authoritative(self):
        explicit=[{
            "gate":"G26",
            "status":"pass",
            "severity":"BLOCKER",
            "evidence":["runtime fixture passed"],
            "issues":[],
        }]
        result=MOD.evaluate(
            policy("G26","runtime","runtime","runtime"),
            {"gates":["G26"]},
            dag("G26","runtime"),
            report(gates=explicit),
            through_phase="release",
        )
        self.assertEqual(result["status"],"passed")
        self.assertEqual(result["gates"][0]["status"],"pass")

    def test_failed_node_fails_gate(self):
        result=MOD.evaluate(
            policy("G02","adapter-evidence","validate","validate"),
            {"gates":["G02"]},
            dag("G02","validate"),
            report(status="failed"),
            through_phase="validate",
        )
        self.assertEqual(result["status"],"failed")
        self.assertEqual(result["gates"][0]["status"],"fail")

if __name__=="__main__":
    unittest.main()
