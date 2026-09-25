import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("repair",ROOT/"plan_repair.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)


def rule(rule_id, mode, scope=None, post=None):
    return {
      "schema_version":"skyrim-analyzer-rule-v1",
      "rule_id":rule_id,
      "title":rule_id,
      "scope":scope or ["generated-output"],
      "severity":"ERROR",
      "detection":{"kind":"generated-output","algorithm":"detect it"},
      "fix_policy":{"mode":mode,"algorithm":"repair it","postconditions":post or ["fixed"]},
      "evidence":[{"source":"test","type":"repro-test"}]
    }


def bug(rule_id=None, **extra):
    b={
      "schema_version":"skyrim-bug-regression-v1",
      "bug_id":"BUG-1",
      "project_id":"demo",
      "status":"reproduced",
      "symptom":"broken",
      "environment":{},
      "evidence":[],
      "layer":"generated-output",
      "regression":{}
    }
    if rule_id:
        b["regression"]["analyzer_rule_id"]=rule_id
    b.update(extra)
    return b


class RepairPlanTests(unittest.TestCase):
    def test_allowlisted_automatic_rule_can_auto_repair(self):
        rid="SKYRIM-GENERATED-OUTPUT-STALE"
        p=MOD.plan(bug(rid),{"rules":[rule(rid,"automatic")]})
        self.assertEqual(p["policy"]["mode"],"automatic")
        self.assertTrue(p["policy"]["postconditions_provable"])
        self.assertEqual(p["repair"]["selected_hypothesis"],"h1")
        self.assertTrue(p["rollback"]["checkpoint_required"])
        self.assertEqual(
            p["repair"]["actions"][0]["handler_id"],
            "generated-output.invalidate-and-regenerate",
        )

    def test_non_allowlisted_automatic_rule_is_downgraded(self):
        rid="SKYRIM-TEST-AUTOMATIC"
        p=MOD.plan(bug(rid),{"rules":[rule(rid,"automatic")]})
        self.assertEqual(p["policy"]["mode"],"proposal")
        self.assertIn("registered executable",p["policy"]["reason"])

    def test_automatic_rule_without_handler_is_proposal_only(self):
        rid="SKYRIM-VALIDATOR-COVERAGE-GAP"
        p=MOD.plan(bug(rid),{"rules":[rule(rid,"automatic",scope=["validation"])]})
        self.assertEqual(p["policy"]["mode"],"proposal")
        self.assertIn("registered executable",p["policy"]["reason"])
        self.assertNotIn("handler_id",p["repair"]["actions"][0])

    def test_proposal_rule_stays_proposal(self):
        rid="SKYRIM-PLUGIN-UNRESOLVED-FORMLINK"
        p=MOD.plan(bug(rid),{"rules":[rule(rid,"proposal",scope=["plugin"])]})
        self.assertEqual(p["policy"]["mode"],"proposal")
        self.assertIn("mutagen",p["validation"]["independent_validators"])
        self.assertIn("xdump",p["validation"]["independent_validators"])

    def test_manual_rule_is_never_automatic(self):
        rid="SKYRIM-NAVM-DELETED"
        b=bug(rid,layer="navmesh")
        p=MOD.plan(b,{"rules":[rule(rid,"manual",scope=["navmesh"])]})
        self.assertEqual(p["policy"]["mode"],"manual")
        self.assertTrue(p["policy"]["requires_user_decision"])

    def test_unknown_failure_needs_hypothesis_not_guess(self):
        p=MOD.plan(bug(),{"rules":[]})
        self.assertEqual(p["policy"]["mode"],"proposal")
        self.assertEqual(len(p["hypotheses"]),1)
        self.assertIn("Reproduce",p["hypotheses"][0]["test"]["action"])

    def test_unknown_rule_id_downgrades_to_proposal(self):
        p=MOD.plan(bug("SKYRIM-NOT-IN-PACK"),{"rules":[]})
        self.assertEqual(p["policy"]["mode"],"proposal")
        self.assertFalse(p["policy"]["postconditions_provable"])


if __name__=="__main__":
    unittest.main()
