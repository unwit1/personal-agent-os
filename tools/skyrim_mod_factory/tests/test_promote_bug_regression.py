import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("promote_bug_regression",ROOT/"promote_bug_regression.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

def bug():
    return {
        "schema_version":"skyrim-bug-regression-v1",
        "bug_id":"BUG-1",
        "project_id":"fixture",
        "build_id":"build-1",
        "status":"validated",
        "symptom":"stale generated output",
        "expected":"fresh generated output",
        "environment":{},
        "reproduction":[{"step":"change source input and rebuild"}],
        "evidence":["fixture"],
        "first_causal_error":"cached output reused",
        "root_cause":"generator cache was stale",
        "layer":"generated-output",
        "fixed_by":["invalidate downstream cache"],
        "validation":["rerun passed"],
        "regression":{"analyzer_rule_id":"SKYRIM-GENERATED-OUTPUT-STALE"},
    }

class PromoteBugRegressionTests(unittest.TestCase):
    def test_promote_returns_schema_valid_candidate(self):
        packet=MOD.promote(bug())
        self.assertEqual(packet["schema_version"],"skyrim-regression-candidate-v1")
        self.assertEqual(packet["bug_id"],"BUG-1")
        self.assertEqual(
            MOD.schema_errors(packet,"skyrim-regression-candidate-v1.schema.json"),
            [],
        )

    def test_promote_rejects_missing_reproduction(self):
        value=bug()
        value.pop("reproduction")
        with self.assertRaises(ValueError):
            MOD.promote(value)

if __name__=="__main__":
    unittest.main()
