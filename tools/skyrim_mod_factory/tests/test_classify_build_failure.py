import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("classify",ROOT/"classify_build_failure.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

RULE_ID="SKYRIM-GENERATED-OUTPUT-STALE"
RULE_PACK={"rules":[{
    "schema_version":"skyrim-analyzer-rule-v1",
    "rule_id":RULE_ID,
    "title":"Generated output is stale",
    "scope":["generated-output"],
    "severity":"ERROR",
    "detection":{"kind":"generated-output"},
    "fix_policy":{"mode":"automatic"},
    "evidence":[{"source":"test","type":"repro-test"}],
}]}

def report(steps):
    return {
        "schema_version":"skyrim-mod-build-report-v1",
        "project_id":"fixture",
        "build_id":"build-1",
        "started_at":"2026-09-24T00:00:00+00:00",
        "status":"failed",
        "runtime_context":{"game_runtime":"1.7.104"},
        "steps":steps,
        "gates":[],
    }

class ClassifyBuildFailureTests(unittest.TestCase):
    def test_selects_first_failed_step_and_preserves_rule(self):
        doc=report([
            {"id":"preflight","status":"passed"},
            {
                "id":"generate.records",
                "adapter_id":"fixture",
                "status":"failed",
                "exit_code":0,
                "issues":["stale output"],
                "issue_codes":["STALE_OUTPUT"],
                "analyzer_rule_ids":[RULE_ID],
                "outputs_before":[
                    {"path":"out.bin","exists":True,"kind":"file","sha256":"a"}
                ],
                "outputs_after":[
                    {"path":"out.bin","exists":True,"kind":"file","sha256":"b"}
                ],
                "stdout_path":"stdout.log",
                "stderr_path":"stderr.log",
            },
            {"id":"validate.records","status":"failed","issues":["cascade"]},
        ])
        bug=MOD.classify(doc,RULE_PACK)
        self.assertEqual(bug["failing_task"],"generate.records")
        self.assertEqual(bug["adapter"],"fixture")
        self.assertEqual(bug["regression"]["analyzer_rule_id"],RULE_ID)
        self.assertEqual(bug["layer"],"generated-output")
        self.assertIn("out.bin",bug["changed_files"])
        self.assertIn(RULE_ID,bug["evidence"])

    def test_rule_match_does_not_claim_root_cause(self):
        bug=MOD.classify(report([{
            "id":"generate.records",
            "status":"failed",
            "issues":["detected stale output"],
            "analyzer_rule_ids":[RULE_ID],
        }]),RULE_PACK)
        self.assertEqual(bug["status"],"reported")
        self.assertNotIn("root_cause",bug)

    def test_unknown_failure_remains_unknown_layer(self):
        bug=MOD.classify(report([{
            "id":"custom/task with spaces",
            "status":"failed",
            "issues":["something failed"],
            "issue_codes":["TOOL_EXIT_CODE"],
        }]),RULE_PACK)
        self.assertEqual(bug["layer"],"unknown")
        self.assertNotIn("/",bug["bug_id"])
        self.assertNotIn(" ",bug["bug_id"])

    def test_no_failed_step_is_rejected(self):
        with self.assertRaises(ValueError):
            MOD.classify(report([{"id":"ok","status":"passed"}]),RULE_PACK)

if __name__=="__main__":
    unittest.main()
